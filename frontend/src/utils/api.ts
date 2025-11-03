// Frontend API utility functions
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export interface PortfolioSnapshot {
  timestamp: string;
  total_value: number;
  cash: number;
  equity_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  positions: Record<string, {
    quantity: number;
    avg_cost: number;
    current_price: number;
    market_value: number;
  }>;
  positions_pnl: Record<string, {
    unrealized_pnl: number;
    unrealized_pnl_pct: number;
  }>;
}

export interface ApiResponse<T> {
  ok: boolean;
  error?: string;
  [key: string]: any;
}

/**
 * Fetch real-time portfolio data
 */
export async function fetchRealTimePortfolio(): Promise<PortfolioSnapshot | null> {
  try {
    const response = await fetch(`${API_BASE}/api/portfolio/real-time`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data: ApiResponse<PortfolioSnapshot> = await response.json();
    
    if (!data.ok || data.error) {
      throw new Error(data.error || 'Failed to load portfolio');
    }

    // Extract portfolio data (it's merged with ok field)
    const { ok, error, ...portfolioData } = data;
    return portfolioData as PortfolioSnapshot;
  } catch (err) {
    if (err instanceof Error) {
      if (err.name === 'AbortError' || err.name === 'TimeoutError') {
        throw new Error('Request timeout, please check your network connection');
      }
      throw err;
    }
    throw new Error('Unknown error occurred');
  }
}

/**
 * Fetch equity history for charts
 */
export async function fetchEquityHistory(limit: number = 60): Promise<any[]> {
  try {
    const response = await fetch(`${API_BASE}/api/portfolio/equity-history?limit=${limit}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(10000),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    if (!data.ok || data.error) {
      console.warn('Equity history not available:', data.error);
      return [];
    }

    // Transform data for chart
    return (data.records || []).map((item: any) => ({
      date: item.date || item.timestamp?.split('T')[0] || '',
      value: item.total_value || 0,
      pnl: item.total_pnl || 0,
    }));
  } catch (err) {
    console.error('Failed to fetch equity history:', err);
    return [];
  }
}

/**
 * Check API connection health
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Get API base URL
 */
export function getApiBase(): string {
  return API_BASE;
}

