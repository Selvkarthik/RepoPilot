from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from rag.embeddings import embeddings
from rag.repository import CodeRepository

class CodeRetriever(BaseRetriever):
    repository : str
    k : int = Field(default=5)

    def _get_relevant_documents(self, query : str):
        query_vector = embeddings.embed_query(query)
        db = CodeRepository()

        results = db.similarity_search(
            repository=self.repository,
            query_vector=query_vector,
            k=self.k
        )

        documents = []

        for (file_path, chunk_index, content, language, distance) in results:
            documents.append(
                Document(
                    page_content = content,
                    metadata = {
                        "repository" : self.repository,
                        "file_path" : file_path,
                        "language" : language,
                        "chunk_index" : chunk_index,
                        "distance" : distance
                    }
                )
            )

        return documents