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

export class UnauthorizedError extends Error {}

const ACCESS_KEY_STORAGE = 'codebase-qa-access-key'

export function getAccessKey(): string | null {
  try {
    return localStorage.getItem(ACCESS_KEY_STORAGE)
  } catch {
    return null
  }
}

export function setAccessKey(key: string): void {
  try {
    localStorage.setItem(ACCESS_KEY_STORAGE, key)
  } catch {
    // ignore — a private/blocked storage context just means the header stays empty
  }
}

export function clearAccessKey(): void {
  try {
    localStorage.removeItem(ACCESS_KEY_STORAGE)
  } catch {
    // ignore
  }
}

function authHeaders(): Record<string, string> {
  const key = getAccessKey()
  return key ? { 'X-Access-Key': key } : {}
}

async function handle<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    clearAccessKey()
    throw new UnauthorizedError('Invalid or missing access key')
  }
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `Request failed with ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function askQuestion(question: string): Promise<AskResponse> {
  return fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ question }),
  }).then((res) => handle<AskResponse>(res))
}

export function startIngest(repoUrl: string): Promise<{ job_id: string }> {
  return fetch('/api/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ repo_url: repoUrl }),
  }).then((res) => handle<{ job_id: string }>(res))
}

export function getIngestStatus(jobId: string): Promise<IngestJob> {
  return fetch(`/api/ingest/${jobId}`, { headers: authHeaders() }).then((res) => handle<IngestJob>(res))
}
