import datetime
import json
import re
import time
from flask_socketio import emit
from openai import OpenAI
import os
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from util.code_execute import execute_code
from util.scrap import download_file, scrape

class SearchAgent:
    def __init__(self):
        load_dotenv(override=True)
        self.tasks = {} # Store tasks and their context
        self.history = [] # Store the history of actions taken
        self.stop_processing = False
        self.init_client_llm()
        self.max_retries = int(os.environ.get('MAX_RETRIES'))
        self.retry_delay = int(os.environ.get('RETRY_DELAY'))
        self.max_search_results = int(os.environ.get('MAX_SEARCH_RESULTS'))
        self.model = os.environ.get('MODEL')
        self.task_stopped = False
        self.global_history = [] # Save content from previous tasks from user
        self.clear_global_history = False
        self.max_step = int(os.environ.get('MAX_STEP'))
        self.min_choose_results = int(os.environ.get('MIN_CHOOSE_RESULTS'))
        self.max_choose_results = int(os.environ.get('MAX_CHOOSE_RESULTS'))

    def init_client_llm(self):
        """
        Initialize the client LLM with the given parameters.
        """
        client_params = {
            'base_url': os.environ.get('BASE_URL'),
            'api_key': os.environ.get('BASE_API')
        }
        try:
            self.client = OpenAI(**client_params)
        except Exception as e:
            print(f"Error initializing client LLM: {e}")
            raise e

    def generate_prompt(self, task: str, previous_actions: list) -> str:
        """
            Generates a dynamic prompt based on the task and previous actions.
        """
        # Chain of thought
        complexity = "complex" if len(previous_actions) > 5 else "simple"
        if complexity == "complex":
            instructions = """
            For complex tasks, ensure intermediate results are validated before proceeding.
            Use structured approaches and avoid assumptions.
            """
        else:
            instructions = """
            For simple tasks, provide precise and concise responses to quickly achieve the goal.
            """

        # Action definitions
        # Define the actions and their formats
        action_definitions = """
        You are an AI with tools and actions.
        THE FORMAT FOR ACTIONS IS {ACTION} [ARGUMENTS]
        The following are the actions that fit the above format:
        1. {SEARCH} [QUERY] - Conduct a web search with a clear, focused query. Example: {SEARCH} weather in New York.
        You must Scrape between 2-6 results depending on task complexity.
        2. {SCRAPE} [URL] - 
        Only use {SCRAPE} if one or more of the following conditions are met: 
            a) You have the URL from search results
            b) You have the URL from a website you scraped
            c) The user included the URL in the task description. 
            In each case or cases you can only use the {SCRAPE} action on the URL provided.
        3. {DOWNLOAD} [URL] - Download a file from a URL. Example: {DOWNLOAD} https://example.com/file.pdf.
        4. {EXECUTE_PYTHON} [CODE] -  Run Python code. Example: {EXECUTE_PYTHON} print(42).
        5. {EXECUTE_BASH} [CODE] - Run a Bash command. Example: {EXECUTE_BASH} ls -l.
        6. {CONCLUDE} [CONCLUSION] - Provide a detailed summary once all tasks are completed. This should be used **only after all 
        actions have been executed** and the task is ready to conclude, 
        For research or scientific tasks, structure your conclusion as follows:
            {CONCLUDE}
            - Abstract - summary of the research objectives, methods, findings, and conclusions.
            - Introduction - Provide background, state the research problem, and outline objectives.
            - Literature Review - Summarize relevant studies and identify gaps.
            - Methodology - Describe the research design, sample size, and methods.
            - Results - Present findings (include tables/graphs if necessary).
            - Discussion - Interpret results, compare with existing studies, and discuss limitations.
            - Conclusion - Summarize findings and suggest future research.
            - References - List citations used.
        For all other cases just provide the summary like this: {CONCLUDE}: followed by the summary of the task.

        - NEVER DO MORE THEN ONE ACTION IN A RESPONSE 
        - NEVER DESCRIBE WHAT YOU ARE DOING.
        - DO NOT BE CHATTY! JUST DO.
        - DO NOT GIVE INTROS OR OUTROS, JUST ONE SINGLE ACTION.
        - YOU ALWAYS PERFORM ONE SINGLE ACTION, NOT MULTIPLE -  For example do not do the following:
        {SEARCH} "Weather in nyc today"
        
        {SCRAPE} https://weather.com/nyc
        
        {SCRAPE} https://weather.com/new_york
        
        {CONCLUDE} The weather in NYC is 70 degrees.
        - NEVER REPEAT A PREVIOUS ACTION - For example do not do the following:
        {SCRAPE} https://weather.com/nyc
        User: {WEBSITE CONTENTS OF SCRAPED WEBSITE}
        {SCRAPE} https://weather.com/nyc
        
        Remember: Do not use CONCLUDE until all necessary actions have been performed.
        """

        system_instruction = f"""
        You are an AI assistant. Follow the rules:
        {action_definitions}
        {instructions}
        """

        # dumps the previous actions to a string
        # and adds it to the task
        # to provide context for the model
        user_task = f"""
        Task: {task}
        Previous Actions: {json.dumps(previous_actions or [])}
        Today's Date: {datetime.datetime.now().isoformat()}
        """
        return system_instruction, user_task

    def stream_response(self, task: str, previous_actions: list):
        """
        Streams the response from the LLM.
        """
        system_instruction, user_task = self.generate_prompt(
            task, previous_actions)

        # Set up the stream
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_task}
                ],
                stream=True
            )

            full_response = ""
            response_iterator = response.__iter__()

            while True:
                if self.stop_processing:
                    print("Stopping processing...")
                    response.close()
                    self.task_stopped = True
                    break

                try:
                    chunk = next(response_iterator)
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        print(content, end='', flush=True)
                        yield content
                except StopIteration:
                    break

            if task in self.tasks:
                self.tasks[task]['streamed_response'] = full_response
        except Exception as e:
            print(f"Error streaming response: {e}")
            raise e

    def conclude(self, task, actions):
        """
        Provides a conclusion for the task based on the actions taken.
        """
        messages = [
            {"role": "system", "content": "You are an AI agent that provides conclusions based on task completion."},
            {"role": "user",
             "content": f"Task: {task}\n\nActions taken: {json.dumps(actions)}\n\nProvide a conclusion for the task."}
        ]
        for idx in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=False
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                if idx == self.max_retries - 1:
                    raise e
                time.sleep(self.retry_delay * (idx + 1))
                
    def is_complete(self, task, actions):
        """
        Evaluates if the task has been completed based on the actions taken.
        """
        # If there are more than 2 actions, we can evaluate
        if len(actions) > 2:
            messages = [
                {"role": "system",
                    "content": "You are an AI agent that evaluates task completion."},
                {"role": "user",
                    "content": f"Task: {task}\n\nActions taken: {json.dumps(actions)}\n\nHas the task been completed? Respond with 'YES' if completed, 'NO' if not."}
            ]
            # print(f"evaluate messages: {messages}")
            for attempt in range(self.max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages
                    )
                    return "YES" in response.choices[0].message.content.upper()
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise e
                    time.sleep(self.retry_delay * (attempt + 1))
        else:
            return
        
    def search(self, query):
        results = DDGS().text(query, max_results=self.max_search_results)
        return results
    
    def extract_actions(self, response: str) -> list:
        """
        Extracts actions from the response string.
        Args:
            response (str): The response string from the LLM.
        Returns:
            list: A list of extracted actions.
        """
        actions = []
        pattern = re.compile(
            r'\{([A-Z_]+)\}(.+?)(?=\{[A-Z_]+\}|$)', re.DOTALL)
        matches = pattern.findall(response)
        for type, content in matches:
            action = f"{{{type}}}{content.strip()}"
            if action not in actions:
                actions.append(action)
        return actions
        
        
    def execute(self, task):
        if task not in self.tasks:
            self.tasks[task] = {'previous_actions': [],
                                'conclusions': [], 'performed_actions': set()}

        task_context = self.tasks[task]
        if self.clear_global_history:
            self.global_history = []
            self.clear_global_history = False
        previous_actions = task_context['previous_actions'] + \
            self.global_history
        self.global_history.append(task_context['previous_actions'])
        conclusions = task_context['conclusions']
        performed_actions = task_context['performed_actions']
        step = 0
            
        print(f"Executing task: {task}")
        
        while step < self.max_step and not self.task_stopped:
            step += 1
            print(f"Step {step} of {self.max_step}")
            # Stream the response from the LLM
            full_response = ""
            for response in self.stream_response(task, previous_actions):
                full_response += response

            # Extract actions from the response
            actions = self.extract_actions(full_response)
            print(f"Extracted actions: {actions}")

            # Check if the task is complete
            # if self.is_complete(task, actions):
            #     print("Task is complete.")
            #     break

            # Execute the actions
            for action in actions:
                
                performed_actions.add(action)
                
                if action.startswith("{CONCLUDE}"):
                    conclusion = action[11:].strip()
                    print(f"Conclusion: {conclusion}")
                    emit('receive_message', {
                         'status': 'info', 'message': "Here's my conclusion:"})
                    emit('receive_message', {
                         'status': 'info', 'message': conclusion})
                    conclusions.append(conclusion)
                    step = self.max_step
                    break
                
                elif action.startswith("{SEARCH}"):
                    query = action[8:].strip().split('\n')[0].replace('"', '')
                    print(f"Searching for: {query}")
                    emit('receive_message', {
                         'status': 'info', 'message': f"Searching web for: {query}"})
                    search_results = self.search(query)
                    print(f"Search results: {search_results}")
                    emit('receive_message', {
                         'status': 'info', 'message': f"Search results: {search_results}"})
                    # Save the search results to the task context
                    if json.dumps(search_results) not in json.dumps(previous_actions):
                        previous_actions.append(f"Searched: {search_results}")
                        previous_actions.append(
                            f"""Search results: {json.dumps(search_results)}
                            Select between {self.min_choose_results} to {self.max_choose_results}\
                                results to scrape.
                            """)
                    else:
                        print("Search results already in previous actions.")
                
                elif action.startswith("{SCRAPE}"):
                    # Extract the URL from the action
                    match = re.search(r'{SCRAPE}\s*(https?://\S+)', action)
                    try:
                        url = match.group(1)
                        if url.endswith(".pdf"):
                            # TODO: handle pdf files
                            pass
                        
                        print(f"Scraping URL: {url}")
                        emit('receive_message', {
                             'status': 'info', 'message': f"Scraping website: {url}"})
                        # Scrape the URL and get the content
                        result = scrape(url)
                        if json.dumps(result) not in json.dumps(previous_actions):
                            previous_actions.append(f"Scraped: {result}")
                            previous_actions.append(
                                f"Scraped content: {json.dumps(result)}\
                                    is this information useful?")
                        else:
                            print("Scraped content already in previous actions.")
                    except Exception as e:
                        print(f"Error scraping URL: {e}")
                        emit('receive_message', {
                             'status': 'error', 'message': f"Error scraping URL: {e}"})
                        pass
                    
                elif action.startswith("{DOWNLOAD}"):
                    try:
                        url = re.search(r'{DOWNLOAD}\s*(https?://\S+)', action).group(1)
                        print(f"Downloading from URL: {url}")
                        download_result = download_file(url)
                        print(f"Download result: {download_result}")
                        emit('receive_message',
                             {'status': 'info', 'message': f"Downloaded: {url} - {download_result}"})
                        previous_actions.append(f"Downloaded: {url} - {download_result}")
                    except Exception as e:
                        print(f"Error downloading file: {e}")
                        emit('receive_message', {
                             'status': 'error', 'message': f"Error downloading file: {e}"})
                        
                elif action.startswith("{EXECUTE_PYTHON}"):
                    code = action[16:].strip().removeprefix("```python").removesuffix("```").strip()
                    print(f"Executing Python code: {code}")
                    emit('receive_message',
                        {'status': 'info', 'message': f"Executing Python code:\n```python\n{code}\n```"})
                    try:
                        result = execute_code(code, language='python')
                        print(f"Executed Python code: {code}")
                        emit('receive_message', {
                         'status': 'info', 'message': f"Result:\n```markdown\n{result}\n```"})
                        previous_actions.append(
                            f"Executed Python code: {code} - Result: {result}")
                    except Exception as e:
                        print(f"Error executing Python code: {e}")
                    
                elif action.startswith("{EXECUTE_BASH}"):
                    code = action[14:].strip().removeprefix("```bash").removesuffix("```").strip()
                    print(f"Executing Bash command: {code}")
                    emit('receive_message', {
                         'status': 'info', 'message': f"Executing Bash code:\n{code}"})
                    try:
                        result = execute_code(code, language='bash')
                        print(f"Executed Bash command: {code}")
                        previous_actions.append(
                            f"Executed Bash command: {code} - Result: {result}")
                        emit('receive_message', {
                         'status': 'info', 'message': f"Result: {result}"})
                    except Exception as e:
                        print(f"Error executing Bash command: {e}")
                        
            self.tasks[task] = {
                'previous_actions': previous_actions,
                'conclusions': conclusions,
                'performed_actions': performed_actions
            }
            self.global_history.extend(previous_actions)
            
            if self.is_complete(task, previous_actions):
                print("Task is complete.")
                emit('receive_message', {
                     'status': 'info', 'message': "Task completed successfully!"})
                break
        
        # Check if the task is complete and provide a conclusion
        if not conclusions:
            conclusion = self.conclude(task, previous_actions)
            if conclusion:
                conclusions.append(conclusion)
                previous_actions.append(f"Added conclusion: {conclusion}")
        
        # Print the conclusions
        if conclusions:
            print(f"Conclusions: {conclusions}")
            for conclusion in conclusions:
                print(conclusion)
                emit('receive_message', {
                     'status': 'info', 'message': conclusion})
                
        return len(conclusions) > 0       

if __name__ == "__main__":
    agent = SearchAgent()
    current_task = ""
    while True:
        if current_task:
            print(f"\nCurrent task: {current_task}\nEnter your task (or 'quit' to exit):")
        else:
            print("\nEnter your task (or 'quit' to exit):")
        task_input = input("INPUT: ").strip()

        if task_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not task_input:
            print("Please enter a valid task.")
            continue

        task = task_input
        current_task = task_input

        try:
            print("\n" + "=" * 50)
            agent.execute(task)
            print("=" * 50)
        except KeyboardInterrupt:
            print("\nTask interrupted by user.")
            continue
        except Exception as e:
            print(f"\nError executing task: {e}")
            continue