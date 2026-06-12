from slack.bot import app
from agent.agent import ask


@app.command("/ask")
def handle_ask(ack, body, say):
    ack()
    answer = ask(body["text"])
    say(answer)
    