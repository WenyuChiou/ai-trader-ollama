// Custom hook for portfolio data management
import { useState, useEffect, useCallback } from 'react';
import { fetchRealTimePortfolio, checkApiHealth, type PortfolioSnapshot } from '../utils/api';

interface UsePortfolioReturn {
  portfolio: PortfolioSnapshot | null;
  loading: boolean;
  error: string | null;
  lastUpdate: Date | null;
  isRefreshing: boolean;
  apiConnected: boolean | null;
  refresh: (showLoading?: boolean) => Promise<void>;
}

export function usePortfolio(autoRefresh: boolean = true, refreshInterval: number = 30000): UsePortfolioReturn {
  const [portfolio, setPortfolio] = useState<PortfolioSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);

  const refresh = useCallback(async (showLoading: boolean = false) => {
    if (showLoading) {
      setIsRefreshing(true);
    }

    try {
      const data = await fetchRealTimePortfolio();
      setPortfolio(data);
      setLastUpdate(new Date());
      setError(null);
      setApiConnected(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setApiConnected(false);
      console.error('Error fetching portfolio:', err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial load and API health check
  useEffect(() => {
    const initialize = async () => {
      // Check API health first
      const isHealthy = await checkApiHealth();
      setApiConnected(isHealthy);
      
      // Then load portfolio
      await refresh(true);
    };
    initialize();
  }, [refresh]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || isRefreshing) return;

    const interval = setInterval(() => {
      refresh(false);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, isRefreshing, refreshInterval, refresh]);

  return {
    portfolio,
    loading,
    error,
    lastUpdate,
    isRefreshing,
    apiConnected,
    refresh,
  };
}

