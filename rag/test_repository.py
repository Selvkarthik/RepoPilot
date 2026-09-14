from rag.repository import CodeRepository

db = CodeRepository()

print(
    db.get_file_hashes(
        "selvkarthik/DocQuery"
    )
)