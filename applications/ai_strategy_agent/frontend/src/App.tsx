import { useMemo, useState } from 'react'
import type { BrainstormRequest, BrainstormResponse, StreamMessage } from './types'
import './App.css'

const DEFAULT_REQUEST: BrainstormRequest = {
  company_name: 'GenXAI Enterprise',
  objectives: ['Accelerate AI adoption', 'Improve customer experience'],
  constraints: ['Budget capped at $2M', 'Regulatory compliance required'],
  horizon: '12 months',
  risk_posture: 'balanced'
}

function App() {
  const [request, setRequest] = useState<BrainstormRequest>(DEFAULT_REQUEST)
  const [streamMessages, setStreamMessages] = useState<StreamMessage[]>([])
  const [response, setResponse] = useState<BrainstormResponse | null>(null)
  const [rankedUseCases, setRankedUseCases] = useState<BrainstormResponse['ai_initiatives']>([])
  const [isStreaming, setIsStreaming] = useState(false)

  const apiBase = useMemo(() => import.meta.env.VITE_API_BASE ?? 'http://localhost:8000', [])

  const handleChange = (field: keyof BrainstormRequest, value: string) => {
    setRequest((prev) => ({ ...prev, [field]: value }))
  }

  const handleListChange = (field: 'objectives' | 'constraints', value: string) => {
    const items = value.split('\n').map((item) => item.trim()).filter(Boolean)
    setRequest((prev) => ({ ...prev, [field]: items }))
  }

  const startBrainstorm = async () => {
    setIsStreaming(true)
    setStreamMessages([])
    setResponse(null)
    setRankedUseCases([])

    const payload = JSON.stringify(request)
    const responseStream = await fetch(`${apiBase}/api/v1/strategy/brainstorm/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload
    })

    if (!responseStream.ok || !responseStream.body) {
      setIsStreaming(false)
      return
    }

    const reader = responseStream.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    const processChunk = (chunk: string) => {
      buffer += chunk
      const parts = buffer.split('\n\n')
      buffer = parts.pop() ?? ''

      parts.forEach((part) => {
        const line = part.split('\n').find((entry) => entry.startsWith('data: '))
        if (!line) return
        const data = JSON.parse(line.replace('data: ', '')) as StreamMessage
        if (data.event === 'done') {
          if (data.strategy_artifact) {
            setResponse({
              executive_summary: data.strategy_artifact.executive_summary,
              strategic_themes: data.strategy_artifact.strategic_themes,
              ai_initiatives: data.strategy_artifact.ai_initiatives,
              prioritized_roadmap: data.strategy_artifact.prioritized_roadmap,
              risks_and_mitigations: data.strategy_artifact.risks_and_mitigations,
              kpis: data.strategy_artifact.kpis,
              termination_reason: data.termination_reason ?? '',
              rounds: streamMessages.length,
              quality_score: 0,
              consensus_score: 0
            })
          }
          if (data.ranked_use_cases) {
            setRankedUseCases(data.ranked_use_cases)
          }
          setIsStreaming(false)
          return
        }
        setStreamMessages((prev) => [...prev, data])
      })
    }

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        processChunk(decoder.decode(value, { stream: true }))
      }
    } catch (error) {
      console.error('Stream error', error)
    } finally {
      setIsStreaming(false)
      reader.releaseLock()
    }
  }

  return (
    <div className="app">
      <header>
        <h1>AI Strategy Brainstorming (P2P)</h1>
        <p>Layered architecture demo with peer-to-peer agents for AI strategy ideation.</p>
      </header>

      <section className="card">
        <h2>Business Context</h2>
        <label>
          Company Name
          <input
            value={request.company_name}
            onChange={(event) => handleChange('company_name', event.target.value)}
          />
        </label>
        <label>
          Objectives (one per line)
          <textarea
            rows={4}
            defaultValue={request.objectives.join('\n')}
            onChange={(event) => handleListChange('objectives', event.target.value)}
          />
        </label>
        <label>
          Constraints (one per line)
          <textarea
            rows={4}
            defaultValue={request.constraints.join('\n')}
            onChange={(event) => handleListChange('constraints', event.target.value)}
          />
        </label>
        <div className="grid">
          <label>
            Horizon
            <input
              value={request.horizon}
              onChange={(event) => handleChange('horizon', event.target.value)}
            />
          </label>
          <label>
            Risk Posture
            <input
              value={request.risk_posture}
              onChange={(event) => handleChange('risk_posture', event.target.value)}
            />
          </label>
        </div>
        <button onClick={startBrainstorm} disabled={isStreaming}>
          {isStreaming ? 'Brainstorming...' : 'Start Brainstorm'}
        </button>
      </section>

      <section className="card">
        <h2>Live Peer Messages</h2>
        {streamMessages.length === 0 ? (
          <p>No messages yet. Start a brainstorm to see peer insights.</p>
        ) : (
          <div className="stream">
            {streamMessages.map((message, index) => (
              <div key={`${message.sender}-${index}`} className="stream-item">
                <strong>{message.role ?? message.sender}</strong>
                <p>{message.content}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {response && (
        <section className="card">
          <h2>Strategy Output</h2>
          <p>{response.executive_summary}</p>
          <h3>Strategic Themes</h3>
          <ul>
            {response.strategic_themes.map((theme) => (
              <li key={theme.title}>
                <strong>{theme.title}</strong>: {theme.rationale}
              </li>
            ))}
          </ul>
          <h3>Initiatives</h3>
          <ul>
            {response.ai_initiatives.map((initiative) => (
              <li key={initiative.name}>
                <strong>{initiative.name}</strong> — {initiative.rationale}
              </li>
            ))}
          </ul>
          <h3>Roadmap</h3>
          <ul>
            {response.prioritized_roadmap.map((item) => (
              <li key={`${item.horizon}-${item.initiative}`}>
                <strong>{item.horizon}</strong>: {item.initiative}
              </li>
            ))}
          </ul>
        </section>
      )}

      {rankedUseCases.length > 0 && (
        <section className="card">
          <h2>Ranked Use Cases</h2>
          <ol>
            {rankedUseCases.map((useCase) => (
              <li key={useCase.name}>
                <strong>{useCase.name}</strong> — {useCase.rationale}
                <div className="muted">
                  Owner: {useCase.owner} · Timeline: {useCase.timeline}
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}
    </div>
  )
}

export default App
