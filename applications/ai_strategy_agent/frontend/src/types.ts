export interface BrainstormRequest {
  company_name: string
  objectives: string[]
  constraints: string[]
  horizon: string
  risk_posture: string
}

export interface StrategyTheme {
  title: string
  rationale: string
}

export interface Initiative {
  name: string
  rationale: string
  owner: string
  timeline: string
  dependencies: string[]
}

export interface RoadmapItem {
  horizon: string
  initiative: string
  outcomes: string[]
}

export interface RiskMitigation {
  risk: string
  mitigation: string
}

export interface KPI {
  name: string
  target: string
  measurement: string
}

export interface BrainstormResponse {
  executive_summary: string
  strategic_themes: StrategyTheme[]
  ai_initiatives: Initiative[]
  prioritized_roadmap: RoadmapItem[]
  risks_and_mitigations: RiskMitigation[]
  kpis: KPI[]
  termination_reason: string
  rounds: number
  quality_score: number
  consensus_score: number
}

export interface StreamMessage {
  sender?: string
  role?: string
  content?: string
  timestamp?: string
  satisfaction?: number
  wants_to_terminate?: boolean
  event?: string
  termination_reason?: string
  strategy_artifact?: Omit<BrainstormResponse, 'termination_reason' | 'rounds' | 'quality_score' | 'consensus_score'>
  ranked_use_cases?: Initiative[]
}