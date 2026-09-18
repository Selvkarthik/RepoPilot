import hashlib

from rag.embeddings import embeddings
from rag.database import get_connection

def store_chunks(chunks):
    texts = [chunk.page_content for chunk in chunks]

    vectors = embeddings.embed_documents(texts)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            for chunk, vector in zip(chunks, vectors):

                content_hash = hashlib.sha256(
                    chunk.page_content.encode('utf-8')
                ).hexdigest()

                cursor.execute(
                    """
                    INSERT INTO code_chunks
                    (repository, file_path, language, chunk_index, content, content_hash, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (repository, file_path, chunk_index)
                    DO UPDATE SET
                    language = EXCLUDED.language,
                    content = EXCLUDED.content
                    content_hash = EXCLUDED.content_hash
                    embedding = EXCLUDED.embedding
                """,
                (
                    chunk.metadata['repository'],
                    chunk.metadata['file_path'],
                    chunk.metadata['language'],
                    chunk.metadata['chunk_index'],
                    chunk.page_content,
                    content_hash,
                    vector
                )
                )
        connection.commit()