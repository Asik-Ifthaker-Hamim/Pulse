from langchain_openai import ChatOpenAI
from .config import settings

llm = None
try:
    llm = ChatOpenAI(
        model="gpt-4o",
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0
    )
    print("ChatOpenAI client initialized successfully.")
except Exception as e:
    print(f"FATAL: Failed to initialize ChatOpenAI client: {e}")