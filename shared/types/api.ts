// shared/types/api.ts
// API request/response types

import { AgentEvent, AgentStatus, TradingCycleResult } from './events';

export interface RunTradingCycleRequest {
  start?: string;
  end?: string;
  universe?: string[];
  rounds?: number;
  auto_tools?: boolean;
  tool_budget?: number;
  preferred_domains?: string[];
}

export interface RunTradingCycleResponse {
  status: 'success' | 'error';
  result?: TradingCycleResult;
  message?: string;
  error?: string;
}

export interface EventsResponse {
  events: AgentEvent[];
}

export interface AgentsStatusResponse {
  agents: Record<string, AgentStatus>;
}

