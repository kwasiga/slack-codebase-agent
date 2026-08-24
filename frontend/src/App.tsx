import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { askQuestion, getIngestStatus, setAccessKey, startIngest, UnauthorizedError, type Source } from './api'
import './App.css'

interface Message {
  role: 'user' | 'assistant'
  text: string
  sources?: Source[]
}

type IngestState =
  | { phase: 'idle' }
  | { phase: 'running'; repoUrl: string }
  | { phase: 'done'; repoUrl: string }
  | { phase: 'error'; repoUrl: string; error: string }

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)

  const [repoUrl, setRepoUrl] = useState('')
  const [ingest, setIngest] = useState<IngestState>({ phase: 'idle' })
  const [runningJobId, setRunningJobId] = useState<string | null>(null)

  const [locked, setLocked] = useState(false)
  const [authError, setAuthError] = useState(false)
  const [accessInput, setAccessInput] = useState('')

  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, asking])

  useEffect(() => {
    if (ingest.phase !== 'running' || !runningJobId) return

    const interval = setInterval(async () => {
      try {
        const job = await getIngestStatus(runningJobId)
        if (job.status === 'done') {
          setIngest({ phase: 'done', repoUrl: job.repo_url })
        } else if (job.status === 'error') {
          setIngest({ phase: 'error', repoUrl: job.repo_url, error: job.error ?? 'Ingestion failed' })
        }
      } catch (err) {
        if (err instanceof UnauthorizedError) {
          setLocked(true)
          setAuthError(true)
        }
        // otherwise keep polling; a transient network error shouldn't kill the poll
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [ingest.phase, runningJobId])

  async function handleIngest(e: React.FormEvent) {
    e.preventDefault()
    const url = repoUrl.trim()
    if (!url || ingest.phase === 'running') return

    setIngest({ phase: 'running', repoUrl: url })
    try {
      const { job_id } = await startIngest(url)
      setRunningJobId(job_id)
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        setLocked(true)
        setAuthError(true)
        setIngest({ phase: 'idle' })
        return
      }
      setIngest({ phase: 'error', repoUrl: url, error: err instanceof Error ? err.message : 'Failed to start ingestion' })
    }
  }

  function handleUnlock(e: React.FormEvent) {
    e.preventDefault()
    const code = accessInput.trim()
    if (!code) return
    setAccessKey(code)
    setAccessInput('')
    setAuthError(false)
    setLocked(false)
  }

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault()
    const text = question.trim()
    if (!text || asking) return

    setMessages((prev) => [...prev, { role: 'user', text }])
    setQuestion('')
    setAsking(true)

    try {
      const result = await askQuestion(text)
      setMessages((prev) => [...prev, { role: 'assistant', text: result.answer, sources: result.sources }])
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        setLocked(true)
        setAuthError(true)
        setMessages((prev) => prev.slice(0, -1))
        setQuestion(text)
        return
      }
      const message = err instanceof Error ? err.message : 'Something went wrong.'
      setMessages((prev) => [...prev, { role: 'assistant', text: `Error: ${message}` }])
    } finally {
      setAsking(false)
    }
  }

  if (locked) {
    return (
      <div className="app">
        <div className="gate">
          <p>$ codebase-qa</p>
          <p className="dim">{authError ? 'incorrect access code, try again' : 'access code required'}</p>
          <form onSubmit={handleUnlock}>
            <span className="prompt">&gt;</span>
            <input
              type="password"
              placeholder="access code"
              value={accessInput}
              onChange={(e) => setAccessInput(e.target.value)}
              autoFocus
            />
            <button type="submit" disabled={!accessInput.trim()}>
              [unlock]
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">codebase-qa</span>

        <form className="ingest-form" onSubmit={handleIngest}>
          <span className="prompt">ingest&gt;</span>
          <input
            type="url"
            placeholder="https://github.com/owner/repo"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            disabled={ingest.phase === 'running'}
            required
          />
          <button type="submit" disabled={ingest.phase === 'running'}>
            {ingest.phase === 'running' ? '[running]' : '[run]'}
          </button>
        </form>
      </header>

      {ingest.phase !== 'idle' && (
        <div className={`ingest-status ingest-status--${ingest.phase}`}>
          {ingest.phase === 'running' && <>cloning, chunking, and embedding {ingest.repoUrl} ...</>}
          {ingest.phase === 'done' && <>{ingest.repoUrl} ready. ask a question below.</>}
          {ingest.phase === 'error' && <>failed to ingest {ingest.repoUrl}: {ingest.error}</>}
        </div>
      )}

      <main className="chat" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            <p>$ ask about any codebase</p>
            <p className="dim">ingest a public github repo above, then ask questions in plain english.</p>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`message message--${m.role}`}>
            <span className="prompt">{m.role === 'user' ? '>' : '~'}</span>
            <div className="message-body">
              {m.role === 'assistant' ? (
                <ReactMarkdown>{m.text}</ReactMarkdown>
              ) : (
                <p>{m.text}</p>
              )}
              {m.sources && m.sources.length > 0 && (
                <p className="sources">
                  sources: {[...new Set(m.sources.map((s) => s.file))].join(', ')}
                </p>
              )}
            </div>
          </div>
        ))}

        {asking && (
          <div className="message message--assistant">
            <span className="prompt">~</span>
            <div className="message-body">
              <span className="cursor">_</span>
            </div>
          </div>
        )}
      </main>

      <form className="ask-form" onSubmit={handleAsk}>
        <span className="prompt">&gt;</span>
        <input
          type="text"
          placeholder="how does authentication work?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={asking}
        />
        <button type="submit" disabled={asking || !question.trim()}>
          [ask]
        </button>
      </form>
    </div>
  )
}

export default App
