from uuid import uuid5, NAMESPACE_URL
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from app.rag.vector_store import (
    initialize_vector_store,
    get_vector_store,
)


documents = [
    Document(
        page_content=(
            "Incident INC001: Candidate synchronization API "
            "returned HTTP 500 during ATS to HRIS integration. "
            "The root cause was an invalid candidate payload. "
            "Resolution: validate required fields and inspect "
            "the upstream API response before retrying."
        ),
        metadata={"source": "INC001", "type": "incident"},
    ),
    Document(
        page_content=(
            "Incident INC002: Users could not log in to the "
            "recruitment portal due to expired SSO certificates. "
            "Resolution: verify identity provider certificate "
            "validity and coordinate certificate renewal."
        ),
        metadata={"source": "INC002", "type": "incident"},
    ),
    Document(
        page_content=(
            "Runbook RB003: Database connection failures. "
            "Verify database availability, connection pool "
            "utilization, network access, and application logs."
        ),
        metadata={"source": "RB003", "type": "runbook"},
    ),
]


def main():
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_documents(documents)

    engine = initialize_vector_store()
    store = get_vector_store(engine)

    # Use stable IDs so repeated ingestion does not
    # generate unlimited duplicate sample records.
    ids = [
    str(uuid5(
        NAMESPACE_URL,
        f"sample-{doc.metadata['source']}-{i}"
    ))
    for i, doc in enumerate(chunks)
]

    store.add_documents(chunks, ids=ids)

    print(f"Indexed {len(chunks)} document chunks.")

    query = "Candidate sync API is returning HTTP 500"

    results = store.similarity_search(query, k=2)

    print("\nRETRIEVED KNOWLEDGE:")
    for doc in results:
        print("Source:", doc.metadata.get("source"))
        print("Content:", doc.page_content)
        print("---")


if __name__ == "__main__":
    main()
