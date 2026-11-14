import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.database import db_manager
from app.services.delta_exchange import delta_client

logger = logging.getLogger(__name__)

class ReconciliationService:
    """
    Reconciliation Service:
    Periodically checks Delta Exchange against MongoDB state to ensure
    absolute synchronization between database records and live exchange positions.
    """
    async def reconcile(self) -> Dict[str, Any]:
        bot_state = await db_manager.get_bot_state()
        if not bot_state:
            return {"status": "skipped", "reason": "No bot state"}

        trading_mode = bot_state.get("trading_mode", "PAPER")
        current_position = bot_state.get("current_position")

        if trading_mode.upper() != "LIVE" or not delta_client.api_key:
            return {"status": "ok", "mode": trading_mode, "reconciled": True}

        try:
            exchange_positions = await delta_client.get_positions()
            symbol = current_position.get("symbol", "BTCUSD") if current_position else "BTCUSD"
            product = await delta_client.get_product(symbol)
            product_id = product["id"] if product else None

            exchange_open = False
            exchange_pos_size = 0.0
            if product_id:
                for p in exchange_positions:
                    if p.get("product_id") == product_id and float(p.get("size", 0)) != 0:
                        exchange_open = True
                        exchange_pos_size = float(p.get("size"))
                        break

            # Case 1: DB says position is OPEN, but Exchange says position is CLOSED (0 size)
            if current_position is not None and not exchange_open:
                logger.info("Reconciliation: Position was closed on Delta Exchange. Synchronizing database...")
                trade_id = current_position.get("trade_id")
                # Determine exit details
                now = datetime.now(timezone.utc)
                await db_manager.update_trade(trade_id, {
                    "status": "CLOSED",
                    "exit_time": now,
                    "exit_reason": "EXCHANGE_CONFIRMED_CLOSE",
                    "updated_at": now
                })
                await db_manager.atomic_release_position_lock()
                await db_manager.add_log(
                    event_type="RECONCILIATION_SYNC",
                    message="Position closed externally on Delta Exchange. Database state reconciled.",
                    severity="INFO",
                    metadata={"trade_id": trade_id}
                )
                return {"status": "reconciled", "action": "closed_internal_position"}

            # Case 2: DB has no open position, but Exchange reports an active position
            if current_position is None and exchange_open:
                logger.critical(f"Reconciliation ALERT: Exchange has active position (size={exchange_pos_size}) not tracked in DB!")
                await db_manager.add_log(
                    event_type="UNTRACKED_POSITION_DETECTED",
                    message=f"Discrepancy: Active position found on Delta Exchange (size={exchange_pos_size}) without active DB record.",
                    severity="CRITICAL",
                    metadata={"size": exchange_pos_size, "symbol": symbol}
                )
                return {"status": "alert", "error": "Untracked exchange position"}

            return {"status": "ok", "mode": "LIVE", "synchronized": True}

        except Exception as e:
            logger.error(f"Reconciliation error: {e}")
            return {"status": "error", "error": str(e)}

reconciliation_service = ReconciliationService()

