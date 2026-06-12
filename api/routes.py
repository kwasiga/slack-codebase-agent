from fastapi import APIRouter
from pydantic import BaseModel
from agent.agent import ask

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
def query(request: QueryRequest):
    answer = ask(request.question)
    return {"answer": answer}
