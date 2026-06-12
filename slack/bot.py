import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from agent.agent import ask
from ingestion.pipeline import run_pipeline

load_dotenv()

app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)


@app.command("/ask")
def handle_ask(ack, body, say):
    ack()
    result = ask(body["text"])
    text = result["answer"]
    if result["sources"]:
        unique_sources = {s["file"] for s in result["sources"]}
        text += "\n\n*Sources:* " + ", ".join(unique_sources)
    say(text)


@app.command("/ingest")
def handle_ingest(ack, body, say):
    ack()
    repo_url = body["text"]
    say(f"Ingesting {repo_url}...")
    run_pipeline(repo_url)
    say("Done! You can now ask questions about this repo.")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
