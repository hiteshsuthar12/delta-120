import React, { useState, useEffect } from 'react';
import { Sliders, Save, CheckCircle, RefreshCw, X } from 'lucide-react';
import type { StrategySettings } from '../types';

interface Props {
  settings: StrategySettings;
  isOpen: boolean;
  onClose: () => void;
  onSave: (updated: StrategySettings) => Promise<boolean>;
}

export const StrategySettingsCard: React.FC<Props> = ({
  settings,
  isOpen,
  onClose,
  onSave,
}) => {
  const [formData, setFormData] = useState<StrategySettings>(settings);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  if (!isOpen) return null;

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!formData.symbol.trim()) {
      errs.symbol = 'Trading symbol is required';
    }
    if (formData.ema_period < 5 || formData.ema_period > 500) {
      errs.ema_period = 'EMA period must be between 5 and 500';
    }
    if (formData.target_points <= 0) {
      errs.target_points = 'Target points must be greater than 0';
    }
    if (formData.stop_loss_points <= 0) {
      errs.stop_loss_points = 'Stop-loss points must be greater than 0';
    }
    if (formData.max_daily_trades < 1 || formData.max_daily_trades > 20) {
      errs.max_daily_trades = 'Max daily trades must be between 1 and 20';
    }
    if (formData.position_size_percentage <= 0 || formData.position_size_percentage > 100) {
      errs.position_size_percentage = 'Position sizing must be between 1% and 100%';
    }
    if (formData.leverage < 1 || formData.leverage > 100) {
      errs.leverage = 'Leverage must be between 1x and 100x';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    setSuccessMsg('');
    try {
      const ok = await onSave(formData);
      if (ok) {
        setSuccessMsg('Settings saved successfully to MongoDB!');
        setTimeout(() => {
          setSuccessMsg('');
          onClose();
        }, 1500);
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/40">
          <div className="flex items-center gap-2">
            <Sliders className="h-5 w-5 text-blue-400" />
            <h3 className="text-base font-bold text-white">Strategy & Risk Configuration</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-6 space-y-4">
          {successMsg && (
            <div className="p-3 bg-emerald-950/60 border border-emerald-800 rounded-lg text-emerald-400 text-xs flex items-center gap-2">
              <CheckCircle className="h-4 w-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            {/* Symbol */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Trading Symbol</label>
              <input
                type="text"
                value={formData.symbol}
                onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:border-blue-500 focus:outline-none"
                placeholder="BTCUSD"
              />
              {errors.symbol && <p className="text-rose-400 text-[11px] mt-1">{errors.symbol}</p>}
            </div>

            {/* Timeframe */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Candle Timeframe</label>
              <select
                value={formData.timeframe}
                onChange={(e) => setFormData({ ...formData, timeframe: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:border-blue-500 focus:outline-none"
              >
                <option value="1h">1 Hour (Recommended / Strategy Rule)</option>
                <option value="15m">15 Minutes</option>
                <option value="4h">4 Hours</option>
                <option value="1d">1 Day</option>
              </select>
            </div>

            {/* EMA Period */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">EMA Period</label>
              <input
                type="number"
                value={formData.ema_period}
                onChange={(e) => setFormData({ ...formData, ema_period: parseInt(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:border-blue-500 focus:outline-none"
              />
              {errors.ema_period && <p className="text-rose-400 text-[11px] mt-1">{errors.ema_period}</p>}
            </div>

            {/* Max Daily Trades */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Max Trades Per Day</label>
              <input
                type="number"
                value={formData.max_daily_trades}
                onChange={(e) => setFormData({ ...formData, max_daily_trades: parseInt(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:border-blue-500 focus:outline-none"
              />
              <span className="text-[10px] text-slate-500">Default: 2 trades max / day</span>
              {errors.max_daily_trades && (
                <p className="text-rose-400 text-[11px] mt-1">{errors.max_daily_trades}</p>
              )}
            </div>

            {/* Target Points */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Target Points (Take Profit)</label>
              <input
                type="number"
                step="10"
                value={formData.target_points}
                onChange={(e) => setFormData({ ...formData, target_points: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-emerald-400 font-mono font-bold focus:border-blue-500 focus:outline-none"
              />
              <span className="text-[10px] text-slate-500">Default: 1500 points</span>
              {errors.target_points && (
                <p className="text-rose-400 text-[11px] mt-1">{errors.target_points}</p>
              )}
            </div>

            {/* Stop Loss Points */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Stop-Loss Points</label>
              <input
                type="number"
                step="5"
                value={formData.stop_loss_points}
                onChange={(e) => setFormData({ ...formData, stop_loss_points: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-rose-400 font-mono font-bold focus:border-blue-500 focus:outline-none"
              />
              <span className="text-[10px] text-slate-500">Default: 100 points</span>
              {errors.stop_loss_points && (
                <p className="text-rose-400 text-[11px] mt-1">{errors.stop_loss_points}</p>
              )}
            </div>

            {/* Position Size % */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Position Sizing (% of Available)</label>
              <input
                type="number"
                min="1"
                max="100"
                value={formData.position_size_percentage}
                onChange={(e) =>
                  setFormData({ ...formData, position_size_percentage: parseFloat(e.target.value) || 0 })
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:border-blue-500 focus:outline-none"
              />
              <span className="text-[10px] text-slate-500">Default: 100% of available balance</span>
              {errors.position_size_percentage && (
                <p className="text-rose-400 text-[11px] mt-1">{errors.position_size_percentage}</p>
              )}
            </div>

            {/* Leverage */}
            <div>
              <label className="block text-slate-300 font-medium mb-1">Leverage Multiplier</label>
              <input
                type="number"
                min="1"
                max="100"
                value={formData.leverage}
                onChange={(e) => setFormData({ ...formData, leverage: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-amber-400 font-mono font-bold focus:border-blue-500 focus:outline-none"
              />
              <span className="text-[10px] text-slate-500">Strategy default: 25x</span>
              {errors.leverage && <p className="text-rose-400 text-[11px] mt-1">{errors.leverage}</p>}
            </div>

            {/* Timezone */}
            <div className="md:col-span-2">
              <label className="block text-slate-300 font-medium mb-1">Daily Reset Timezone</label>
              <select
                value={formData.daily_reset_timezone}
                onChange={(e) => setFormData({ ...formData, daily_reset_timezone: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:border-blue-500 focus:outline-none"
              >
                <option value="Asia/Kolkata">Asia/Kolkata (IST - Delta India Standard)</option>
                <option value="UTC">UTC (Universal Coordinated Time)</option>
                <option value="America/New_York">America/New_York (EST)</option>
                <option value="Europe/London">Europe/London (GMT)</option>
                <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
              </select>
            </div>
          </div>

          {/* Trade Direction Toggles */}
          <div className="border-t border-slate-800 pt-4 flex flex-wrap items-center justify-between gap-4 text-xs">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.allow_buy}
                onChange={(e) => setFormData({ ...formData, allow_buy: e.target.checked })}
                className="h-4 w-4 rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-0"
              />
              <span className="text-slate-300 font-medium">Enable BUY / Long Trades</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.allow_sell}
                onChange={(e) => setFormData({ ...formData, allow_sell: e.target.checked })}
                className="h-4 w-4 rounded bg-slate-950 border-slate-800 text-rose-500 focus:ring-0"
              />
              <span className="text-slate-300 font-medium">Enable SELL / Short Trades</span>
            </label>
          </div>

          {/* Footer Controls */}
          <div className="border-t border-slate-800 pt-4 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-md transition disabled:opacity-50"
            >
              {saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              <span>Save Settings to MongoDB</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
