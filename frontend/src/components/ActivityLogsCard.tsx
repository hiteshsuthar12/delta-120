import React from 'react';
import { Terminal } from 'lucide-react';
import type { ActivityLog } from '../types';

interface Props {
  logs: ActivityLog[];
}

export const ActivityLogsCard: React.FC<Props> = ({ logs }) => {
  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'SUCCESS':
        return (
          <span className="px-1.5 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800 text-[10px] font-bold">
            SUCCESS
          </span>
        );
      case 'WARNING':
        return (
          <span className="px-1.5 py-0.5 rounded bg-amber-950/80 text-amber-400 border border-amber-800 text-[10px] font-bold">
            WARNING
          </span>
        );
      case 'ERROR':
        return (
          <span className="px-1.5 py-0.5 rounded bg-rose-950/80 text-rose-400 border border-rose-800 text-[10px] font-bold">
            ERROR
          </span>
        );
      case 'CRITICAL':
        return (
          <span className="px-1.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-600 text-[10px] font-bold animate-pulse">
            CRITICAL
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.5 rounded bg-blue-950/80 text-blue-400 border border-blue-800 text-[10px] font-bold">
            INFO
          </span>
        );
    }
  };

  const formatLogTime = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md flex flex-col">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-emerald-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Live Activity & Safety Events</h3>
        </div>
        <span className="text-[11px] font-mono text-slate-500">Real-time WebSocket Feed</span>
      </div>

      <div className="overflow-y-auto max-h-[280px] space-y-2 pr-1 font-mono text-xs">
        {logs.length === 0 ? (
          <div className="text-center py-8 text-slate-500 font-sans">
            No activity logged yet. Bot events will stream here in real time.
          </div>
        ) : (
          logs.map((log) => (
            <div
              key={log._id}
              className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-slate-700/80 transition flex items-start justify-between gap-3"
            >
              <div className="flex items-start gap-2.5">
                <span className="text-[11px] text-slate-500 shrink-0 mt-0.5">
                  {formatLogTime(log.timestamp)}
                </span>
                <div>
                  <div className="text-slate-200 text-xs leading-relaxed">{log.message}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Event: {log.event_type}</div>
                </div>
              </div>
              <div className="shrink-0">{getSeverityBadge(log.severity)}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
