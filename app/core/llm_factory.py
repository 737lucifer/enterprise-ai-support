
import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "ollama":
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            temperature=0,
            base_url=os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434"
            ),
        )

    elif provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0,
        )

    elif provider == "openai":
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            temperature=0,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )
