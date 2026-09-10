from rag.retriever import CodeRepository


results = CodeRepository(
    repository="selvkarthik/DocQuery",
    k=3
)

for result in results:

    file_path, chunk_index, content, distance = result

    print("\n====================")
    print("File:", file_path)
    print("Chunk:", chunk_index)
    print("Distance:", distance)
    print("--------------------")
    print(content[:500])