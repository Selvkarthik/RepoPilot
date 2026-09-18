from workers.repository_worker import sync_repository

result = sync_repository(
    owner='selvkarthik',
    repo='DocQuery'
)

print(result)