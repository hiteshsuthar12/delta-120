import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  fetchDashboard,
  fetchMarketTicker,
  startBot,
  stopBot,
  emergencyStop,
  updateStrategySettings,
} from './api';
import type { DashboardData, StrategySettings, MarketTicker } from './types';
import { Navbar } from './components/Navbar';
import { LiveTickerStrip } from './components/LiveTickerStrip';
import { AccountOverviewCards } from './components/AccountOverviewCards';
import { BotControlPanel } from './components/BotControlPanel';
import { LivePositionCard } from './components/LivePositionCard';
import { TradingSignalPanel } from './components/TradingSignalPanel';
import { TradingChart } from './components/TradingChart';
import { TradeHistoryTable } from './components/TradeHistoryTable';
import { ActivityLogsCard } from './components/ActivityLogsCard';
import { StrategySettingsCard } from './components/StrategySettingsCard';
import { ApiSettingsModal } from './components/ApiSettingsModal';
import { LiveConfirmationModal } from './components/LiveConfirmationModal';
import { CheckCircle2, AlertTriangle } from 'lucide-react';

export const App: React.FC = () => {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number>(73800.5);
  const [currentEma, setCurrentEma] = useState<number>(75295.4);
  const [liveTicker, setLiveTicker] = useState<MarketTicker | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'warning' | 'error' } | null>(null);

  // Modals state
  const [isApiSettingsOpen, setIsApiSettingsOpen] = useState<boolean>(false);
  const [isStrategySettingsOpen, setIsStrategySettingsOpen] = useState<boolean>(false);
  const [isLiveConfirmOpen, setIsLiveConfirmOpen] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  const showToast = (message: string, type: 'success' | 'warning' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4500);
  };

  // Initial dashboard load
  const loadDashboard = useCallback(async (quiet: boolean = false) => {
    if (!quiet) setIsRefreshing(true);
    try {
      const data = await fetchDashboard();
      setDashboard(data);
      if (data.live_ticker) {
        setLiveTicker(data.live_ticker);
        if (data.live_ticker.mark_price) {
          setCurrentPrice(data.live_ticker.mark_price);
        }
      } else if (data.current_position?.current_price) {
        setCurrentPrice(data.current_position.current_price);
      } else if (data.last_signal?.close_price) {
        setCurrentPrice(data.last_signal.close_price);
      }
      if (data.last_signal?.ema_value) {
        setCurrentEma(data.last_signal.ema_value);
      }
    } catch (err: any) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setIsRefreshing(false);
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(() => {
      loadDashboard(true);
    }, 5000);
    return () => clearInterval(interval);
  }, [loadDashboard]);

  // High-frequency fast ticker sync (ensures data is always fresh even if WS reconnects)
  useEffect(() => {
    const fetchFastTicker = async () => {
      try {
        const fresh = await fetchMarketTicker('BTCUSD');
        if (fresh && fresh.mark_price) {
          setLiveTicker(fresh);
          setCurrentPrice(fresh.mark_price);
        }
      } catch (err) {
        // quiet error
      }
    };

    const tickerInterval = setInterval(fetchFastTicker, 1200);
    return () => clearInterval(tickerInterval);
  }, []);

  // WebSocket Live Connection
  useEffect(() => {
    let pingInterval: any = null;

    const connectWs = () => {
      // Determine WebSocket endpoint (supports Vercel env variable VITE_WS_URL or local dev)
      let wsUrl: string;
      if (import.meta.env.VITE_WS_URL) {
        wsUrl = import.meta.env.VITE_WS_URL;
      } else {
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        wsUrl = isLocal
          ? `ws://${window.location.hostname}:8000/ws/live`
          : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/live`;
      }

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected to live bot stream at', wsUrl);
        // Periodic heartbeat ping
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 10000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Dedicated Real-time Delta Ticker Stream
          if (data.type === 'TICKER_FEED' && data.ticker) {
            setLiveTicker(data.ticker);
            if (data.ticker.mark_price) {
              setCurrentPrice(data.ticker.mark_price);
            }
          }

          if (data.type === 'TICK_UPDATE') {
            if (data.price) setCurrentPrice(data.price);
            if (data.ema) setCurrentEma(data.ema);
            if (data.live_ticker) setLiveTicker(data.live_ticker);

            setDashboard((prev) => {
              if (!prev) return prev;
              const prevPos = prev.current_position;
              const newPos = data.current_position;

              if (!prevPos && newPos) {
                showToast(`New ${newPos.direction} position opened on ${newPos.symbol} @ $${newPos.entry_price}`, 'success');
              } else if (prevPos && !newPos) {
                showToast(`Position closed on ${prevPos.symbol}`, 'success');
              }

              return {
                ...prev,
                bot_status: data.bot_status || prev.bot_status,
                state_machine_stage: data.state_machine_stage || prev.state_machine_stage,
                current_position: data.current_position,
                account: data.account || prev.account,
                daily_trade_count: data.daily_trade_count !== undefined ? data.daily_trade_count : prev.daily_trade_count,
                live_ticker: data.live_ticker || prev.live_ticker,
              };
            });
          }
        } catch (e) {
          console.error('WebSocket parse error:', e);
        }
      };

      ws.onclose = () => {
        if (pingInterval) clearInterval(pingInterval);
        console.log('WebSocket disconnected. Reconnecting in 2s...');
        reconnectTimeoutRef.current = setTimeout(connectWs, 2000);
      };

      ws.onerror = (e) => {
        console.warn('WebSocket encountered error:', e);
        ws.close();
      };
    };

    connectWs();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (pingInterval) clearInterval(pingInterval);
    };
  }, []);

  // Bot Control Actions
  const handleStartBot = async (mode: 'PAPER' | 'LIVE', liveConfirmation: boolean = false) => {
    try {
      await startBot(mode, liveConfirmation);
      showToast(`Bot started in ${mode} mode!`, 'success');
      loadDashboard(true);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to start bot', 'error');
    }
  };

  const handleStopBot = async () => {
    try {
      await stopBot();
      showToast('Bot stopped safely.', 'warning');
      loadDashboard(true);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to stop bot', 'error');
    }
  };

  const handleEmergencyStop = async () => {
    try {
      await emergencyStop();
      showToast('EMERGENCY STOP TRIGGERED: Orders cancelled and positions flattened.', 'error');
      loadDashboard(true);
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Emergency stop error', 'error');
    }
  };

  const handleToggleAutoTrading = async (enabled: boolean) => {
    if (!dashboard) return;
    try {
      const updated: StrategySettings = {
        ...dashboard.strategy_settings,
        trading_enabled: enabled,
      };
      await updateStrategySettings(updated);
      showToast(`Automated trading ${enabled ? 'ENABLED' : 'PAUSED'}`, 'success');
      loadDashboard(true);
    } catch (err: any) {
      showToast('Failed to toggle auto trading', 'error');
    }
  };

  const handleSaveStrategySettings = async (updated: StrategySettings): Promise<boolean> => {
    try {
      await updateStrategySettings(updated);
      showToast('Strategy configuration saved to MongoDB!', 'success');
      loadDashboard(true);
      return true;
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to save settings', 'error');
      return false;
    }
  };

  if (isLoading && !dashboard) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white">
        <div className="h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
        <h2 className="text-base font-bold tracking-wider">CONNECTING TO EMA 120 TRADING ENGINE...</h2>
        <p className="text-xs text-slate-400 mt-1">Initializing database state & Delta Exchange market feeds</p>
      </div>
    );
  }

  const defaultAccount = {
    total_balance: 10000.0,
    available_balance: 10000.0,
    used_margin: 0.0,
    today_realized_pnl: 0.0,
    today_unrealized_pnl: 0.0,
    today_trades_count: 0,
    winning_trades: 0,
    losing_trades: 0,
  };

  const account = dashboard?.account || defaultAccount;
  const botStatus = dashboard?.bot_status || 'STOPPED';
  const tradingMode = dashboard?.trading_mode || 'PAPER';
  const exchangeConnected = dashboard?.exchange_connected || false;
  const position = dashboard?.current_position || null;
  const lastSignal = dashboard?.last_signal || null;
  const strategySettings = dashboard?.strategy_settings || {
    symbol: 'BTCUSD',
    timeframe: '1h',
    ema_period: 120,
    target_points: 1500,
    stop_loss_points: 100,
    max_daily_trades: 2,
    position_size_percentage: 100,
    leverage: 25,
    daily_reset_timezone: 'Asia/Kolkata',
    allow_buy: true,
    allow_sell: true,
    trading_enabled: true,
  };
  const recentTrades = dashboard?.recent_trades || [];
  const recentLogs = dashboard?.recent_logs || [];

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* 1. TOP NAVIGATION */}
      <Navbar
        botStatus={botStatus}
        tradingMode={tradingMode}
        exchangeConnected={exchangeConnected}
        onOpenApiSettings={() => setIsApiSettingsOpen(true)}
        onOpenStrategySettings={() => setIsStrategySettingsOpen(true)}
        onRefresh={() => loadDashboard(false)}
        isRefreshing={isRefreshing}
      />

      {/* Toast Notification Banner */}
      {toast && (
        <div className="fixed top-16 right-6 z-50 animate-in slide-in-from-top-3 fade-in duration-200">
          <div
            className={`px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 border text-xs font-semibold ${
              toast.type === 'success'
                ? 'bg-emerald-950 border-emerald-700 text-emerald-300'
                : toast.type === 'warning'
                ? 'bg-amber-950 border-amber-700 text-amber-300'
                : 'bg-rose-950 border-rose-700 text-rose-300'
            }`}
          >
            {toast.type === 'success' && <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />}
            {toast.type === 'warning' && <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />}
            {toast.type === 'error' && <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />}
            <span>{toast.message}</span>
          </div>
        </div>
      )}

      {/* MAIN CONTAINER */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-6 space-y-5">
        {/* LIVE DELTA EXCHANGE INDIA MARKET TICKER STRIP */}
        <LiveTickerStrip ticker={liveTicker} />

        {/* 2. ACCOUNT OVERVIEW CARDS */}
        <AccountOverviewCards
          account={account}
          maxDailyTrades={strategySettings.max_daily_trades || 2}
        />

        {/* 3. BOT CONTROL PANEL */}
        <BotControlPanel
          botStatus={botStatus}
          tradingMode={tradingMode}
          tradingEnabled={strategySettings.trading_enabled}
          onStartBot={handleStartBot}
          onStopBot={handleStopBot}
          onEmergencyStop={handleEmergencyStop}
          onToggleTradingEnabled={handleToggleAutoTrading}
          onRequestLiveModeConfirmation={() => setIsLiveConfirmOpen(true)}
          isLoading={isRefreshing}
        />

        {/* 10. TRADINGVIEW CANDLESTICK CHART WITH EMA 120 OVERLAY (MATCHING IMAGE 1) */}
        <TradingChart
          symbol={strategySettings.symbol || 'BTCUSD'}
          currentPrice={currentPrice}
          currentEma={currentEma}
          position={position}
          recentTrades={recentTrades}
          liveTicker={liveTicker}
        />

        {/* 5, 6 & 8. LIVE TRADING POSITION + TRADING SIGNAL PANEL + ACTIVITY LOGS */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <LivePositionCard
            position={position}
            currentMarketPrice={currentPrice}
          />
          <TradingSignalPanel
            lastSignal={lastSignal}
            currentEma={currentEma}
            currentPrice={currentPrice}
          />
          <ActivityLogsCard logs={recentLogs} />
        </div>

        {/* 7. TRADE HISTORY TABLE */}
        <TradeHistoryTable trades={recentTrades} />
      </main>

      {/* Footer Disclaimer */}
      <footer className="border-t border-slate-900 bg-slate-950/70 py-4 px-6 text-center text-xs text-slate-500">
        <p>Automated EMA 120 Trading Bot for Delta Exchange • Strict One Open Position Rule • Max 2 Trades / Day</p>
        <p className="text-[11px] text-slate-600 mt-1">Financial safety warning: Algorithmic trading involves significant capital risk. Always paper-trade before activating live mode.</p>
      </footer>

      {/* MODALS */}
      {/* 4. Strategy Settings Modal */}
      <StrategySettingsCard
        settings={strategySettings}
        isOpen={isStrategySettingsOpen}
        onClose={() => setIsStrategySettingsOpen(false)}
        onSave={handleSaveStrategySettings}
      />

      {/* 9. API Settings Modal */}
      <ApiSettingsModal
        isOpen={isApiSettingsOpen}
        onClose={() => setIsApiSettingsOpen(false)}
        onConnectionSuccess={() => loadDashboard(true)}
      />

      {/* Live Trading Explicit Confirmation Modal */}
      <LiveConfirmationModal
        isOpen={isLiveConfirmOpen}
        onClose={() => setIsLiveConfirmOpen(false)}
        onConfirm={() => handleStartBot('LIVE', true)}
        leverage={strategySettings.leverage || 25}
        positionSizePct={strategySettings.position_size_percentage || 100}
      />
    </div>
  );
};

export default App;
