export interface AccountOverview {
  total_balance: number;
  available_balance: number;
  used_margin: number;
  today_realized_pnl: number;
  today_unrealized_pnl: number;
  today_trades_count: number;
  winning_trades: number;
  losing_trades: number;
}

export interface BotPosition {
  trade_id: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  entry_price: number;
  current_price: number;
  target_price: number;
  stop_loss_price: number;
  quantity: number;
  unrealized_pnl: number;
  status: string;
  mode: 'PAPER' | 'LIVE';
  entry_time: string;
}

export interface SignalInfo {
  symbol: string;
  direction: 'BUY' | 'SELL' | 'HOLD';
  candle_time: string;
  close_price: number;
  previous_close_price: number;
  ema_value: number;
  is_confirmed: boolean;
  reason?: string;
  generated_at: string;
}

export interface BotState {
  bot_status: 'RUNNING' | 'STOPPED' | 'EMERGENCY_STOPPED';
  trading_mode: 'PAPER' | 'LIVE';
  state_machine_stage: string;
  exchange_connected: boolean;
  current_position: BotPosition | null;
  daily_trade_count: number;
  trading_day: string;
  last_processed_candle?: string;
  last_signal: SignalInfo | null;
  timestamp: string;
}

export interface StrategySettings {
  _id?: string;
  symbol: string;
  timeframe: string;
  ema_period: number;
  target_points: number;
  stop_loss_points: number;
  max_daily_trades: number;
  position_size_percentage: number;
  leverage: number;
  daily_reset_timezone: string;
  allow_buy: boolean;
  allow_sell: boolean;
  trading_enabled: boolean;
  updated_at?: string;
}

export interface Trade {
  _id: string;
  symbol: string;
  direction: 'BUY' | 'SELL';
  entry_price: number;
  exit_price?: number;
  quantity: number;
  target_price: number;
  stop_loss_price: number;
  entry_time: string;
  exit_time?: string;
  realized_pnl?: number;
  status: 'OPEN' | 'CLOSED' | 'CANCELLED';
  exchange_order_ids?: string[];
  exit_reason?: 'TARGET' | 'STOP_LOSS' | 'MANUAL' | 'EMERGENCY' | string;
  trading_day: string;
  mode: 'PAPER' | 'LIVE';
}

export interface ActivityLog {
  _id: string;
  timestamp: string;
  event_type: string;
  message: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS' | 'CRITICAL';
  metadata?: Record<string, any>;
}

export interface MarketTicker {
  symbol: string;
  mark_price: number;
  spot_price: number;
  best_bid: number;
  best_ask: number;
  bid_size: number;
  ask_size: number;
  ltp: number;
  timestamp: number;
  timestamp_iso: string;
  feed_status: string;
}

export interface DashboardData {
  account: AccountOverview;
  bot_status: 'RUNNING' | 'STOPPED' | 'EMERGENCY_STOPPED';
  trading_mode: 'PAPER' | 'LIVE';
  state_machine_stage: string;
  exchange_connected: boolean;
  current_position: BotPosition | null;
  daily_trade_count: number;
  trading_day: string;
  last_signal: SignalInfo | null;
  strategy_settings: StrategySettings;
  recent_trades: Trade[];
  recent_logs: ActivityLog[];
  live_ticker?: MarketTicker;
  server_time: string;
}

