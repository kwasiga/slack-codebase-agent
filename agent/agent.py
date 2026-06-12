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
            tool_use_block = next(b for b in response.content if b.type == "tool_use")
            query = tool_use_block.input["query"]
            top_k = tool_use_block.input.get("top_k", 5)
            chunks = semantic_search(query, top_k)

            sources.extend(
                {"file": c["file_path"], "lines": f"{c['start_line']}-{c['end_line']}"}
                for c in chunks
            )

            tool_result = "\n\n".join(
                f"File: {c['file_path']} (lines {c['start_line']}-{c['end_line']})\n{c['chunk_text']}"
                for c in chunks
            )

            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": tool_result or "No results found."
                    }
                ]
            })

    return {"answer": "Could not generate an answer after multiple searches.", "sources": sources}
