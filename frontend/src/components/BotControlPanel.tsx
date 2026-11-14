import React from 'react';
import { Play, Square, AlertOctagon, Shield } from 'lucide-react';

interface Props {
  botStatus: string;
  tradingMode: string;
  tradingEnabled: boolean;
  onStartBot: (mode: 'PAPER' | 'LIVE', liveConfirmation: boolean) => void;
  onStopBot: () => void;
  onEmergencyStop: () => void;
  onToggleTradingEnabled: (enabled: boolean) => void;
  onRequestLiveModeConfirmation: () => void;
  isLoading?: boolean;
}

export const BotControlPanel: React.FC<Props> = ({
  botStatus,
  tradingMode,
  tradingEnabled,
  onStartBot,
  onStopBot,
  onEmergencyStop,
  onToggleTradingEnabled,
  onRequestLiveModeConfirmation,
  isLoading = false,
}) => {
  const isRunning = botStatus === 'RUNNING';

  const handleModeChange = (newMode: 'PAPER' | 'LIVE') => {
    if (newMode === 'LIVE') {
      onRequestLiveModeConfirmation();
    } else {
      onStartBot('PAPER', false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-md">
      <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
        {/* Left: Mode Selection & Auto-trade Toggle */}
        <div className="flex flex-wrap items-center gap-4 w-full lg:w-auto">
          {/* Mode Switcher */}
          <div className="flex items-center p-1 bg-slate-950 rounded-lg border border-slate-800">
            <button
              onClick={() => handleModeChange('PAPER')}
              disabled={isLoading}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                tradingMode === 'PAPER'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Paper Trading
            </button>
            <button
              onClick={() => handleModeChange('LIVE')}
              disabled={isLoading}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center gap-1.5 ${
                tradingMode === 'LIVE'
                  ? 'bg-rose-600 text-white shadow animate-pulse'
                  : 'text-slate-400 hover:text-rose-400'
              }`}
            >
              <Shield className="h-3 w-3" />
              <span>Live Trading</span>
            </button>
          </div>

          {/* Auto-Trading Global Toggle */}
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-300 font-medium">Auto-Trading:</span>
            <button
              onClick={() => onToggleTradingEnabled(!tradingEnabled)}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                tradingEnabled ? 'bg-emerald-500' : 'bg-slate-700'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                  tradingEnabled ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
            <span
              className={`text-[11px] font-mono font-semibold ${
                tradingEnabled ? 'text-emerald-400' : 'text-slate-500'
              }`}
            >
              {tradingEnabled ? 'ENABLED' : 'PAUSED'}
            </span>
          </div>
        </div>

        {/* Right: Main Bot Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto justify-end">
          {/* Start Bot Button */}
          <button
            onClick={() => onStartBot(tradingMode as 'PAPER' | 'LIVE', tradingMode === 'LIVE')}
            disabled={isRunning || isLoading}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition shadow-md ${
              isRunning
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30'
            }`}
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            <span>START BOT</span>
          </button>

          {/* Stop Bot Button */}
          <button
            onClick={onStopBot}
            disabled={!isRunning || isLoading}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition border ${
              !isRunning
                ? 'bg-slate-800/50 text-slate-600 border-slate-800 cursor-not-allowed'
                : 'bg-slate-800 hover:bg-slate-700 text-amber-400 border-amber-600/40 shadow-sm'
            }`}
          >
            <Square className="h-3.5 w-3.5 fill-current" />
            <span>STOP BOT</span>
          </button>

          {/* Emergency Stop Button */}
          <button
            onClick={onEmergencyStop}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-950/50 border border-rose-500 transition active:scale-95"
            title="Immediately cancel all open orders and flatten any active positions"
          >
            <AlertOctagon className="h-4 w-4" />
            <span>EMERGENCY STOP</span>
          </button>
        </div>
      </div>
    </div>
  );
};
