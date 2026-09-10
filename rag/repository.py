from rag.database import get_connection

class CodeRepository:

    def similarity_search(
            self,
            repository : str,
            query_vector : list[float],
            k : int = 5
    ):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT file_path, chunk_index, content, 
                    language, embedding <=> %s :: vector AS distance
                    FROM code_chunks
                    WHERE repository = %s
                    ORDER BY embedding <=> %s :: vector
                    LIMIT %s
                    """,
                    (
                        query_vector,
                        repository,
                        query_vector,
                        k
                    )
                )
                return cursor.fetchall()