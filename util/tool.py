from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import tool
from langgraph.prebuilt.tool_node import ToolNode


def define_tool(db, llm):
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    # Query checking
    query_check_system = """You are a SQL expert with a strong attention to detail.
	Double check the PostgreSQL query for common mistakes, including:
	- Using NOT IN with NULL values
	- Using UNION when UNION ALL should have been used
	- Using BETWEEN for exclusive ranges
	- Data type mismatch in predicates
	- Properly quoting identifiers
	- Using the correct number of arguments for functions
	- Casting to the correct data type
	- Using the proper columns for joins

	If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

	Execute the correct query with the appropriate tool."""
    query_check_prompt = ChatPromptTemplate.from_messages(
        [("system", query_check_system), ("user", "{query}")])
    query_check = query_check_prompt | llm

    @tool
    def check_query_tool(query: str) -> str:
        """
        Use this tool to double check if your query is correct before executing it.
        """
        return query_check.invoke({"query": query}).content

    # Query result checking
    query_result_check_system = """You are grading the result of a SQL query from a DB. 
  - Check that the result is not empty.
  - If it is empty, instruct the system to re-try!"""
    query_result_check_prompt = ChatPromptTemplate.from_messages(
        [("system", query_result_check_system), ("user", "{query_result}")])
    query_result_check = query_result_check_prompt | llm

    @tool
    def check_result(query_result: str) -> str:
        """
        Use this tool to check the query result from the database to confirm it is not empty and is relevant.
        """
        return query_result_check.invoke({"query_result": query_result}).content

    tools.append(check_query_tool)
    tools.append(check_result)
    
    return tools
