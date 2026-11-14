import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.database import db_manager
from app.services.delta_exchange import delta_client
from app.services.risk_manager import risk_manager

logger = logging.getLogger(__name__)

class OrderManager:
    """
    Order execution manager.
    Handles Paper Trading fills and Live Delta Exchange order execution
    with immediate protective stop-loss and take-profit enforcement.
    """
    async def execute_entry_order(
        self,
        mode: str,
        symbol: str,
        direction: str,  # BUY or SELL
        quantity: float,
        current_price: float,
        target_points: float,
        stop_loss_points: float,
        trading_day: str,
        tick_size: float = 0.5
    ) -> Dict[str, Any]:
        """
        Executes entry order with protective TP/SL.
        Returns execution result dict.
        """
        client_order_id = f"EMA_{uuid.uuid4().hex[:12]}"
        
        # Calculate TP and SL prices based on actual execution price
        tp_price, sl_price = risk_manager.calculate_tp_sl(
            direction=direction,
            entry_price=current_price,
            target_points=target_points,
            stop_loss_points=stop_loss_points,
            tick_size=tick_size
        )

        if mode.upper() == "PAPER":
            # Paper trading fill simulation
            trade_id = str(uuid.uuid4())
            trade_doc = {
                "_id": trade_id,
                "symbol": symbol,
                "direction": direction.upper(),
                "entry_price": current_price,
                "exit_price": None,
                "quantity": quantity,
                "target_price": tp_price,
                "stop_loss_price": sl_price,
                "entry_time": datetime.now(timezone.utc),
                "exit_time": None,
                "realized_pnl": 0.0,
                "status": "OPEN",
                "exchange_order_ids": [f"PAPER_{client_order_id}"],
                "exit_reason": None,
                "trading_day": trading_day,
                "mode": "PAPER",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            await db_manager.create_trade(trade_doc)

            position_doc = {
                "trade_id": trade_id,
                "symbol": symbol,
                "direction": direction.upper(),
                "entry_price": current_price,
                "current_price": current_price,
                "target_price": tp_price,
                "stop_loss_price": sl_price,
                "quantity": quantity,
                "unrealized_pnl": 0.0,
                "status": "OPEN",
                "mode": "PAPER",
                "entry_time": datetime.now(timezone.utc).isoformat()
            }

            await db_manager.add_log(
                event_type=f"{direction.upper()}_ORDER",
                message=f"[PAPER] Opened {direction.upper()} position on {symbol} @ {current_price}. Target: {tp_price}, SL: {sl_price}, Qty: {quantity}",
                severity="SUCCESS",
                metadata={"trade_id": trade_id, "mode": "PAPER", "tp": tp_price, "sl": sl_price}
            )

            return {
                "success": True,
                "trade_id": trade_id,
                "position": position_doc,
                "mode": "PAPER"
            }

        # LIVE Trading Mode
        try:
            product = await delta_client.get_product(symbol)
            if not product:
                raise ValueError(f"Product {symbol} not found on Delta Exchange")
            product_id = product["id"]

            # Place order on Delta Exchange with native bracket SL/TP
            order_res = await delta_client.place_order(
                product_id=product_id,
                size=int(quantity),
                side=direction.lower(),
                order_type="market_order",
                bracket_stop_loss_price=sl_price,
                bracket_take_profit_price=tp_price,
                client_order_id=client_order_id
            )

            if not order_res.get("success", False) and "result" not in order_res:
                error_msg = order_res.get("error", {}).get("message", "Order placement failed")
                raise RuntimeError(f"Delta exchange rejected entry order: {error_msg}")

            result_order = order_res.get("result", {})
            filled_price = float(result_order.get("average_fill_price") or current_price)
            exchange_order_id = str(result_order.get("id", client_order_id))

            # Recalculate TP/SL based on actual filled average price
            tp_price, sl_price = risk_manager.calculate_tp_sl(
                direction=direction,
                entry_price=filled_price,
                target_points=target_points,
                stop_loss_points=stop_loss_points,
                tick_size=tick_size
            )

            trade_id = str(uuid.uuid4())
            trade_doc = {
                "_id": trade_id,
                "symbol": symbol,
                "direction": direction.upper(),
                "entry_price": filled_price,
                "exit_price": None,
                "quantity": quantity,
                "target_price": tp_price,
                "stop_loss_price": sl_price,
                "entry_time": datetime.now(timezone.utc),
                "exit_time": None,
                "realized_pnl": 0.0,
                "status": "OPEN",
                "exchange_order_ids": [exchange_order_id],
                "exit_reason": None,
                "trading_day": trading_day,
                "mode": "LIVE",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            await db_manager.create_trade(trade_doc)

            position_doc = {
                "trade_id": trade_id,
                "symbol": symbol,
                "direction": direction.upper(),
                "entry_price": filled_price,
                "current_price": filled_price,
                "target_price": tp_price,
                "stop_loss_price": sl_price,
                "quantity": quantity,
                "unrealized_pnl": 0.0,
                "status": "OPEN",
                "mode": "LIVE",
                "entry_time": datetime.now(timezone.utc).isoformat()
            }

            await db_manager.add_log(
                event_type=f"{direction.upper()}_ORDER",
                message=f"[LIVE] Executed {direction.upper()} on {symbol} @ {filled_price}. Target: {tp_price}, SL: {sl_price}, Qty: {quantity}",
                severity="SUCCESS",
                metadata={"trade_id": trade_id, "mode": "LIVE", "order_id": exchange_order_id}
            )

            return {
                "success": True,
                "trade_id": trade_id,
                "position": position_doc,
                "mode": "LIVE"
            }

        except Exception as e:
            logger.critical(f"Live order execution failed: {e}")
            await db_manager.add_log(
                event_type="ORDER_REJECTED",
                message=f"Live order failed: {str(e)}",
                severity="CRITICAL",
                metadata={"symbol": symbol, "direction": direction, "error": str(e)}
            )
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_exit_order(
        self,
        trade_id: str,
        symbol: str,
        direction: str,
        quantity: float,
        entry_price: float,
        exit_price: float,
        exit_reason: str,
        mode: str
    ) -> Dict[str, Any]:
        """
        Executes position exit (closing).
        Computes realized PnL and updates trade record to CLOSED.
        """
        # PnL formula
        if direction.upper() == "BUY":
            pnl_points = exit_price - entry_price
        else:
            pnl_points = entry_price - exit_price

        realized_pnl = round(pnl_points * quantity, 2)

        if mode.upper() == "LIVE":
            try:
                product = await delta_client.get_product(symbol)
                if product:
                    await delta_client.close_position_market(product["id"])
                    await delta_client.cancel_all_orders(product["id"])
            except Exception as e:
                logger.error(f"Live exit error: {e}")

        # Update trade in database
        now = datetime.now(timezone.utc)
        await db_manager.update_trade(trade_id, {
            "exit_price": exit_price,
            "exit_time": now,
            "realized_pnl": realized_pnl,
            "status": "CLOSED",
            "exit_reason": exit_reason,
            "updated_at": now
        })

        # Release position lock in bot state
        await db_manager.atomic_release_position_lock()

        severity = "SUCCESS" if realized_pnl >= 0 else "WARNING"
        await db_manager.add_log(
            event_type=f"{exit_reason}_TRIGGERED" if "STOP" in exit_reason or "TARGET" in exit_reason else "POSITION_CLOSED",
            message=f"Closed {direction} trade on {symbol} @ {exit_price} ({exit_reason}). PnL: ${realized_pnl:+.2f}",
            severity=severity,
            metadata={
                "trade_id": trade_id,
                "exit_price": exit_price,
                "realized_pnl": realized_pnl,
                "reason": exit_reason
            }
        )

        return {
            "success": True,
            "realized_pnl": realized_pnl,
            "exit_price": exit_price,
            "exit_reason": exit_reason
        }

order_manager = OrderManager()

