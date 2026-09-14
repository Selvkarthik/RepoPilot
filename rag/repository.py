from rag.database import get_connection


class CodeRepository:

    def similarity_search(
        self,
        repository: str,
        query_vector: list[float],
        k: int = 5
    ):
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        file_path,
                        chunk_index,
                        content,
                        language,
                        embedding <=> %s::vector AS distance
                    FROM code_chunks
                    WHERE repository = %s
                    ORDER BY embedding <=> %s::vector
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

    def get_file_hashes(self, repository: str):

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT file_path, content_hash
                    FROM code_files
                    WHERE repository = %s
                    """,
                    (repository,)
                )

                return {
                    file_path: content_hash
                    for file_path, content_hash in cursor.fetchall()
                }

    def delete_file(self, repository: str, file_path: str):

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    DELETE FROM code_chunks
                    WHERE repository = %s
                    AND file_path = %s
                    """,
                    (
                        repository,
                        file_path
                    )
                )
                deleted_chunks = cursor.rowcount

                cursor.execute(
                    """
                    DELETE FROM code_files
                    WHERE repository = %s
                    AND file_path = %s
                    """,
                    (
                        repository,
                        file_path
                    )
                )

            connection.commit()

        return deleted_chunks

    def save_file(
        self,
        repository: str,
        file_path: str,
        language: str,
        content_hash: str
    ):

        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO code_files
                    (
                        repository,
                        file_path,
                        language,
                        content_hash
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (repository, file_path)
                    DO UPDATE SET
                        language = EXCLUDED.language,
                        content_hash = EXCLUDED.content_hash,
                        last_indexed_at = CURRENT_TIMESTAMP
                    """,
                    (
                        repository,
                        file_path,
                        language,
                        content_hash
                    )
                )

            connection.commit()
