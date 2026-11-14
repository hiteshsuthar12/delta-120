import React, { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  leverage: number;
  positionSizePct: number;
}

export const LiveConfirmationModal: React.FC<Props> = ({
  isOpen,
  onClose,
  onConfirm,
  leverage,
  positionSizePct,
}) => {
  const [hasAcknowledgedRisk, setHasAcknowledgedRisk] = useState(false);
  const [hasConfirmedCapital, setHasConfirmedCapital] = useState(false);

  if (!isOpen) return null;

  const canProceed = hasAcknowledgedRisk && hasConfirmedCapital;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-rose-800/80 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-rose-950/50 border-b border-rose-900/50">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-rose-600/30 border border-rose-500 flex items-center justify-center text-rose-400">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-rose-200">Enable LIVE Trading Confirmation</h3>
              <p className="text-[11px] text-rose-400">Real Money Execution on Delta Exchange</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 text-xs text-slate-300 leading-relaxed">
          <p className="text-slate-200">
            You are about to switch the automated EMA 120 trading bot to <span className="text-rose-400 font-bold">LIVE TRADING MODE</span>. Real orders will be submitted to Delta Exchange whenever strategy signals trigger.
          </p>

          {/* Critical Risk Parameters Card */}
          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2 font-mono">
            <div className="text-[11px] text-slate-400 font-sans font-bold uppercase tracking-wider mb-1">
              Active Strategy Parameters:
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Position Sizing:</span>
              <span className="font-bold text-amber-400">{positionSizePct}% of Available Balance</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Configured Leverage:</span>
              <span className="font-bold text-amber-400">{leverage}x Multiplier</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Protective Stop-Loss:</span>
              <span className="font-bold text-rose-400">100 Points (Enforced via exchange)</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span>Protective Take-Profit:</span>
              <span className="font-bold text-emerald-400">1500 Points (Reduce-only limit)</span>
            </div>
          </div>

          {/* Acknowledgments */}
          <div className="space-y-3 pt-2">
            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={hasAcknowledgedRisk}
                onChange={(e) => setHasAcknowledgedRisk(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded bg-slate-950 border-slate-700 text-rose-500 focus:ring-0"
              />
              <span className="text-slate-300">
                I understand that cryptocurrency futures involve high market volatility and leverage carries risk of liquidation.
              </span>
            </label>

            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={hasConfirmedCapital}
                onChange={(e) => setHasConfirmedCapital(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded bg-slate-950 border-slate-700 text-rose-500 focus:ring-0"
              />
              <span className="text-slate-300">
                I confirm that my Delta Exchange API credentials are authenticated and I authorize live orders.
              </span>
            </label>
          </div>

          {/* Footer Controls */}
          <div className="border-t border-slate-800 pt-4 flex items-center justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            >
              Cancel (Stay on Paper)
            </button>
            <button
              onClick={() => {
                onConfirm();
                onClose();
              }}
              disabled={!canProceed}
              className="px-5 py-2 rounded-lg text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-950 transition disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Confirm & Activate Live Mode
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
