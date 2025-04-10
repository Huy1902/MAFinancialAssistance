
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

llm = OllamaLLM(model="qwen2.5:0.5b")


template = """Question: {question}

Answer: Let's think step by step."""

prompt = ChatPromptTemplate.from_template(template)

chain = prompt | llm

chain.invoke({"question": "What is LangChain?"})