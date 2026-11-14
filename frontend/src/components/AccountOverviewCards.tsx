import React from 'react';
import { Wallet, DollarSign, TrendingUp, TrendingDown, Layers, PieChart, ShieldAlert } from 'lucide-react';
import type { AccountOverview } from '../types';

interface Props {
  account: AccountOverview;
  maxDailyTrades: number;
}

export const AccountOverviewCards: React.FC<Props> = ({ account, maxDailyTrades = 2 }) => {
  const isRealizedProfitable = account.today_realized_pnl >= 0;
  const isUnrealizedProfitable = account.today_unrealized_pnl >= 0;
  const isLimitReached = account.today_trades_count >= maxDailyTrades;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
      {/* 1. Total Balance */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Total Balance</span>
          <Wallet className="h-4 w-4 text-blue-400" />
        </div>
        <div>
          <div className="text-lg font-bold text-white font-mono">
            ${account.total_balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[10px] text-slate-500">USDT / USD</span>
        </div>
      </div>

      {/* 2. Available Balance */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Available</span>
          <DollarSign className="h-4 w-4 text-emerald-400" />
        </div>
        <div>
          <div className="text-lg font-bold text-white font-mono">
            ${account.available_balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[10px] text-emerald-500">Ready to trade</span>
        </div>
      </div>

      {/* 3. Used Margin */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Used Margin</span>
          <Layers className="h-4 w-4 text-amber-400" />
        </div>
        <div>
          <div className="text-lg font-bold text-white font-mono">
            ${account.used_margin.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <span className="text-[10px] text-slate-500">Active exposure</span>
        </div>
      </div>

      {/* 4. Realized P&L */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Today's Realized</span>
          {isRealizedProfitable ? (
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          ) : (
            <TrendingDown className="h-4 w-4 text-rose-400" />
          )}
        </div>
        <div>
          <div
            className={`text-lg font-bold font-mono ${
              isRealizedProfitable ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isRealizedProfitable ? '+' : ''}${account.today_realized_pnl.toFixed(2)}
          </div>
          <span className="text-[10px] text-slate-500">Settled trades</span>
        </div>
      </div>

      {/* 5. Unrealized P&L */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Today's Unrealized</span>
          {isUnrealizedProfitable ? (
            <TrendingUp className="h-4 w-4 text-emerald-400" />
          ) : (
            <TrendingDown className="h-4 w-4 text-rose-400" />
          )}
        </div>
        <div>
          <div
            className={`text-lg font-bold font-mono ${
              isUnrealizedProfitable ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isUnrealizedProfitable ? '+' : ''}${account.today_unrealized_pnl.toFixed(2)}
          </div>
          <span className="text-[10px] text-slate-500">Live mark</span>
        </div>
      </div>

      {/* 6. Today's Trades (Daily limit indicator) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Today's Trades</span>
          {isLimitReached ? (
            <ShieldAlert className="h-4 w-4 text-amber-400" />
          ) : (
            <PieChart className="h-4 w-4 text-indigo-400" />
          )}
        </div>
        <div>
          <div className="text-lg font-bold text-white font-mono flex items-baseline gap-1">
            <span>{account.today_trades_count}</span>
            <span className="text-xs text-slate-500">/ {maxDailyTrades} max</span>
          </div>
          <span className={`text-[10px] ${isLimitReached ? 'text-amber-400 font-semibold' : 'text-slate-500'}`}>
            {isLimitReached ? 'Daily limit hit' : 'Limit active'}
          </span>
        </div>
      </div>

      {/* 7. Winning Trades */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Wins</span>
          <TrendingUp className="h-4 w-4 text-emerald-400" />
        </div>
        <div>
          <div className="text-lg font-bold text-emerald-400 font-mono">
            {account.winning_trades}
          </div>
          <span className="text-[10px] text-slate-500">
            {account.today_trades_count > 0
              ? `${Math.round((account.winning_trades / account.today_trades_count) * 100)}% Win Rate`
              : '0% Win Rate'}
          </span>
        </div>
      </div>

      {/* 8. Losing Trades */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex flex-col justify-between shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-1">
          <span className="text-[11px] font-medium uppercase tracking-wider">Losses</span>
          <TrendingDown className="h-4 w-4 text-rose-400" />
        </div>
        <div>
          <div className="text-lg font-bold text-rose-400 font-mono">
            {account.losing_trades}
          </div>
          <span className="text-[10px] text-slate-500">Stops hit</span>
        </div>
      </div>
    </div>
  );
};
