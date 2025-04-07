import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv


load_dotenv(override=True)

base_model = os.getenv("MODEL")
base_api = os.getenv("BASE_API")
base_url = os.getenv("BASE_URL")

    

llm = ChatGoogleGenerativeAI(model=base_model, google_api_key=base_api)
    
    
messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = llm.invoke(messages)
ai_msg

print(ai_msg.content)