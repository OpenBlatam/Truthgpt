export type Role = 'user' | 'assistant' | 'system';

export type AgentStepType = 'rag' | 'vector_search' | 'swarm' | 'smt_verify' | 'tool' | 'synthesis';

export type AgentStepStatus = 'pending' | 'running' | 'completed' | 'error';

export interface AgentStep {
  id: string;
  type: AgentStepType;
  title: string;
  description: string;
  status: AgentStepStatus;
  duration_ms?: number;
  details?: {
    sources?: Array<{ title: string; score: number; snippet: string; url?: string }>;
    invariants?: string[];
    solver_output?: string;
    agent_name?: string;
    action?: string;
    [key: string]: unknown;
  };
}

export interface ProofCertificate {
  certificate_id: string;
  status: string;
  solver_engine: string;
  verification_time_ms: number;
  confidence_score: number;
  proof_tree_hash: string;
  mathematical_invariants: string[];
  smt_constraints_evaluated?: number;
  tier_rigor_level?: number;
}

export interface SwarmAgentInvolved {
  role_name: string;
  status: string;
  contribution: string;
}

export interface SwarmTrace {
  session_id: string;
  consensus_summary: string;
  agents_involved: SwarmAgentInvolved[];
}

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  timestamp: string;
  isStreaming?: boolean;
  model_used?: string;
  execution_time_ms?: number;
  tokens_consumed?: number;
  agent_steps?: AgentStep[];
  proof_certificate?: ProofCertificate;
  swarm_trace?: SwarmTrace | null;
}

export interface ChatSettings {
  apiUrl: string;
  apiKey: string;
  model: string;
  temperature: number;
  maxTokens: number;
  enableSwarm: boolean;
  enableFormalVerification: boolean;
  enableStreaming: boolean;
}

export interface PredefinedPrompt {
  id: string;
  title: string;
  description: string;
  prompt: string;
  badge: string;
  category: 'smt' | 'rag' | 'swarm' | 'code';
}
