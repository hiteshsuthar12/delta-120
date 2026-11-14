import React, { useState } from 'react';
import { KeyRound, CheckCircle, AlertCircle, RefreshCw, X, Lock } from 'lucide-react';
import { connectExchange, testExchangeConnection } from '../api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConnectionSuccess: () => void;
}

export const ApiSettingsModal: React.FC<Props> = ({ isOpen, onClose, onConnectionSuccess }) => {
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [environment, setEnvironment] = useState('india');
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ text: string; isError: boolean } | null>(null);

  if (!isOpen) return null;

  const handleTestConnection = async () => {
    setIsTesting(true);
    setStatusMessage(null);
    try {
      const res = await testExchangeConnection();
      if (res.success) {
        setStatusMessage({ text: res.message || 'Delta Exchange connection verified successfully!', isError: false });
      } else {
        setStatusMessage({ text: res.message || 'Failed to connect with configured credentials.', isError: true });
      }
    } catch (e: any) {
      setStatusMessage({ text: e.response?.data?.detail || e.message || 'Connection test error', isError: true });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim() || !apiSecret.trim()) {
      setStatusMessage({ text: 'Please enter both Delta Exchange API Key and Secret.', isError: true });
      return;
    }

    setIsSaving(true);
    setStatusMessage(null);
    try {
      const res = await connectExchange({
        api_key: apiKey.trim(),
        api_secret: apiSecret.trim(),
        environment,
      });

      if (res.success) {
        setStatusMessage({
          text: `Credentials encrypted and saved! Mode: ${environment.toUpperCase()}`,
          isError: false,
        });
        // Clear secrets from component state immediately for security
        setApiKey('');
        setApiSecret('');
        onConnectionSuccess();
        setTimeout(() => {
          onClose();
        }, 1500);
      }
    } catch (e: any) {
      setStatusMessage({ text: e.response?.data?.detail || 'Failed to save credentials.', isError: true });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <KeyRound className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Delta Exchange API Settings</h3>
              <p className="text-[11px] text-slate-400">Encrypted server-side with AES-256 Fernet</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Security Banner */}
        <div className="px-6 py-3 bg-blue-950/30 border-b border-blue-900/30 flex items-center gap-2 text-xs text-blue-300">
          <Lock className="h-3.5 w-3.5 shrink-0 text-blue-400" />
          <span>Never exposed in browser storage or client responses. Encrypted in MongoDB.</span>
        </div>

        <form onSubmit={handleSave} className="p-6 space-y-4">
          {statusMessage && (
            <div
              className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                statusMessage.isError
                  ? 'bg-rose-950/60 border border-rose-800 text-rose-300'
                  : 'bg-emerald-950/60 border border-emerald-800 text-emerald-300'
              }`}
            >
              {statusMessage.isError ? (
                <AlertCircle className="h-4 w-4 shrink-0" />
              ) : (
                <CheckCircle className="h-4 w-4 shrink-0" />
              )}
              <span>{statusMessage.text}</span>
            </div>
          )}

          {/* Environment */}
          <div>
            <label className="block text-xs text-slate-300 font-medium mb-1">Delta Exchange Environment</label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono text-xs focus:border-blue-500 focus:outline-none"
            >
              <option value="india">Delta Exchange India (api.india.delta.exchange)</option>
              <option value="global">Delta Exchange Global (api.delta.exchange)</option>
              <option value="testnet">Delta Global Testnet (testnet-api.delta.exchange)</option>
            </select>
          </div>

          {/* API Key */}
          <div>
            <label className="block text-xs text-slate-300 font-medium mb-1">Delta API Key</label>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your Delta API Key"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono text-xs focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* API Secret */}
          <div>
            <label className="block text-xs text-slate-300 font-medium mb-1">Delta API Secret</label>
            <input
              type="password"
              value={apiSecret}
              onChange={(e) => setApiSecret(e.target.value)}
              placeholder="Enter your Delta API Secret"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono text-xs focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Footer Controls */}
          <div className="border-t border-slate-800 pt-4 flex flex-wrap items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={isTesting}
              className="px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition"
            >
              {isTesting && <RefreshCw className="h-3 w-3 animate-spin" />}
              <span>Test Existing Connection</span>
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSaving}
                className="px-4 py-2 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-md transition disabled:opacity-50"
              >
                {isSaving ? 'Encrypting & Saving...' : 'Save Credentials'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
