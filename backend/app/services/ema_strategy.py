import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class StrategySignal:
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class EMAStrategyEngine:
    """
    EMA 120 Trading Strategy Engine.
    Strictly evaluates fully closed candles only.
    Prevents duplicate signals for the same candle.
    """
    def __init__(self, period: int = 120):
        self.period = period
        self.last_evaluated_candle_time: Optional[int] = None
        self.last_signal_direction: Optional[str] = None

    def calculate_ema(self, candles: List[Dict[str, Any]], period: Optional[int] = None) -> pd.DataFrame:
        """
        Calculates EMA using pandas exponential moving average.
        Requires sufficient candles (at least period length, ideally 150+).
        """
        span = period or self.period
        if len(candles) < span:
            raise ValueError(f"Insufficient historical candles for EMA {span}. Have {len(candles)}, need at least {span}.")

        df = pd.DataFrame(candles)
        # Standardize numeric types
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df["ema"] = df["close"].ewm(span=span, adjust=False).mean()
        return df

    def evaluate_signals(
        self,
        candles: List[Dict[str, Any]],
        period: Optional[int] = None,
        allow_buy: bool = True,
        allow_sell: bool = True,
        force_reevaluate: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates closed candles for EMA crossover:
        - BUY: previous candle closed <= EMA, latest closed candle > EMA.
        - SELL: previous candle closed >= EMA, latest closed candle < EMA.
        """
        span = period or self.period
        if len(candles) < max(span + 2, 10):
            return {
                "signal": StrategySignal.HOLD,
                "reason": f"Insufficient candles for EMA {span} evaluation (count={len(candles)})",
                "is_new_signal": False,
                "ema": None,
                "latest_close": None,
                "prev_close": None,
                "candle_time": None
            }

        df = self.calculate_ema(candles, span)
        
        # Latest fully closed candle is at iloc[-1]
        # Previous fully closed candle is at iloc[-2]
        prev_candle = df.iloc[-2]
        latest_candle = df.iloc[-1]

        prev_close = float(prev_candle["close"])
        prev_ema = float(prev_candle["ema"])
        latest_close = float(latest_candle["close"])
        latest_ema = float(latest_candle["ema"])
        latest_time = int(latest_candle["time"])

        # Check for duplicate evaluation of the exact same closed candle
        if not force_reevaluate and self.last_evaluated_candle_time == latest_time:
            return {
                "signal": StrategySignal.HOLD,
                "reason": f"Candle at timestamp {latest_time} was already evaluated. Waiting for new closed candle.",
                "is_new_signal": False,
                "ema": round(latest_ema, 2),
                "latest_close": round(latest_close, 2),
                "prev_close": round(prev_close, 2),
                "candle_time": latest_time
            }

        detected_signal = StrategySignal.HOLD
        reason = "No crossover detected"

        # BUY Condition: previous <= EMA and latest > EMA
        if prev_close <= prev_ema and latest_close > latest_ema:
            if allow_buy:
                detected_signal = StrategySignal.BUY
                reason = f"Bullish Crossover: Previous {prev_close} <= EMA {prev_ema:.2f} and Latest {latest_close} > EMA {latest_ema:.2f}"
            else:
                reason = "Bullish crossover detected but BUY trades are disabled in settings."

        # SELL Condition: previous >= EMA and latest < EMA
        elif prev_close >= prev_ema and latest_close < latest_ema:
            if allow_sell:
                detected_signal = StrategySignal.SELL
                reason = f"Bearish Crossover: Previous {prev_close} >= EMA {prev_ema:.2f} and Latest {latest_close} < EMA {latest_ema:.2f}"
            else:
                reason = "Bearish crossover detected but SELL trades are disabled in settings."

        # Record last evaluated candle timestamp
        self.last_evaluated_candle_time = latest_time
        if detected_signal != StrategySignal.HOLD:
            self.last_signal_direction = detected_signal

        return {
            "signal": detected_signal,
            "reason": reason,
            "is_new_signal": detected_signal != StrategySignal.HOLD,
            "ema": round(latest_ema, 2),
            "prev_ema": round(prev_ema, 2),
            "latest_close": round(latest_close, 2),
            "prev_close": round(prev_close, 2),
            "candle_time": latest_time
        }

ema_strategy_engine = EMAStrategyEngine()

