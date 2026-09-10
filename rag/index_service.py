from rag.indexer import get_repository_files
from rag.documents import create_documents
from rag.splitter import split_documents
from rag.vector_store import store_chunks

def index_repository(owner : str, repo : str):
    repository = f"{owner}/{repo}"
    print(f"Indexing repository: {repository}")

    files = get_repository_files(owner, repo)
    print(f"Found {len(files)} source files")

    documents = create_documents(files, repository)
    print(f"Created {len(documents)} Documents")

    chunks = split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    store_chunks(chunks)

    return {
        "repository" : repository,
        "files" : len(files),
        "chunks" : len(chunks)
    }