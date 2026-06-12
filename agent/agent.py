import os
from dotenv import load_dotenv
from anthropic import Anthropic
from anthropic.types import TextBlock
from retrieval.search import semantic_search



load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)


def ask(question):
    chunks = semantic_search(question)
    
    if not chunks:
        return "No relevant code found for that question."

    context = "\n\n".join(
        f"File: {c['file_path']} (lines {c['start_line']}-{c['end_line']})\n{c['chunk_text']}"
        for c in chunks
    )
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system="You are a codebase assistant. Answer questions using only the provided code context.",
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}]
    )

    block = response.content[0]
    return block.text if isinstance(block, TextBlock) else ""