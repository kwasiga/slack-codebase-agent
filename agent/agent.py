import os
from dotenv import load_dotenv
from anthropic import Anthropic
from anthropic.types import TextBlock
from retrieval.search import semantic_search
from agent.tools import search_codebase_tool

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = (
    "You are a codebase assistant. You have a search_codebase tool you can use to find relevant code. "
    "Call it with different queries as many times as needed to gather enough context before answering. "
    "Always ground your answer in the code you retrieve."
)


def ask(question) -> dict:
    messages = [{"role": "user", "content": question}]
    sources = []

    for _ in range(4):
        import json
        print("=== MESSAGES SENT TO API ===")
        for i, m in enumerate(messages):
            print(f"[{i}] role={m['role']} content={json.dumps(m['content'], default=str)[:300]}")
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[search_codebase_tool],
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if isinstance(block, TextBlock):
                    return {"answer": block.text, "sources": sources}
            return {"answer": "", "sources": sources}

        if response.stop_reason == "tool_use":
            assistant_content = []
            for b in response.content:
                if b.type == "text":
                    assistant_content.append({"type": "text", "text": b.text})
                elif b.type == "tool_use":
                    assistant_content.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for b in response.content:
                if b.type != "tool_use":
                    continue
                query = b.input["query"]
                top_k = b.input.get("top_k", 5)
                chunks = semantic_search(query, top_k)
                sources.extend(
                    {"file": c["file_path"], "lines": f"{c['start_line']}-{c['end_line']}"}
                    for c in chunks
                )
                tool_result = "\n\n".join(
                    f"File: {c['file_path']} (lines {c['start_line']}-{c['end_line']})\n{c['chunk_text']}"
                    for c in chunks
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": b.id,
                    "content": tool_result or "No results found."
                })
            messages.append({"role": "user", "content": tool_results})

    return {"answer": "Could not generate an answer after multiple searches.", "sources": sources}
