from tools.github_tools import search_repository_code


result = search_repository_code.invoke({
    "query": "How does the application connect to the database?",
    "repository": "selvkarthik/DocQuery"
})

print(result)