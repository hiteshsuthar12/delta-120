import axios from 'axios';
import type { DashboardData, StrategySettings, Trade, ActivityLog, MarketTicker } from './types';

// Support Vercel / Remote Backend URL via environment variable
const baseURL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const fetchDashboard = async (): Promise<DashboardData> => {
  const res = await api.get('/dashboard');
  return res.data;
};

export const fetchMarketTicker = async (symbol: string = 'BTCUSD'): Promise<MarketTicker> => {
  const res = await api.get('/market/ticker', { params: { symbol } });
  return res.data;
};

export const fetchChartCandles = async (params?: {
  symbol?: string;
  resolution?: string;
  limit?: number;
}): Promise<{
  symbol: string;
  resolution: string;
  current_price: number;
  latest_ema: number;
  candles: { time: number; open: number; high: number; low: number; close: number }[];
  ema: { time: number; value: number }[];
}> => {
  const res = await api.get('/chart/candles', { params });
  return res.data;
};

export const fetchStrategySettings = async (): Promise<StrategySettings> => {
  const res = await api.get('/strategy/settings');
  return res.data;
};

export const updateStrategySettings = async (settings: StrategySettings): Promise<any> => {
  const res = await api.put('/strategy/settings', settings);
  return res.data;
};

export const startBot = async (mode: 'PAPER' | 'LIVE', liveConfirmation: boolean = false): Promise<any> => {
  const res = await api.post('/bot/start', {
    mode,
    live_confirmation: liveConfirmation,
  });
  return res.data;
};

export const stopBot = async (): Promise<any> => {
  const res = await api.post('/bot/stop');
  return res.data;
};

export const emergencyStop = async (): Promise<any> => {
  const res = await api.post('/bot/emergency-stop');
  return res.data;
};

export const fetchTrades = async (params?: {
  symbol?: string;
  direction?: string;
  date?: string;
  limit?: number;
}): Promise<Trade[]> => {
  const res = await api.get('/trades', { params });
  return res.data;
};

export const fetchLogs = async (limit: number = 50): Promise<ActivityLog[]> => {
  const res = await api.get('/logs', { params: { limit } });
  return res.data;
};

export const connectExchange = async (data: {
  api_key: string;
  api_secret: string;
  environment: string;
}): Promise<any> => {
  const res = await api.post('/exchange/connect', data);
  return res.data;
};

export const testExchangeConnection = async (): Promise<any> => {
  const res = await api.post('/exchange/test-connection');
  return res.data;
};

export default api;
