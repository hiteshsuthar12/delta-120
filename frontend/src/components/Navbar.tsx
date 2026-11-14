import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, ShieldAlert, KeyRound, Sliders, RefreshCw } from 'lucide-react';

interface NavbarProps {
  botStatus: string;
  tradingMode: string;
  exchangeConnected: boolean;
  onOpenApiSettings: () => void;
  onOpenStrategySettings: () => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  botStatus,
  tradingMode,
  exchangeConnected,
  onOpenApiSettings,
  onOpenStrategySettings,
  onRefresh,
  isRefreshing = false,
}) => {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleString('en-US', {
          timeZone: 'Asia/Kolkata',
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        }) + ' IST'
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const isRunning = botStatus === 'RUNNING';
  const isEmergency = botStatus === 'EMERGENCY_STOPPED';
  const isLive = tradingMode === 'LIVE';

  return (
    <header className="bg-slate-900/90 backdrop-blur border-b border-slate-800 sticky top-0 z-40 px-4 lg:px-8 py-3">
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 max-w-7xl mx-auto">
        {/* Brand & Logo */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Activity className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-white tracking-tight">EMA 120 BOT</span>
              <span className="text-xs px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 font-mono">
                DELTA
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Delta Exchange Automated Algorithmic System</p>
          </div>
        </div>

        {/* Status Indicators & Clock */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* Exchange Connection Status */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${
              exchangeConnected
                ? 'bg-emerald-950/60 border-emerald-800/80 text-emerald-400'
                : 'bg-amber-950/50 border-amber-800/60 text-amber-400'
            }`}
          >
            {exchangeConnected ? (
              <>
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Exchange Connected</span>
              </>
            ) : (
              <>
                <span className="h-2 w-2 rounded-full bg-amber-400" />
                <ShieldAlert className="h-3.5 w-3.5" />
                <span>Exchange Standby</span>
              </>
            )}
          </div>

          {/* Mode Indicator: Paper vs Live */}
          <div
            className={`px-2.5 py-1 rounded-full font-semibold border ${
              isLive
                ? 'bg-red-950/80 border-red-700 text-red-300 animate-pulse'
                : 'bg-indigo-950/60 border-indigo-800 text-indigo-300'
            }`}
          >
            {isLive ? '🔴 LIVE TRADING' : '📝 PAPER TRADING'}
          </div>

          {/* Bot State Badge */}
          <div
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold border ${
              isRunning
                ? 'bg-emerald-950/80 border-emerald-700 text-emerald-300'
                : isEmergency
                ? 'bg-rose-950/90 border-rose-600 text-rose-300'
                : 'bg-slate-800 border-slate-700 text-slate-300'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isRunning ? 'bg-emerald-400 animate-ping' : isEmergency ? 'bg-rose-500' : 'bg-slate-500'
              }`}
            />
            <span>{botStatus}</span>
          </div>

          {/* Live Clock */}
          <div className="text-slate-400 font-mono hidden sm:block bg-slate-800/60 px-2.5 py-1 rounded border border-slate-700/60">
            {timeStr}
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1.5 ml-2">
            <button
              onClick={onRefresh}
              title="Refresh Data"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin text-blue-400' : ''}`} />
            </button>
            <button
              onClick={onOpenStrategySettings}
              title="Strategy Settings"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            >
              <Sliders className="h-4 w-4" />
            </button>
            <button
              onClick={onOpenApiSettings}
              title="Exchange API Settings"
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition shadow-sm"
            >
              <KeyRound className="h-3.5 w-3.5" />
              <span>API Keys</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

