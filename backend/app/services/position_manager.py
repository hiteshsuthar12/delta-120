import logging
from typing import Dict, Any, Optional, Tuple
from app.database import db_manager
from app.services.order_manager import order_manager

logger = logging.getLogger(__name__)

class PositionManager:
    """
    Position Manager:
    Monitors open position, calculates live unrealized P&L,
    evaluates Target and Stop Loss conditions, and coordinates exits.
    """
    async def evaluate_open_position(
        self,
        current_price: float,
        bot_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate currently open position against latest market price.
        Triggers exit if Target or Stop Loss price levels are breached.
        """
        position = bot_state.get("current_position")
        if not position:
            return None

        trade_id = position.get("trade_id")
        symbol = position.get("symbol", "BTCUSD")
        direction = position.get("direction", "BUY").upper()
        entry_price = float(position.get("entry_price", 0.0))
        target_price = float(position.get("target_price", 0.0))
        stop_loss_price = float(position.get("stop_loss_price", 0.0))
        quantity = float(position.get("quantity", 0.0))
        mode = position.get("mode", "PAPER")

        # Calculate unrealized P&L
        if direction == "BUY":
            points = current_price - entry_price
            hit_tp = current_price >= target_price
            hit_sl = current_price <= stop_loss_price
        else:  # SELL
            points = entry_price - current_price
            hit_tp = current_price <= target_price
            hit_sl = current_price >= stop_loss_price

        unrealized_pnl = round(points * quantity, 2)

        # Update position's current price & unrealized PnL in state
        position["current_price"] = current_price
        position["unrealized_pnl"] = unrealized_pnl
        await db_manager.update_bot_state_fields({"current_position": position})

        # Check exits
        if hit_tp:
            logger.info(f"Take Profit triggered for {symbol} {direction} @ {current_price} (Target: {target_price})")
            return await order_manager.execute_exit_order(
                trade_id=trade_id,
                symbol=symbol,
                direction=direction,
                quantity=quantity,
                entry_price=entry_price,
                exit_price=target_price,
                exit_reason="TARGET",
                mode=mode
            )

        if hit_sl:
            logger.warning(f"Stop Loss triggered for {symbol} {direction} @ {current_price} (SL: {stop_loss_price})")
            return await order_manager.execute_exit_order(
                trade_id=trade_id,
                symbol=symbol,
                direction=direction,
                quantity=quantity,
                entry_price=entry_price,
                exit_price=stop_loss_price,
                exit_reason="STOP_LOSS",
                mode=mode
            )

        return None

position_manager = PositionManager()

