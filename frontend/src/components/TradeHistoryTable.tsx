import React, { useState, useMemo } from 'react';
import { History, ArrowUpRight, ArrowDownRight, Search } from 'lucide-react';
import type { Trade } from '../types';

interface Props {
  trades: Trade[];
}

export const TradeHistoryTable: React.FC<Props> = ({ trades }) => {
  const [directionFilter, setDirectionFilter] = useState<'ALL' | 'BUY' | 'SELL'>('ALL');
  const [symbolFilter, setSymbolFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');

  const filteredTrades = useMemo(() => {
    return trades.filter((t) => {
      if (directionFilter !== 'ALL' && t.direction !== directionFilter) {
        return false;
      }
      if (symbolFilter.trim() && !t.symbol.toLowerCase().includes(symbolFilter.toLowerCase().trim())) {
        return false;
      }
      if (dateFilter && t.trading_day !== dateFilter) {
        return false;
      }
      return true;
    });
  }, [trades, directionFilter, symbolFilter, dateFilter]);

  const formatDate = (isoStr: string) => {
    if (!isoStr) return '--';
    try {
      const d = new Date(isoStr);
      return d.toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md flex flex-col">
      {/* Title & Filter Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-slate-800 pb-4 mb-4">
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-blue-400" />
          <h3 className="text-base font-bold text-white tracking-wide">Trade History & Audit Trail</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
            {filteredTrades.length} trades
          </span>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2.5 text-xs">
          {/* Direction Filter */}
          <div className="flex items-center bg-slate-950 rounded-lg p-0.5 border border-slate-800">
            <button
              onClick={() => setDirectionFilter('ALL')}
              className={`px-2.5 py-1 rounded font-medium transition ${
                directionFilter === 'ALL' ? 'bg-slate-800 text-white' : 'text-slate-400'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setDirectionFilter('BUY')}
              className={`px-2.5 py-1 rounded font-medium transition ${
                directionFilter === 'BUY' ? 'bg-emerald-950 text-emerald-400 font-bold' : 'text-slate-400'
              }`}
            >
              BUY
            </button>
            <button
              onClick={() => setDirectionFilter('SELL')}
              className={`px-2.5 py-1 rounded font-medium transition ${
                directionFilter === 'SELL' ? 'bg-rose-950 text-rose-400 font-bold' : 'text-slate-400'
              }`}
            >
              SELL
            </button>
          </div>

          {/* Symbol Filter */}
          <div className="relative">
            <Search className="h-3.5 w-3.5 text-slate-500 absolute left-2.5 top-2" />
            <input
              type="text"
              placeholder="Filter symbol..."
              value={symbolFilter}
              onChange={(e) => setSymbolFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-2.5 py-1 text-white font-mono placeholder:text-slate-600 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Date Filter */}
          <div className="relative">
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-white font-mono text-xs focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Reset Filters */}
          {(directionFilter !== 'ALL' || symbolFilter || dateFilter) && (
            <button
              onClick={() => {
                setDirectionFilter('ALL');
                setSymbolFilter('');
                setDateFilter('');
              }}
              className="text-slate-400 hover:text-white underline text-[11px]"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto max-h-[380px] overflow-y-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-950/80 sticky top-0 text-[11px] text-slate-400 uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Trade ID</th>
              <th className="py-2.5 px-3">Date / Time</th>
              <th className="py-2.5 px-3">Symbol</th>
              <th className="py-2.5 px-3">Side</th>
              <th className="py-2.5 px-3">Entry</th>
              <th className="py-2.5 px-3">Exit</th>
              <th className="py-2.5 px-3">Qty</th>
              <th className="py-2.5 px-3">TP Target</th>
              <th className="py-2.5 px-3">SL</th>
              <th className="py-2.5 px-3">P&L</th>
              <th className="py-2.5 px-3">Exit Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredTrades.length === 0 ? (
              <tr>
                <td colSpan={11} className="py-8 text-center text-slate-500 font-sans">
                  No trade records found matching criteria.
                </td>
              </tr>
            ) : (
              filteredTrades.map((t) => {
                const isBuy = t.direction === 'BUY';
                const pnl = t.realized_pnl || 0;
                const isWin = pnl > 0;
                const isLoss = pnl < 0;

                return (
                  <tr key={t._id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 text-slate-400">{t._id.substring(0, 8)}...</td>
                    <td className="py-2.5 px-3 text-slate-300">{formatDate(t.entry_time)}</td>
                    <td className="py-2.5 px-3 font-bold text-white">{t.symbol}</td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded text-[10px] font-bold ${
                          isBuy
                            ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/80'
                            : 'bg-rose-950/80 text-rose-400 border border-rose-800/80'
                        }`}
                      >
                        {isBuy ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                        {t.direction}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-200">${t.entry_price.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-slate-200">
                      {t.exit_price ? `$${t.exit_price.toLocaleString()}` : <span className="text-amber-400 animate-pulse">OPEN</span>}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{t.quantity}</td>
                    <td className="py-2.5 px-3 text-emerald-400/90">${t.target_price.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-rose-400/90">${t.stop_loss_price.toLocaleString()}</td>
                    <td className="py-2.5 px-3">
                      {t.status === 'CLOSED' ? (
                        <span
                          className={`font-bold ${
                            isWin ? 'text-emerald-400' : isLoss ? 'text-rose-400' : 'text-slate-400'
                          }`}
                        >
                          {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-slate-500">--</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3">
                      {t.exit_reason ? (
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                            t.exit_reason === 'TARGET'
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-900'
                              : t.exit_reason === 'STOP_LOSS'
                              ? 'bg-rose-950 text-rose-400 border border-rose-900'
                              : 'bg-slate-800 text-slate-300'
                          }`}
                        >
                          {t.exit_reason}
                        </span>
                      ) : (
                        <span className="text-[10px] text-slate-500">HOLDING</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
