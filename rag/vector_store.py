from rag.embeddings import embeddings
from rag.database import get_connection

def store_chunks(chunks):
    texts = [chunk.page_content for chunk in chunks]

    vectors = embeddings.embed_documents(texts)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for chunk, vector in zip(chunks, vectors):
                cursor.execute(
                    """
                    INSERT INTO code_chunks
                    (repository, file_path, language, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    chunk.metadata['repository'],
                    chunk.metadata['file_path'],
                    chunk.metadata['language'],
                    chunk.metadata['chunk_index'],
                    chunk.page_content,
                    vector
                )
                )
        connection.commit()