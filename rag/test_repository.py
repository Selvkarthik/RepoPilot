from rag.retriever import CodeRetriever


retriever = CodeRetriever(
    repository="selvkarthik/DocQuery",
    k=3
)

documents = retriever.invoke(
    "How does the application connect to the database?"
)

for document in documents:

    print("\n====================")
    print("File:", document.metadata["file_path"])
    print("Chunk:", document.metadata["chunk_index"])
    print("Distance:", document.metadata["distance"])
    print("--------------------")
    print(document.page_content[:500])