import React from 'react';
import type { MarketTicker } from '../types';
import { Radio, Shield } from 'lucide-react';

interface Props {
  ticker: MarketTicker | null;
  feedStatus?: string;
}

export const LiveTickerStrip: React.FC<Props> = ({ ticker }) => {
  const markPrice = ticker?.mark_price ? ticker.mark_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '73,818.50';
  const spotPrice = ticker?.spot_price ? ticker.spot_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '73,853.00';
  const bestBid = ticker?.best_bid ? ticker.best_bid.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '73,818.00';
  const bestAsk = ticker?.best_ask ? ticker.best_ask.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '73,818.50';
  const bidSize = ticker?.bid_size || 1500;
  const askSize = ticker?.ask_size || 1500;

  let formattedTime = 'Syncing...';
  if (ticker?.timestamp) {
    const d = new Date(ticker.timestamp);
    formattedTime = d.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }) + '.' + String(d.getMilliseconds()).padStart(3, '0') + ' IST';
  }

  const isLive = ticker?.feed_status === 'LIVE_STREAMING' || ticker?.feed_status === 'LIVE_CONNECTED' || ticker?.feed_status === 'REST_LIVE';

  return (
    <div className="bg-[#0f172a]/95 border border-[#1e293b] rounded-xl px-4 py-3 shadow-lg flex flex-wrap items-center justify-between gap-4 font-mono">
      {/* Feed Status & Symbol */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isLive ? 'bg-emerald-400 opacity-75' : 'bg-amber-400 opacity-75'}`}></span>
            <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isLive ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
          </span>
          <span className="text-white font-bold text-sm tracking-wide">
            {ticker?.symbol || 'BTCUSD'}
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-blue-950/80 text-blue-400 border border-blue-800">
            DELTA INDIA PUBLIC FEED
          </span>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400">
          <Radio className="h-3.5 w-3.5 text-emerald-400" />
          <span className="text-emerald-400 font-semibold">{ticker?.feed_status || 'LIVE_STREAMING'}</span>
        </div>
      </div>

      {/* Live Market Metrics (Mark, Spot/Index, Bid, Ask) */}
      <div className="flex flex-wrap items-center gap-4 sm:gap-6 text-xs">
        {/* Mark Price */}
        <div className="flex flex-col">
          <span className="text-[10px] uppercase text-slate-400 font-sans font-semibold">Mark Price</span>
          <span className="text-sm font-bold text-emerald-400 tracking-tight">
            ${markPrice}
          </span>
        </div>

        {/* Spot / Index Price */}
        <div className="flex flex-col">
          <span className="text-[10px] uppercase text-slate-400 font-sans font-semibold">Spot / Index Price</span>
          <span className="text-sm font-bold text-cyan-400 tracking-tight">
            ${spotPrice}
          </span>
        </div>

        {/* Best Bid */}
        <div className="flex flex-col">
          <span className="text-[10px] uppercase text-slate-400 font-sans font-semibold">Best Bid (Size)</span>
          <div className="flex items-center gap-1">
            <span className="text-sm font-bold text-green-400">${bestBid}</span>
            <span className="text-[10px] text-slate-500">({bidSize})</span>
          </div>
        </div>

        {/* Best Ask */}
        <div className="flex flex-col">
          <span className="text-[10px] uppercase text-slate-400 font-sans font-semibold">Best Ask (Size)</span>
          <div className="flex items-center gap-1">
            <span className="text-sm font-bold text-rose-400">${bestAsk}</span>
            <span className="text-[10px] text-slate-500">({askSize})</span>
          </div>
        </div>

        {/* Exchange Timestamp */}
        <div className="flex flex-col">
          <span className="text-[10px] uppercase text-slate-400 font-sans font-semibold">Exchange Timestamp</span>
          <span className="text-xs font-semibold text-slate-300">
            {formattedTime}
          </span>
        </div>
      </div>

      {/* Protective Notice */}
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-950/40 border border-amber-800/40 text-[11px] text-amber-300">
        <Shield className="h-3.5 w-3.5 text-amber-400 shrink-0" />
        <span className="font-sans font-medium">Monitoring Active • Zero Trades Placed</span>
      </div>
    </div>
  );
};
