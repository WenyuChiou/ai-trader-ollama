// shared/types/events.ts
// TypeScript type definitions for event system

export interface AgentEvent {
  timestamp: number;
  agent_name: string;
  event_type: string;
  status: 'idle' | 'running' | 'success' | 'error';
  payload: Record<string, any>;
  round_number?: number;
  session_id?: string;
}

export interface AgentStatus {
  status: 'idle' | 'running' | 'success' | 'error';
  last_activity: string | null;
  last_event_type?: string;
  round_number?: number;
}

export interface TradingCycleResult {
  stance: string;
  decision: any;
  rounds: number;
  symbols: string[];
  top_signals: Array<[string, number]>;
  session_id?: string;
}

