from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap = 200
)

def split_documents(documents):
    chunks = splitter.split_documents(documents)

    counters = {}

    for chunk in chunks:
        file_path = chunk.metadata['file_path']
        index = counters.get(file_path, 0)
        chunk.metadata['chunk_index'] = index
        counters[file_path] = index + 1

    return chunks