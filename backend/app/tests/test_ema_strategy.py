import pytest
import time
from app.services.ema_strategy import EMAStrategyEngine, StrategySignal

def generate_candles(prices, base_time=1700000000, step=3600):
    candles = []
    for i, p in enumerate(prices):
        candles.append({
            "time": base_time + (i * step),
            "open": p - 5,
            "high": p + 10,
            "low": p - 10,
            "close": p,
            "volume": 50
        })
    return candles

def test_insufficient_candles():
    engine = EMAStrategyEngine(period=120)
    # 50 candles is less than required 120
    candles = generate_candles([60000.0] * 50)
    res = engine.evaluate_signals(candles)
    assert res["signal"] == StrategySignal.HOLD
    assert "Insufficient candles" in res["reason"]

def test_buy_crossover_detection():
    engine = EMAStrategyEngine(period=10)  # Use 10 for deterministic testing
    # Generate series where prices were low, then jump above EMA on the latest candle
    prices = [100.0] * 20
    # previous candle closes at or below EMA (100.0 <= 100.0)
    prices.append(100.0)
    # latest candle crosses above EMA
    prices.append(150.0)
    
    candles = generate_candles(prices)
    res = engine.evaluate_signals(candles, period=10)
    
    assert res["signal"] == StrategySignal.BUY
    assert res["is_new_signal"] is True
    assert res["prev_close"] <= res["prev_ema"]
    assert res["latest_close"] > res["ema"]

def test_sell_crossover_detection():
    engine = EMAStrategyEngine(period=10)
    # Generate series where prices were high, then drop below EMA on the latest candle
    prices = [200.0] * 20
    # previous candle closes at or above EMA (200.0 >= 200.0)
    prices.append(200.0)
    # latest candle crosses below EMA
    prices.append(120.0)
    
    candles = generate_candles(prices)
    res = engine.evaluate_signals(candles, period=10)
    
    assert res["signal"] == StrategySignal.SELL
    assert res["is_new_signal"] is True
    assert res["prev_close"] >= res["prev_ema"]
    assert res["latest_close"] < res["ema"]

def test_no_duplicate_signal_on_same_candle():
    engine = EMAStrategyEngine(period=10)
    prices = [100.0] * 20 + [100.0, 150.0]
    candles = generate_candles(prices)
    
    # First evaluation: BUY
    res1 = engine.evaluate_signals(candles, period=10)
    assert res1["signal"] == StrategySignal.BUY
    assert res1["is_new_signal"] is True

    # Immediate second evaluation on the SAME closed candle timestamp
    res2 = engine.evaluate_signals(candles, period=10)
    assert res2["signal"] == StrategySignal.HOLD
    assert res2["is_new_signal"] is False
    assert "already evaluated" in res2["reason"]

def test_allow_buy_and_allow_sell_flags():
    engine = EMAStrategyEngine(period=10)
    prices = [100.0] * 20 + [100.0, 150.0]
    candles = generate_candles(prices)
    
    # allow_buy=False should suppress BUY signal
    res = engine.evaluate_signals(candles, period=10, allow_buy=False)
    assert res["signal"] == StrategySignal.HOLD
    assert "disabled in settings" in res["reason"]

