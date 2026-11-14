import math
import logging
from typing import Dict, Any, Tuple, Optional
from app.database import db_manager
from app.services.delta_exchange import delta_client
from app.utils.datetime_utils import get_current_trading_day

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Risk Manager enforcing all safety and sizing rules:
    1. Strict One Open Position Rule
    2. Maximum Two Trades Per Day Limit
    3. Position Sizing & Margin Validation
    4. Stop Loss (100 pts) and Take Profit (1500 pts) Calculations
    """
    def __init__(self):
        pass

    def round_to_tick_size(self, price: float, tick_size: float = 0.5) -> float:
        """Round price to the contract's minimum tick size."""
        if tick_size <= 0:
            return round(price, 2)
        ticks = round(price / tick_size)
        rounded = ticks * tick_size
        # format according to tick decimals
        decimals = max(0, -int(math.floor(math.log10(tick_size)))) if tick_size < 1 else 0
        return round(rounded, decimals)

    def calculate_tp_sl(
        self,
        direction: str,
        entry_price: float,
        target_points: float = 1500.0,
        stop_loss_points: float = 100.0,
        tick_size: float = 0.5
    ) -> Tuple[float, float]:
        """
        Calculates Take Profit and Stop Loss based on entry price and points.
        BUY: TP = entry + target, SL = entry - stop_loss
        SELL: TP = entry - target, SL = entry + stop_loss
        """
        if direction.upper() == "BUY":
            tp = entry_price + target_points
            sl = entry_price - stop_loss_points
        else:
            tp = entry_price - target_points
            sl = entry_price + stop_loss_points

        return (
            self.round_to_tick_size(tp, tick_size),
            self.round_to_tick_size(sl, tick_size)
        )

    async def can_open_new_position(
        self,
        trading_mode: str,
        trading_day_tz: str = "Asia/Kolkata",
        max_daily_trades: int = 2
    ) -> Tuple[bool, str]:
        """
        Validates whether a new position is permitted to open.
        Enforces:
        1. One Open Position Rule (Exchange + State + DB)
        2. Maximum Daily Trades Rule
        """
        current_trading_day = get_current_trading_day(trading_day_tz)
        bot_state = await db_manager.get_bot_state()

        if not bot_state:
            return False, "Bot state uninitialized"

        # Check internal position
        if bot_state.get("current_position") is not None:
            return False, "One Open Position Rule violation: A position is already open."

        # Check stage
        stage = bot_state.get("state_machine_stage", "IDLE")
        if stage in ["ENTRY_PENDING", "POSITION_OPEN", "EXIT_PENDING", "PROTECTION_PENDING"]:
            return False, f"Trade currently in progress (stage={stage}). Entry blocked."

        # Check daily trade count
        daily_count = bot_state.get("daily_trade_count", 0)
        stored_day = bot_state.get("trading_day")
        if stored_day == current_trading_day and daily_count >= max_daily_trades:
            return False, f"Maximum daily trades limit reached ({daily_count}/{max_daily_trades} for {current_trading_day})."

        # In LIVE mode, cross-verify with Delta Exchange
        if trading_mode.upper() == "LIVE" and delta_client.api_key:
            try:
                positions = await delta_client.get_positions()
                for pos in positions:
                    size = float(pos.get("size", 0))
                    if size != 0:
                        return False, f"Delta Exchange reports an active open position (size={size})."
            except Exception as e:
                logger.error(f"Error checking live positions on Delta Exchange: {e}")
                return False, f"Exchange position verification failed: {e}"

        return True, "Safe to open position"

    def calculate_position_size(
        self,
        available_balance: float,
        current_price: float,
        position_size_pct: float = 100.0,
        leverage: float = 25.0,
        contract_value: float = 1.0,
        min_order_qty: float = 1.0,
        qty_step: float = 1.0
    ) -> float:
        """
        Calculate valid position quantity:
        Total Capital Allocation = available_balance * (position_size_pct / 100.0)
        Total Notional Exposure = Capital Allocation * leverage
        Order Contracts = Total Notional Exposure / (current_price * contract_value)
        Rounded down to qty_step, subject to min_order_qty and margin checks.
        """
        if available_balance <= 0 or current_price <= 0:
            return 0.0

        pct_clamped = min(max(position_size_pct, 1.0), 100.0)
        capital_allocated = available_balance * (pct_clamped / 100.0)
        notional_exposure = capital_allocated * leverage

        contract_unit_value = current_price * contract_value
        raw_quantity = notional_exposure / contract_unit_value

        # Round down to valid step size
        steps = math.floor(raw_quantity / qty_step)
        final_qty = steps * qty_step

        if final_qty < min_order_qty:
            logger.warning(
                f"Calculated quantity {final_qty} is below contract minimum {min_order_qty} "
                f"(Balance: {available_balance}, Price: {current_price}, Leverage: {leverage}x)"
            )
            return 0.0

        return round(final_qty, 4)

risk_manager = RiskManager()

