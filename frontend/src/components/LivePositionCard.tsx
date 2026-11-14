import React from 'react';
import { Crosshair, ArrowUpRight, ArrowDownRight, Target, ShieldAlert, CheckCircle } from 'lucide-react';
import type { BotPosition } from '../types';

interface Props {
  position: BotPosition | null;
  currentMarketPrice: number;
}

export const LivePositionCard: React.FC<Props> = ({ position, currentMarketPrice }) => {
  if (!position) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col items-center justify-center text-center min-h-[220px]">
        <div className="h-12 w-12 rounded-full bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-500 mb-3">
          <Crosshair className="h-6 w-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-300">No Open Position</h4>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Strict One Open Position Rule is active. The bot is actively scanning 1h candles for an EMA 120 crossover.
        </p>
        <div className="mt-3 text-[11px] font-mono text-emerald-400 bg-emerald-950/40 px-3 py-1 rounded-full border border-emerald-900/60 flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
          <span>Capital Safe • Ready for Valid Signal</span>
        </div>
      </div>
    );
  }

  const isBuy = position.direction === 'BUY';
  const isProfitable = position.unrealized_pnl >= 0;

  // Price distance calculations
  const tpDistance = Math.abs(position.target_price - currentMarketPrice);
  const slDistance = Math.abs(currentMarketPrice - position.stop_loss_price);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md relative overflow-hidden">
      {/* Top Banner */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <span
            className={`px-2.5 py-1 rounded text-xs font-bold tracking-wide flex items-center gap-1 ${
              isBuy
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                : 'bg-rose-950 text-rose-400 border border-rose-800'
            }`}
          >
            {isBuy ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
            {isBuy ? 'LONG (BUY)' : 'SHORT (SELL)'}
          </span>
          <span className="text-base font-bold text-white font-mono">{position.symbol}</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 uppercase font-mono">
            {position.mode}
          </span>
        </div>

        {/* Live Unrealized P&L Badge */}
        <div className="text-right">
          <div
            className={`text-xl font-extrabold font-mono ${
              isProfitable ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isProfitable ? '+' : ''}${position.unrealized_pnl.toFixed(2)}
          </div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wider">Unrealized P&L</div>
        </div>
      </div>

      {/* Grid of Position Details */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
        {/* Entry Price */}
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
          <div className="text-slate-400 text-[11px] mb-1">Entry Price</div>
          <div className="text-white text-sm font-bold">${position.entry_price.toLocaleString()}</div>
        </div>

        {/* Current Market Price */}
        <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
          <div className="text-slate-400 text-[11px] mb-1">Market Price</div>
          <div className="text-blue-400 text-sm font-bold animate-pulse">
            ${currentMarketPrice.toLocaleString()}
          </div>
        </div>

        {/* Take-Profit Target */}
        <div className="bg-emerald-950/30 p-2.5 rounded-lg border border-emerald-900/50">
          <div className="text-emerald-400 text-[11px] flex items-center gap-1 mb-1">
            <Target className="h-3 w-3" />
            <span>Target (+1500)</span>
          </div>
          <div className="text-emerald-300 text-sm font-bold">${position.target_price.toLocaleString()}</div>
          <div className="text-[10px] text-emerald-500/80 mt-0.5">{tpDistance.toFixed(1)} pts to TP</div>
        </div>

        {/* Stop Loss */}
        <div className="bg-rose-950/30 p-2.5 rounded-lg border border-rose-900/50">
          <div className="text-rose-400 text-[11px] flex items-center gap-1 mb-1">
            <ShieldAlert className="h-3 w-3" />
            <span>Stop Loss (-100)</span>
          </div>
          <div className="text-rose-300 text-sm font-bold">${position.stop_loss_price.toLocaleString()}</div>
          <div className="text-[10px] text-rose-500/80 mt-0.5">{slDistance.toFixed(1)} pts to SL</div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-500 mt-4 pt-3 border-t border-slate-800/80">
        <div>Contracts / Qty: <span className="text-slate-300 font-mono font-semibold">{position.quantity}</span></div>
        <div>Trade ID: <span className="font-mono text-slate-400">{position.trade_id.substring(0, 8)}...</span></div>
        <div className="flex items-center gap-1 text-emerald-400 font-medium">
          <CheckCircle className="h-3 w-3" />
          <span>Active Protective Orders In Place</span>
        </div>
      </div>
    </div>
  );
};
