from tools.github_tools import index_github_repository

result = index_github_repository.invoke({
    "owner" : "selvkarthik",
    "repo" : "DocQuery"
})

print(result)