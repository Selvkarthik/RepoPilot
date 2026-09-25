EVAL_CASES = [
    {
        "repository": "Selvkarthik/DocQuery",
        "question": "How does document ingestion process uploaded documents?",
        "expected_files": [
            "app/services/ingestion.py",
            "rag/ingest.py",
        ],
    },
    {
        "repository": "Selvkarthik/DocQuery",
        "question": "How does the application retrieve relevant document chunks for a query?",
        "expected_files": [
            "app/services/retriever.py",
            "rag/retriever.py",
        ],
    },
    {
        "repository": "Selvkarthik/DocQuery",
        "question": "How does the application assemble the retrieval augmented generation pipeline?",
        "expected_files": [
            "app/services/rag_service.py",
            "rag/rag_pipeline.py",
        ],
    },
    {
        "repository": "Selvkarthik/DocQuery",
        "question": "How are text embeddings generated for documents?",
        "expected_files": [
            "app/services/embedding.py",
        ],
    },
    {
        "repository": "Selvkarthik/DocQuery",
        "question": "How does the application generate the final LLM response?",
        "expected_files": [
            "app/services/generator.py",
            "rag/generator.py",
        ],
    },
    {
        "repository": "Selvkarthik/DocQuery",
        "question": "How does the application execute its agent workflow?",
        "expected_files": [
            "app/services/agent_service.py",
            "rag/agent.py",
        ],
    },
    {
        "repository": "Selvkarthik/DocQuery",
        "question": "How is conversation memory stored using Redis?",
        "expected_files": [
            "memory/redis_memory.py",
        ],
    },
    {
        "repository": "Selvkarthik/DocQuery",
        "question": "How are the application's database models defined?",
        "expected_files": [
            "app/db/models.py",
            "rag/models.py",
        ],
    },
    {
        "repository": "Selvkarthik/DocQuery",
        "question": "How does the search API handle a search request?",
        "expected_files": [
            "app/api/v1/endpoints/search.py",
        ],
    },
    {
        "repository": "Selvkarthik/DocQuery",
        "question": "How does the API handle document upload and document management?",
        "expected_files": [
            "app/api/v1/endpoints/documents.py",
        ],
    },
]