import os
import sys
import asyncio

# Windows compatibility fix for Psycopg async connections
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

load_dotenv()

TABLE_NAME = "support_knowledge"
VECTOR_SIZE = 768

def get_embeddings():
    return OllamaEmbeddings(
        model=os.getenv(
            "OLLAMA_EMBEDDING_MODEL",
            "nomic-embed-text"
        ),
        base_url=os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434"
        ),
    )


def get_engine():
    return PGEngine.from_connection_string(
        url=os.environ["DATABASE_URL"]
    )


def initialize_vector_store():
    engine = get_engine()

    try:
        engine.init_vectorstore_table(
            table_name=TABLE_NAME,
            vector_size=VECTOR_SIZE,
        )
        print("Vector store table created successfully.")

    except Exception as e:
        from sqlalchemy.exc import ProgrammingError

        if (
            isinstance(e, ProgrammingError)
            and getattr(e.orig, "sqlstate", None) == "42P07"
        ):
            print("Vector store table already exists. Reusing it.")
        else:
            raise

    return engine


def get_vector_store(engine):
    return PGVectorStore.create_sync(
        engine=engine,
        table_name=TABLE_NAME,
        embedding_service=get_embeddings(),
    )
