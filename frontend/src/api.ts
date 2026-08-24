export interface Source {
  file: string
  lines: string
}

export interface AskResponse {
  answer: string
  sources: Source[]
}

export interface IngestJob {
  status: 'running' | 'done' | 'error'
  repo_url: string
  error: string | null
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `Request failed with ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function askQuestion(question: string): Promise<AskResponse> {
  return fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  }).then((res) => handle<AskResponse>(res))
}

export function startIngest(repoUrl: string): Promise<{ job_id: string }> {
  return fetch('/api/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl }),
  }).then((res) => handle<{ job_id: string }>(res))
}

export function getIngestStatus(jobId: string): Promise<IngestJob> {
  return fetch(`/api/ingest/${jobId}`).then((res) => handle<IngestJob>(res))
}
