import datetime
import json
import re
import time
from openai import OpenAI
import os
from dotenv import load_dotenv
from duckduckgo_search import DDGS


class SearchAgent:
    def __init__(self):
        load_dotenv(override=True)
        self.tasks = {}
        self.history = []
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
            return "NO"
        
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
                action_type = action.split(' ')[0][1:-1]
                if action_type == 'SEARCH':
                    query = action.split(' ')[1:]
                    search_results = self.search(' '.join(query))
                    task_context['previous_actions'].append(search_results)
                    performed_actions.add(action)
                    print(f"Performed search: {search_results}")
                elif action_type == 'SCRAPE':
                    url = action.split(' ')[1]
                    scraped_content = self.scrape(url)
                    task_context['previous_actions'].append(scraped_content)
                    performed_actions.add(action)
                    print(f"Scraped content: {scraped_content}")
                elif action_type == 'EXECUTE_PYTHON':
                    code = action.split(' ')[1:]
                    execution_result = self.execute_python(' '.join(code))
                    task_context['previous_actions'].append(execution_result)
                    performed_actions.add(action)
                    print(f"Executed Python code: {execution_result}")
                elif action_type == 'EXECUTE_BASH':
                    code = action.split(' ')[1:]
                    execution_result = self.execute_bash(' '.join(code))
                    task_context['previous_actions'].append(execution_result)
                    performed_actions.add(action)
                    print(f"Executed Bash command: {execution_result}")
                elif action_type == 'CONCLUDE':
                    conclusion = self.conclude(task, task_context['previous_actions'])
                    conclusions.append(conclusion)
                    task_context['previous_actions'].append(conclusion)
                    performed_actions.add(action)
                    print(f"Conclusion: {conclusion}")
                
            
