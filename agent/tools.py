search_codebase_tool = {
    "name": "search_codebase",
    "description": (
        "Search the codebase for relevant code snippets. "
        "Call this if the current context doesn't fully answer the question. "
        "You can call it multiple times with different queries to gather enough context before answering."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant code"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default 5)",
                "default": 5
            }
        },
        "required": ["query"]
    }
}
