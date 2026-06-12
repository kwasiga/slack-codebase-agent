from ingestion.clone import clone_repo
from ingestion.chunker import chunk_repo
from ingestion.embedder import embed_chunks
from ingestion.store import store_chunks


def run_pipeline(repo_url):
    path = clone_repo(repo_url)
    chunks = chunk_repo(path)
    embedded = embed_chunks(chunks)
    store_chunks(embedded)