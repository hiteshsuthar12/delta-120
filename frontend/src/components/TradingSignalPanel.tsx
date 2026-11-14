import React from 'react';
import { Radio, ArrowUpCircle, ArrowDownCircle, MinusCircle, Clock, Zap } from 'lucide-react';
import type { SignalInfo } from '../types';

interface Props {
  lastSignal: SignalInfo | null;
  currentEma?: number;
  currentPrice?: number;
}

export const TradingSignalPanel: React.FC<Props> = ({ lastSignal, currentEma, currentPrice }) => {
  const signal = lastSignal?.direction || 'HOLD';
  const isBuy = signal === 'BUY';
  const isSell = signal === 'SELL';

  const formatSignalTime = (dateStr?: string) => {
    if (!dateStr) return 'Awaiting initial candle close';
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Radio className="h-4 w-4 text-indigo-400 animate-pulse" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Trading Signal Engine</h3>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-400 border border-indigo-800/80 font-mono">
            1H Candle • EMA 120
          </span>
        </div>

        {/* Signal Big Status Card */}
        <div
          className={`p-4 rounded-xl border flex items-center justify-between mb-4 ${
            isBuy
              ? 'bg-emerald-950/40 border-emerald-800/80'
              : isSell
              ? 'bg-rose-950/40 border-rose-800/80'
              : 'bg-slate-950 border-slate-800'
          }`}
        >
          <div className="flex items-center gap-3">
            {isBuy && <ArrowUpCircle className="h-8 w-8 text-emerald-400" />}
            {isSell && <ArrowDownCircle className="h-8 w-8 text-rose-400" />}
            {!isBuy && !isSell && <MinusCircle className="h-8 w-8 text-slate-500" />}
            <div>
              <div className="text-[10px] text-slate-400 uppercase tracking-widest">Latest Valid Signal</div>
              <div
                className={`text-2xl font-black font-mono tracking-tight ${
                  isBuy ? 'text-emerald-400' : isSell ? 'text-rose-400' : 'text-slate-300'
                }`}
              >
                {signal}
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-[10px] text-slate-400 uppercase">Confirmation</div>
            <div className="text-xs font-semibold text-emerald-400 flex items-center gap-1 justify-end mt-0.5">
              <Zap className="h-3 w-3 fill-emerald-400" />
              <span>CANDLE CLOSED</span>
            </div>
          </div>
        </div>

        {/* Detailed Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 text-xs font-mono">
          <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[11px]">EMA 120 Value</div>
            <div className="text-amber-400 font-bold text-sm mt-0.5">
              ${(lastSignal?.ema_value || currentEma || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>

          <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[11px]">Latest Closed Candle</div>
            <div className="text-white font-bold text-sm mt-0.5">
              ${(lastSignal?.close_price || currentPrice || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>

          <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[11px]">Previous Closed Candle</div>
            <div className="text-slate-300 font-bold text-sm mt-0.5">
              ${(lastSignal?.previous_close_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>

          <div className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[11px]">Strategy Rule Check</div>
            <div className="text-[11px] text-slate-300 font-semibold mt-1 truncate" title={lastSignal?.reason || 'Scanning...'}>
              {lastSignal?.reason ? lastSignal.reason.substring(0, 24) + '...' : 'Evaluating 1h close'}
            </div>
          </div>
        </div>
      </div>

      {/* Footer Timestamp */}
      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-3 mt-4 border-t border-slate-800">
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          <span>Last Signal Time:</span>
        </span>
        <span className="text-slate-400 font-mono">{formatSignalTime(lastSignal?.generated_at)}</span>
      </div>
    </div>
  );
};
