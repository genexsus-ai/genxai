import { useEffect, useMemo, useState } from 'react'
import './index.css'

type AuthMode = 'login' | 'register'

type Preferences = {
  origin: string
  destination: string
  start_date: string
  end_date: string
  travelers: number
  budget: number
  interests: string
}

type PlanResult = {
  session_id: number
  plan_id: number
  coordinator: Record<string, unknown>
  final_approval?: {
    approved: boolean | null
    reason?: string
    required_changes?: string[]
  }
  final_approval_raw?: Record<string, unknown>
  delegator: Record<string, unknown>
  itinerary: {
    days: Array<{ day: number; theme: string; details?: unknown }>
    raw?: string
  }
  budget_breakdown: { items?: Record<string, number>; raw?: string }
  recommendations: { summary?: string; raw?: string; items?: unknown[] }
  summary_highlights?: string[]
  summary_daily_recommendations?: Array<{ day?: number; activities?: string[] }>
  summary: string
  workflow?: {
    progress?: Array<{ node_id?: string; event?: string; status?: string; message?: string }>
  }
}

type LiveNodeEvent = {
  node_id?: string
  event?: string
  status?: string
  message?: string
  output?: unknown
  text_output?: string
  timestamp?: string
}

type ActivityEvent = LiveNodeEvent & { id: string }

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'

function App() {
  const [authMode, setAuthMode] = useState<AuthMode>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [status, setStatus] = useState<string>('')
  const [liveNodes, setLiveNodes] = useState<Record<string, LiveNodeEvent>>({})
  const [activityEvents, setActivityEvents] = useState<ActivityEvent[]>([])
  const [agentTranscripts, setAgentTranscripts] = useState<Record<string, string[]>>({})
  const [preferences, setPreferences] = useState<Preferences>({
    origin: 'NYC',
    destination: 'Barcelona',
    start_date: '2026-06-01',
    end_date: '2026-06-07',
    travelers: 2,
    budget: 2200,
    interests: 'food, culture, seaside',
  })
  const [result, setResult] = useState<PlanResult | null>(null)
  const [rawPayload, setRawPayload] = useState<string>('')

  const getApprovalStatus = (approval?: PlanResult['final_approval']) => {
    if (!approval) return { label: 'Pending', tone: 'pending' }
    if (approval.approved === null) return { label: 'Pending', tone: 'pending' }
    return approval.approved
      ? { label: 'Approved', tone: 'approved' }
      : { label: 'Needs changes', tone: 'needs-changes' }
  }

  const stringify = (value: unknown) => {
    if (!value) return ''
    if (typeof value === 'string') return value
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return String(value)
    }
  }

  const parseSummary = (summary?: string) => {
    if (!summary) return 'Plan generated.'
    const trimmed = summary.trim()
    const withoutFence = trimmed.replace(/```json|```/g, '').trim()
    const start = withoutFence.indexOf('{')
    const end = withoutFence.lastIndexOf('}')
    if (start === -1 || end === -1 || end <= start) return summary
    const jsonSlice = withoutFence.slice(start, end + 1)
    try {
      const parsed = JSON.parse(jsonSlice)
      if (parsed?.summary) return String(parsed.summary)
    } catch {
      return summary.replace(/```json|```/g, '').trim()
    }
    return summary
  }

  const approvalStatus = getApprovalStatus(result?.final_approval)

  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      setStatus(`UI error: ${event.message}`)
    }
    const handleRejection = (event: PromiseRejectionEvent) => {
      setStatus(`UI error: ${event.reason}`)
    }

    window.addEventListener('error', handleError)
    window.addEventListener('unhandledrejection', handleRejection)

    if (token) {
      localStorage.setItem('token', token)
    } else {
      localStorage.removeItem('token')
    }

    return () => {
      window.removeEventListener('error', handleError)
      window.removeEventListener('unhandledrejection', handleRejection)
    }
  }, [token])

  const interestList = useMemo(
    () => preferences.interests.split(',').map((item: string) => item.trim()).filter(Boolean),
    [preferences.interests],
  )

  const submitAuth = async () => {
    setStatus('Authenticating...')
    const endpoint = authMode === 'login' ? 'login' : 'register'
    const response = await fetch(`${apiBase}/auth/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!response.ok) {
      setStatus('Authentication failed.')
      return
    }
    const data = await response.json()
    setToken(data.access_token)
    setStatus('Authenticated.')
  }

  const submitPlan = async () => {
    if (!token) return
    setStatus('Starting planner...')
    setLiveNodes({})
    setActivityEvents([])
    setAgentTranscripts({})
    setResult(null)
    setRawPayload('')

    const response = await fetch(`${apiBase}/planner/plan/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        session_title: `${preferences.destination} getaway`,
        preferences: {
          ...preferences,
          interests: interestList,
        },
      }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      setStatus(`Planner request failed (${response.status}). ${errorText || ''}`.trim())
      return
    }

    if (!response.body) {
      setStatus('Streaming not supported by browser.')
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          if (!part.startsWith('data:')) continue
          const payload = part.replace('data: ', '').trim()
          if (!payload) continue
          const parsed = JSON.parse(payload)
          if (parsed.event === 'node') {
            const nodeData = parsed.data as LiveNodeEvent
            const nodeKey = nodeData.node_id || 'unknown'
            const eventId = `${nodeKey}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
            setLiveNodes((prev) => ({
              ...prev,
              [nodeKey]: {
                ...(prev[nodeKey] || {}),
                ...nodeData,
              },
            }))
            setActivityEvents((prev) => [
              {
                id: eventId,
                ...nodeData,
              },
              ...prev,
            ])
            const textOutput = nodeData.text_output || nodeData.message || ''
            if (textOutput) {
              setAgentTranscripts((prev) => {
                const existing = prev[nodeKey] || []
                if (nodeData.event === 'token') {
                  const last = existing[existing.length - 1] || ''
                  const updated = [...existing.slice(0, -1), `${last}${textOutput}`]
                  return {
                    ...prev,
                    [nodeKey]: updated.length ? updated : [textOutput],
                  }
                }
                return {
                  ...prev,
                  [nodeKey]: [...existing, textOutput],
                }
              })
            }
            if (nodeKey === 'coordinator_node' && nodeData.status) {
              setStatus(`Final approval: ${nodeData.status}`)
            }
          }
          if (parsed.event === 'complete') {
            console.log('Planner complete payload:', parsed.data)
            setResult(parsed.data)
            const payloadText = JSON.stringify(parsed.data, null, 2)
            setRawPayload(
              payloadText.length > 5000 ? `${payloadText.slice(0, 5000)}\n...truncated` : payloadText,
            )
            setStatus('Plan ready.')
          }
          if (parsed.event === 'error') {
            setStatus(parsed.data?.message || 'Planner failed.')
            if (parsed.data) {
              const payloadText = JSON.stringify(parsed.data, null, 2)
              setRawPayload(
                payloadText.length > 5000 ? `${payloadText.slice(0, 5000)}\n...truncated` : payloadText,
              )
            }
          }
        }
      }
    } catch (error) {
      setStatus(`Stream parsing error: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  const logout = () => {
    setToken(null)
    setStatus('Logged out.')
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>GenXAI Travel Planning Agent</h1>
          <p>JWT-protected, streaming itinerary planner powered by GenXAI + Enterprise.</p>
        </div>
        {token ? (
          <button className="secondary" onClick={logout}>
            Sign out
          </button>
        ) : null}
      </header>

      {!token ? (
        <section className="card">
          <h2>Sign in</h2>
          <div className="toggle">
            <button
              className={authMode === 'login' ? 'active' : ''}
              onClick={() => setAuthMode('login')}
            >
              Login
            </button>
            <button
              className={authMode === 'register' ? 'active' : ''}
              onClick={() => setAuthMode('register')}
            >
              Register
            </button>
          </div>
          <div className="form-grid">
            <label>
              Username
              <input value={username} onChange={(e) => setUsername(e.target.value)} />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
          </div>
          <button onClick={submitAuth}>Continue</button>
        </section>
      ) : (
        <section className="grid">
          <div className="card compact-approval">
            <h2>Approval Snapshot</h2>
            {result?.final_approval ? (
              <>
                <p>
                  <strong>Status:</strong>{' '}
                  <span className={`approval-badge ${approvalStatus.tone}`}>
                    {approvalStatus.label}
                  </span>
                </p>
                {result.final_approval.reason ? (
                  <p className="muted">{result.final_approval.reason}</p>
                ) : (
                  <p className="muted">Waiting for approval details.</p>
                )}
              </>
            ) : (
              <p className="muted">No approval data yet.</p>
            )}
          </div>
          <div className="card">
            <h2>Trip Preferences</h2>
            <div className="form-grid">
              <label>
                Origin
                <input
                  value={preferences.origin}
                  onChange={(e) => setPreferences({ ...preferences, origin: e.target.value })}
                />
              </label>
              <label>
                Destination
                <input
                  value={preferences.destination}
                  onChange={(e) => setPreferences({ ...preferences, destination: e.target.value })}
                />
              </label>
              <label>
                Start date
                <input
                  type="date"
                  value={preferences.start_date}
                  onChange={(e) => setPreferences({ ...preferences, start_date: e.target.value })}
                />
              </label>
              <label>
                End date
                <input
                  type="date"
                  value={preferences.end_date}
                  onChange={(e) => setPreferences({ ...preferences, end_date: e.target.value })}
                />
              </label>
              <label>
                Travelers
                <input
                  type="number"
                  min={1}
                  value={preferences.travelers}
                  onChange={(e) =>
                    setPreferences({ ...preferences, travelers: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                Budget ($)
                <input
                  type="number"
                  min={0}
                  value={preferences.budget}
                  onChange={(e) => setPreferences({ ...preferences, budget: Number(e.target.value) })}
                />
              </label>
              <label className="full">
                Interests (comma-separated)
                <input
                  value={preferences.interests}
                  onChange={(e) => setPreferences({ ...preferences, interests: e.target.value })}
                />
              </label>
            </div>
            <button onClick={submitPlan}>Generate itinerary</button>
          </div>

          <div className="card">
            <h2>Agent Text Output (Real-Time)</h2>
            {Object.keys(agentTranscripts).length === 0 ? <p>No activity yet.</p> : null}
            <div className="agent-console">
              {Object.entries(agentTranscripts).map(([nodeId, lines]) => (
                <div className="agent-panel" key={nodeId}>
                  <div className="agent-header">
                    <strong>{nodeId}</strong>
                    {liveNodes[nodeId]?.status ? (
                      <span>Status: {liveNodes[nodeId]?.status}</span>
                    ) : null}
                    {nodeId === 'coordinator_node' && result?.final_approval ? (
                      <span className={`approval-badge ${approvalStatus.tone}`}>
                        {approvalStatus.label}
                      </span>
                    ) : null}
                  </div>
                  <div className="agent-log">
                    {lines.map((line, idx) => (
                      <p key={`${nodeId}-${idx}`}>{line}</p>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h2>Plan Summary</h2>
            {result ? (
              <>
                <p>{parseSummary(result.summary)}</p>
                {result.summary_highlights?.length ? (
                  <>
                    <h3>Summary Highlights</h3>
                    <ul>
                      {result.summary_highlights.map((item, index) => (
                        <li key={`highlight-${index}`}>{item}</li>
                      ))}
                    </ul>
                  </>
                ) : null}
                {result.summary_daily_recommendations?.length ? (
                  <>
                    <h3>Daily Recommendations</h3>
                    {result.summary_daily_recommendations.map((dayItem, index) => (
                      <div key={`daily-${index}`} className="daily-block">
                        <strong>Day {dayItem.day ?? index + 1}</strong>
                        <ul>
                          {(dayItem.activities || []).map((activity, activityIndex) => (
                            <li key={`activity-${index}-${activityIndex}`}>{activity}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </>
                ) : null}
                {result.final_approval ? (
                  <div className="approval-block">
                    <h3>Final Approval</h3>
                    <p>
                      <strong>Status:</strong>{' '}
                      <span className={`approval-badge ${approvalStatus.tone}`}>
                        {approvalStatus.label}
                      </span>
                    </p>
                    {result.final_approval.reason ? (
                      <p>
                        <strong>Reason:</strong> {result.final_approval.reason}
                      </p>
                    ) : null}
                    {result.final_approval.required_changes?.length ? (
                      <>
                        <h4>Required Changes</h4>
                        <ul>
                          {result.final_approval.required_changes.map((item, index) => (
                            <li key={`required-change-${index}`}>{item}</li>
                          ))}
                        </ul>
                      </>
                    ) : null}
                    {!result.final_approval.reason && result.final_approval_raw ? (
                      <div className="raw-block">
                        <h4>Approval Raw Output</h4>
                        <pre>{stringify(result.final_approval_raw)}</pre>
                      </div>
                    ) : null}
                  </div>
                ) : null}
                <h3>Itinerary</h3>
                <ul>
                  {result.itinerary?.days?.length ? (
                    result.itinerary.days.map((day) => (
                      <li key={day.day}>
                        <strong>Day {day.day}:</strong> {day.theme}
                        {day.details ? (
                          <p className="detail">{stringify(day.details)}</p>
                        ) : null}
                      </li>
                    ))
                  ) : (
                    <li className="muted">No itinerary details available yet.</li>
                  )}
                </ul>
                {(!result.itinerary?.days?.length ||
                  result.itinerary.days.every((day) => !day.theme)) &&
                result.itinerary?.raw ? (
                  <div className="raw-block">
                    <h4>Itinerary Raw Output</h4>
                    <pre>{result.itinerary.raw}</pre>
                  </div>
                ) : null}
                <h3>Budget</h3>
                <ul>
                  {result.budget_breakdown?.items &&
                  Object.keys(result.budget_breakdown.items).length ? (
                    Object.entries(result.budget_breakdown.items).map(([key, value]) => (
                      <li key={key}>
                        {key}: ${value}
                      </li>
                    ))
                  ) : (
                    <li className="muted">No budget breakdown available yet.</li>
                  )}
                </ul>
                {!result.budget_breakdown?.items && result.budget_breakdown?.raw ? (
                  <div className="raw-block">
                    <h4>Budget Raw Output</h4>
                    <pre>{result.budget_breakdown.raw}</pre>
                  </div>
                ) : null}
                {result.recommendations?.items?.length ? (
                  <>
                    <h3>Recommendations</h3>
                    <ul>
                      {result.recommendations.items.map((item, index) => (
                        <li key={`${index}-${stringify(item).slice(0, 8)}`}>
                          {stringify(item)}
                        </li>
                      ))}
                    </ul>
                  </>
                ) : null}
                {!result.recommendations?.items?.length && result.recommendations?.raw ? (
                  <div className="raw-block">
                    <h4>Reviewer Notes</h4>
                    <pre>{result.recommendations.raw}</pre>
                  </div>
                ) : null}
              </>
            ) : (
              <p>Submit a request to see your itinerary.</p>
            )}
          </div>

          <div className="card">
            <h2>Raw Payload</h2>
            {rawPayload ? (
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{rawPayload}</pre>
            ) : (
              <p>No payload received yet.</p>
            )}
          </div>
        </section>
      )}

      {status ? <p className="status">{status}</p> : null}
    </div>
  )
}

export default App