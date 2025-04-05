from openai import OpenAI
import os
import datetime
import json
import os
from dotenv import load_dotenv


load_dotenv(override=True)

base_model = os.getenv("BASE_MODEL")
base_api = os.getenv("BASE_API")
base_url = os.getenv("BASE_URL")
client = OpenAI(
    api_key=base_api,
    base_url=base_url
)


def generate_prompt(task: str, previous_actions: list) -> str:
    """
    Generates a dynamic prompt based on the task and previous actions.
    """
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

    action_definitions = """
        You are an AI with tools and actions.
        HE FORMAT FOR ACTIONS IS {ACTION} [ARGUMENTS]
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
            - Abstract – summary of the research objectives, methods, findings, and conclusions.
            - Introduction – Provide background, state the research problem, and outline objectives.
            - Literature Review – Summarize relevant studies and identify gaps.
            - Methodology – Describe the research design, sample size, and methods.
            - Results – Present findings (include tables/graphs if necessary).
            - Discussion – Interpret results, compare with existing studies, and discuss limitations.
            - Conclusion – Summarize findings and suggest future research.
            - References – List citations used.
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

        """
    system_instruction = f"""
      You are an AI assistant. Follow the rules:
      {action_definitions}
      {instructions}
    """
    user_task = f"""
      Task: {task}
      Previous Actions: {json.dumps(previous_actions or [])}
      Today's Date: {datetime.datetime.now().isoformat()}

      Remember: Do not use CONCLUDE until all necessary actions have been performed.
    """
    return system_instruction, user_task


task = "Plot a graph of the weather in NYC, Chicago, and Houston for the next 3 days."
previous_actions = []
system, user = generate_prompt(task, previous_actions)
messages = [{"role": "system", "content": system}, 
            {"role": "user", "content": user}]
# print(f"stream messages: {messages}")
response = client.chat.completions.create(
    model=base_model,
    messages=messages,
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta)
