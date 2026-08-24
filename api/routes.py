import os
import re
import threading
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from agent.agent import ask
from ingestion.pipeline import run_pipeline

GITHUB_REPO_RE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+(?:\.git)?/?$")


def require_access_key(x_access_key: str | None = Header(default=None)):
    expected = os.getenv("ACCESS_KEY")
    if expected and x_access_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing access key")


router = APIRouter(dependencies=[Depends(require_access_key)])

_jobs: dict[str, dict] = {}


class QueryRequest(BaseModel):
    question: str


class IngestRequest(BaseModel):
    repo_url: str


@router.post("/query")
def query(request: QueryRequest):
    return ask(request.question)


@router.post("/ingest")
def ingest(request: IngestRequest):
    if not GITHUB_REPO_RE.match(request.repo_url):
        raise HTTPException(status_code=400, detail="repo_url must be a public github.com repository URL")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "repo_url": request.repo_url, "error": None}

    def run():
        try:
            run_pipeline(request.repo_url)
            _jobs[job_id]["status"] = "done"
        except Exception as e:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(e)

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


@router.get("/ingest/{job_id}")
def ingest_status(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
