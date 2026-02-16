import { useMemo, useState } from 'react'
import './index.css'

type PlanStep = {
  id: string
  title: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  requires_approval: boolean
}

type TimelineEvent = {
  timestamp: string
  agent: string
  event: string
  content: string
}

type Artifact = {
  id: string
  kind: 'plan' | 'diff' | 'command_output' | 'summary'
  title: string
  content: string
}

type ProposedAction = {
  id: string
  action_type: 'edit' | 'command'
  description: string
  safe: boolean
  status: 'pending' | 'approved' | 'rejected' | 'executed'
  command?: string | null
  file_path?: string | null
  patch?: string | null
}

type RunSession = {
  id: string
  goal: string
  repo_path: string
  status: 'created' | 'awaiting_approval' | 'running' | 'completed' | 'failed'
  plan_steps: PlanStep[]
  timeline: TimelineEvent[]
  artifacts: Artifact[]
  pending_actions: ProposedAction[]
  memory_summary: string
}

function App() {
  const [goal, setGoal] = useState('Add endpoint-level tests for planner API and fix lint issues')
  const [repoPath, setRepoPath] = useState('/Users/irsalimran/Desktop/GenXAI-OSS')
  const [run, setRun] = useState<RunSession | null>(null)
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const apiBase = useMemo(() => import.meta.env.VITE_API_BASE ?? 'http://localhost:8000', [])

  const createRun = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${apiBase}/api/v1/runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, repo_path: repoPath }),
      })
      if (!res.ok) {
        throw new Error(`Failed to create run (${res.status})`)
      }
      const data = (await res.json()) as RunSession
      setRun(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const decide = async (actionId: string, approve: boolean) => {
    if (!run) return
    const res = await fetch(`${apiBase}/api/v1/runs/${run.id}/approval`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId, approve }),
    })
    if (!res.ok) {
      setError(`Failed to decide action (${res.status})`)
      return
    }
    const updated = (await res.json()) as RunSession
    setRun(updated)
  }

  return (
    <main className="app">
      <h1>GenXBot — Autonomous Coding Workflow</h1>
      <p className="muted">Repo ingest → plan → edit → test with approval gates.</p>

      <section className="card">
        <h2>Start Run</h2>
        <label>
          Goal
          <textarea value={goal} onChange={(e) => setGoal(e.target.value)} rows={3} />
        </label>
        <label>
          Repository Path
          <input value={repoPath} onChange={(e) => setRepoPath(e.target.value)} />
        </label>
        <button disabled={loading} onClick={createRun}>
          {loading ? 'Creating…' : 'Create Run'}
        </button>
        {error && <p className="error">{error}</p>}
      </section>

      {run && (
        <>
          <section className="card">
            <h2>Run Status</h2>
            <p>
              <strong>ID:</strong> {run.id}
            </p>
            <p>
              <strong>Status:</strong> {run.status}
            </p>
            <p>
              <strong>Memory:</strong> {run.memory_summary}
            </p>
          </section>

          <section className="card">
            <h2>Plan</h2>
            <ul>
              {run.plan_steps.map((step) => (
                <li key={step.id}>
                  {step.title} <span className="pill">{step.status}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="card">
            <h2>Pending Actions</h2>
            {run.pending_actions.length === 0 ? (
              <p>No actions.</p>
            ) : (
              run.pending_actions.map((action) => (
                <div key={action.id} className="action">
                  <p>
                    <strong>{action.action_type.toUpperCase()}</strong>: {action.description}
                  </p>
                  <p className="muted">Status: {action.status}</p>
                  {action.command && <code>{action.command}</code>}
                  {action.file_path && <code>{action.file_path}</code>}
                  {action.status === 'pending' && (
                    <div className="row">
                      <button onClick={() => decide(action.id, true)}>Approve</button>
                      <button className="danger" onClick={() => decide(action.id, false)}>
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </section>

          <section className="card">
            <h2>Timeline</h2>
            <ul>
              {run.timeline.map((event, idx) => (
                <li key={`${event.timestamp}-${idx}`}>
                  <strong>{event.agent}</strong> · {event.event} — {event.content}
                </li>
              ))}
            </ul>
          </section>

          <section className="card">
            <h2>Artifacts</h2>
            {run.artifacts.map((artifact) => (
              <details key={artifact.id}>
                <summary>
                  {artifact.title} <span className="pill">{artifact.kind}</span>
                </summary>
                <pre>{artifact.content}</pre>
              </details>
            ))}
          </section>
        </>
      )}
    </main>
  )
}

export default App
