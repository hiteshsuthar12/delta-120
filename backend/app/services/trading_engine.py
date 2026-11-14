import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.database import db_manager
from app.services.delta_exchange import delta_client
from app.services.market_data import market_data_service
from app.services.ema_strategy import ema_strategy_engine, StrategySignal
from app.services.risk_manager import risk_manager
from app.services.order_manager import order_manager
from app.services.position_manager import position_manager
from app.services.reconciliation import reconciliation_service
from app.services.websocket_manager import websocket_manager
from app.utils.datetime_utils import get_current_trading_day

logger = logging.getLogger(__name__)

class TradingEngine:
    """
    Autonomous EMA 120 Trading Engine.
    Executes trades independently of the frontend, maintaining a persistent state machine
    in MongoDB and Delta Exchange.
    """
    def __init__(self):
        self.is_running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._reconcile_counter: int = 0
        self._simulated_balance: float = 10000.0  # Default paper trading initial balance

    async def start(self, mode: str = "PAPER", live_confirmation: bool = False) -> Dict[str, Any]:
        """Start trading bot in paper or live mode."""
        if mode.upper() == "LIVE" and not live_confirmation:
            raise ValueError("Live trading requires explicit confirmation before activation.")

        # Update bot state in DB
        await db_manager.update_bot_state_fields({
            "bot_status": "RUNNING",
            "trading_mode": mode.upper(),
            "state_machine_stage": "IDLE" if not (await db_manager.get_bot_state()).get("current_position") else "POSITION_OPEN"
        })
        self.is_running = True

        await db_manager.add_log(
            event_type="BOT_STARTED",
            message=f"EMA 120 Trading Bot started in {mode.upper()} mode.",
            severity="INFO",
            metadata={"mode": mode.upper()}
        )

        logger.info(f"Bot started successfully in {mode.upper()} mode.")
        return {"status": "RUNNING", "mode": mode.upper()}

    async def stop(self) -> Dict[str, Any]:
        """Gracefully stop automated signal processing without closing open positions."""
        await db_manager.update_bot_state_fields({
            "bot_status": "STOPPED"
        })
        self.is_running = False

        await db_manager.add_log(
            event_type="BOT_STOPPED",
            message="EMA 120 Trading Bot stopped by user.",
            severity="WARNING"
        )
        logger.info("Bot stopped successfully.")
        return {"status": "STOPPED"}

    async def emergency_stop(self) -> Dict[str, Any]:
        """
        EMERGENCY STOP:
        Immediately disables automated trading, cancels all open/conditional orders,
        and executes market exit on any open position.
        """
        logger.critical("EMERGENCY STOP initiated!")
        # 1. Disable bot immediately
        await db_manager.update_bot_state_fields({
            "bot_status": "EMERGENCY_STOPPED",
            "state_machine_stage": "EMERGENCY_EXIT"
        })
        self.is_running = False

        bot_state = await db_manager.get_bot_state()
        pos = bot_state.get("current_position") if bot_state else None
        
        # 2. Flatten position if open
        if pos:
            trade_id = pos.get("trade_id")
            symbol = pos.get("symbol", "BTCUSD")
            direction = pos.get("direction", "BUY")
            quantity = float(pos.get("quantity", 0))
            entry_price = float(pos.get("entry_price", 0))
            current_price = await market_data_service.get_current_price(symbol)
            mode = pos.get("mode", "PAPER")

            await order_manager.execute_exit_order(
                trade_id=trade_id,
                symbol=symbol,
                direction=direction,
                quantity=quantity,
                entry_price=entry_price,
                exit_price=current_price,
                exit_reason="EMERGENCY",
                mode=mode
            )

        # 3. Cancel any pending orders on live exchange
        try:
            await delta_client.cancel_all_orders()
        except Exception as e:
            logger.error(f"Error cancelling orders during emergency stop: {e}")

        # 4. Release state lock
        await db_manager.atomic_release_position_lock()

        await db_manager.add_log(
            event_type="EMERGENCY_STOP",
            message="CRITICAL: Emergency stop executed. All orders cancelled and positions closed.",
            severity="CRITICAL"
        )

        return {"status": "EMERGENCY_STOPPED", "message": "Emergency exit completed"}

    async def get_account_overview(self) -> Dict[str, Any]:
        """Fetch unified account overview."""
        bot_state = await db_manager.get_bot_state()
        mode = bot_state.get("trading_mode", "PAPER") if bot_state else "PAPER"
        tz = "Asia/Kolkata"
        today = get_current_trading_day(tz)

        # Retrieve today's trades
        trades = await db_manager.get_trades(trading_day=today)
        realized_pnl = sum(float(t.get("realized_pnl", 0.0) or 0.0) for t in trades if t.get("status") == "CLOSED")
        winning = len([t for t in trades if t.get("status") == "CLOSED" and float(t.get("realized_pnl", 0.0) or 0.0) > 0])
        losing = len([t for t in trades if t.get("status") == "CLOSED" and float(t.get("realized_pnl", 0.0) or 0.0) < 0])

        pos = bot_state.get("current_position") if bot_state else None
        unrealized_pnl = float(pos.get("unrealized_pnl", 0.0)) if pos else 0.0

        if mode == "LIVE" and delta_client.api_key:
            try:
                balances = await delta_client.get_wallet_balances()
                total_bal = 0.0
                avail_bal = 0.0
                for b in balances:
                    if b.get("asset_symbol") in ["USDT", "USD"]:
                        total_bal += float(b.get("balance", 0.0))
                        avail_bal += float(b.get("available_balance", 0.0))
                used_margin = total_bal - avail_bal
                return {
                    "total_balance": round(total_bal, 2),
                    "available_balance": round(avail_bal, 2),
                    "used_margin": round(used_margin, 2),
                    "today_realized_pnl": round(realized_pnl, 2),
                    "today_unrealized_pnl": round(unrealized_pnl, 2),
                    "today_trades_count": len(trades),
                    "winning_trades": winning,
                    "losing_trades": losing,
                }
            except Exception as e:
                logger.warning(f"Failed to fetch live balance: {e}")

        # Paper trading balance overview
        sim_total = self._simulated_balance + realized_pnl
        used_margin = (float(pos["entry_price"]) * float(pos["quantity"]) / 25.0) if pos else 0.0
        avail_bal = max(0.0, sim_total - used_margin)

        return {
            "total_balance": round(sim_total, 2),
            "available_balance": round(avail_bal, 2),
            "used_margin": round(used_margin, 2),
            "today_realized_pnl": round(realized_pnl, 2),
            "today_unrealized_pnl": round(unrealized_pnl, 2),
            "today_trades_count": len(trades),
            "winning_trades": winning,
            "losing_trades": losing,
        }

    async def tick(self):
        """
        Master execution tick:
        Evaluates active positions, closed candles, signals, and executes orders.
        """
        try:
            bot_state = await db_manager.get_bot_state()
            if not bot_state:
                return

            strategy_settings = await db_manager.get_strategy_settings()
            if not strategy_settings:
                return

            symbol = strategy_settings.get("symbol", "BTCUSD")
            timeframe = strategy_settings.get("timeframe", "1h")
            ema_period = strategy_settings.get("ema_period", 120)
            target_points = float(strategy_settings.get("target_points", 1500.0))
            stop_loss_points = float(strategy_settings.get("stop_loss_points", 100.0))
            max_daily_trades = int(strategy_settings.get("max_daily_trades", 2))
            position_size_pct = float(strategy_settings.get("position_size_percentage", 100.0))
            leverage = float(strategy_settings.get("leverage", 25.0))
            trading_enabled = strategy_settings.get("trading_enabled", True)
            allow_buy = strategy_settings.get("allow_buy", True)
            allow_sell = strategy_settings.get("allow_sell", True)
            tz = strategy_settings.get("daily_reset_timezone", "Asia/Kolkata")
            mode = bot_state.get("trading_mode", "PAPER")
            bot_status = bot_state.get("bot_status", "STOPPED")
            trading_day = get_current_trading_day(tz)

            # 1. Fetch current price
            current_price = await market_data_service.get_current_price(symbol)

            # 2. Evaluate open position for TP/SL
            if bot_state.get("current_position"):
                await position_manager.evaluate_open_position(current_price, bot_state)
                # Refresh state after position evaluation
                bot_state = await db_manager.get_bot_state()

            # 3. Periodic Reconciliation (every ~30s)
            self._reconcile_counter += 1
            if self._reconcile_counter >= 6:
                self._reconcile_counter = 0
                await reconciliation_service.reconcile()

            # 4. Fetch closed candles & compute EMA 120
            closed_candles = await market_data_service.get_closed_candles(
                symbol=symbol,
                resolution=timeframe,
                limit=max(ema_period + 30, 160)
            )

            signal_result = ema_strategy_engine.evaluate_signals(
                candles=closed_candles,
                period=ema_period,
                allow_buy=allow_buy,
                allow_sell=allow_sell
            )

            # Record signal in state
            if signal_result.get("ema"):
                signal_info = {
                    "symbol": symbol,
                    "direction": signal_result.get("signal", "HOLD"),
                    "candle_time": str(signal_result.get("candle_time")),
                    "close_price": signal_result.get("latest_close"),
                    "previous_close_price": signal_result.get("prev_close"),
                    "ema_value": signal_result.get("ema"),
                    "is_confirmed": True,
                    "reason": signal_result.get("reason"),
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                await db_manager.update_bot_state_fields({"last_signal": signal_info})

            # 5. Process signal ONLY IF bot is RUNNING and trading is enabled
            if (
                bot_status == "RUNNING"
                and trading_enabled
                and signal_result.get("is_new_signal")
                and signal_result.get("signal") in [StrategySignal.BUY, StrategySignal.SELL]
            ):
                signal_dir = signal_result["signal"]
                await db_manager.add_log(
                    event_type="EMA_CROSSOVER",
                    message=f"EMA crossover confirmed: {signal_result['reason']}",
                    severity="INFO",
                    metadata=signal_result
                )

                # STRICT ONE OPEN POSITION & MAX 2 TRADES CHECKS
                can_open, reason = await risk_manager.can_open_new_position(
                    trading_mode=mode,
                    trading_day_tz=tz,
                    max_daily_trades=max_daily_trades
                )

                if not can_open:
                    logger.info(f"Signal ignored: {reason}")
                    await db_manager.add_log(
                        event_type="SIGNAL_IGNORED",
                        message=f"Signal ignored: {reason}",
                        severity="WARNING",
                        metadata={"signal": signal_dir, "reason": reason}
                    )
                else:
                    # Proceed with order execution
                    account = await self.get_account_overview()
                    available_balance = account["available_balance"]

                    # Calculate position size
                    quantity = risk_manager.calculate_position_size(
                        available_balance=available_balance,
                        current_price=current_price,
                        position_size_pct=position_size_pct,
                        leverage=leverage,
                        contract_value=1.0,
                        min_order_qty=1.0,
                        qty_step=1.0
                    )

                    if quantity <= 0:
                        logger.warning("Calculated quantity is 0. Insufficient margin or balance.")
                        await db_manager.add_log(
                            event_type="ORDER_REJECTED",
                            message=f"Order rejected: Insufficient available balance (${available_balance}) for sizing.",
                            severity="ERROR"
                        )
                    else:
                        # Transition to SIGNAL_DETECTED
                        await db_manager.update_bot_state_fields({"state_machine_stage": "SIGNAL_DETECTED"})

                        # ATOMIC LOCK ACQUISITION
                        placeholder_pos = {
                            "trade_id": "pending",
                            "symbol": symbol,
                            "direction": signal_dir,
                            "entry_price": current_price,
                            "current_price": current_price,
                            "target_price": 0.0,
                            "stop_loss_price": 0.0,
                            "quantity": quantity,
                            "status": "PENDING",
                            "mode": mode,
                            "entry_time": datetime.now(timezone.utc).isoformat()
                        }
                        lock_acquired = await db_manager.atomic_acquire_position_lock(placeholder_pos)

                        if not lock_acquired:
                            logger.warning("Concurrency guard: Failed to acquire atomic position lock.")
                        else:
                            # ATOMIC DAILY TRADE COUNTER INCREMENT
                            count_incremented = await db_manager.atomic_increment_daily_trades(
                                trading_day=trading_day,
                                max_limit=max_daily_trades
                            )

                            if not count_incremented:
                                logger.warning("Daily trade limit reached during atomic increment.")
                                await db_manager.atomic_release_position_lock()
                                await db_manager.add_log(
                                    event_type="DAILY_LIMIT_REACHED",
                                    message=f"Maximum daily trade limit ({max_daily_trades}) reached. Entry blocked.",
                                    severity="WARNING"
                                )
                            else:
                                # EXECUTE ORDER
                                exec_res = await order_manager.execute_entry_order(
                                    mode=mode,
                                    symbol=symbol,
                                    direction=signal_dir,
                                    quantity=quantity,
                                    current_price=current_price,
                                    target_points=target_points,
                                    stop_loss_points=stop_loss_points,
                                    trading_day=trading_day,
                                    tick_size=0.5
                                )

                                if exec_res.get("success"):
                                    await db_manager.update_bot_state_fields({
                                        "current_position": exec_res["position"],
                                        "state_machine_stage": "POSITION_OPEN"
                                    })
                                else:
                                    # Entry failed, release lock
                                    await db_manager.atomic_release_position_lock()
                                    await db_manager.update_bot_state_fields({
                                        "state_machine_stage": "ORDER_REJECTED"
                                    })

            # 6. Broadcast live dashboard updates via WebSocket
            account = await self.get_account_overview()
            fresh_state = await db_manager.get_bot_state()
            live_ticker = await market_data_service.get_live_ticker(symbol)
            broadcast_payload = {
                "type": "TICK_UPDATE",
                "price": current_price,
                "symbol": symbol,
                "live_ticker": live_ticker,
                "ema": signal_result.get("ema"),
                "latest_close": signal_result.get("latest_close"),
                "prev_close": signal_result.get("prev_close"),
                "signal": signal_result.get("signal"),
                "bot_status": fresh_state.get("bot_status"),
                "state_machine_stage": fresh_state.get("state_machine_stage"),
                "current_position": fresh_state.get("current_position"),
                "account": account,
                "daily_trade_count": fresh_state.get("daily_trade_count"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await websocket_manager.broadcast(broadcast_payload)

        except Exception as e:
            logger.error(f"Error in engine tick: {e}", exc_info=True)

    async def run_loop(self):
        """Continuous background execution loop."""
        logger.info("Trading engine background loop started.")
        while True:
            await self.tick()
            await asyncio.sleep(1)

trading_engine = TradingEngine()

