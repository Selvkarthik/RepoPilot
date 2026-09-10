from langchain_core.documents import Document

def create_documents(files, repository):
    documents = []

    for file in files:
        document = Document(
            page_content=file['content'],
            metadata={
                "repository" : repository,
                "file_path" : file['path'],
                "language" : file['language']
            }
        )

        documents.append(document)

    return documents