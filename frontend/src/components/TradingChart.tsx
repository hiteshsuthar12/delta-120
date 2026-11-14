import React, { useEffect, useRef, useState } from 'react';
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  ColorType,
  CrosshairMode,
  type IChartApi,
  type ISeriesApi,
} from 'lightweight-charts';
import { fetchChartCandles } from '../api';
import type { BotPosition, Trade, MarketTicker } from '../types';
import { Undo2, Redo2, SlidersHorizontal, BarChart3, Eye } from 'lucide-react';

interface Props {
  symbol: string;
  currentPrice: number;
  currentEma: number;
  position: BotPosition | null;
  recentTrades?: Trade[];
  liveTicker?: MarketTicker | null;
}

export const TradingChart: React.FC<Props> = ({
  symbol,
  currentPrice,
  currentEma,
  position,
  recentTrades = [],
  liveTicker = null,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const emaSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const lastBarRef = useRef<{
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
  } | null>(null);
  const tpLineRef = useRef<any>(null);
  const slLineRef = useRef<any>(null);

  const [activeTimeframe, setActiveTimeframe] = useState<string>('1h');
  const [oneClickTrade, setOneClickTrade] = useState<boolean>(true);
  const [showEma, setShowEma] = useState<boolean>(true);
  const [hoveredOhlc, setHoveredOhlc] = useState<{
    open: number;
    high: number;
    low: number;
    close: number;
    change: number;
    changePct: number;
    isUp: boolean;
  } | null>(null);

  const [latestCandle, setLatestCandle] = useState<{
    open: number;
    high: number;
    low: number;
    close: number;
    change: number;
    changePct: number;
    isUp: boolean;
  } | null>(null);

  const [displayEma, setDisplayEma] = useState<number>(currentEma);

  // Timeframes list inspired by image 1
  const timeframes = ['30s', '1m', '5m', '15m', '1h', '4h', '1D', '3m'];

  // Calculate live bid/ask quote & spread for the top-left trading widget
  const bidPrice = liveTicker?.best_bid
    ? liveTicker.best_bid.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })
    : (currentPrice > 0 ? (currentPrice - 0.5).toFixed(1) : '73,800.0');

  const askPrice = liveTicker?.best_ask
    ? liveTicker.best_ask.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })
    : (currentPrice > 0 ? (currentPrice + 0.5).toFixed(1) : '73,800.5');

  const spread = (liveTicker?.best_ask && liveTicker?.best_bid)
    ? (liveTicker.best_ask - liveTicker.best_bid).toFixed(1)
    : '0.5';

  // Initialize and manage Lightweight Chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const container = chartContainerRef.current;

    // Create TradingView Lightweight Chart with dark theme
    const chart = createChart(container, {
      width: container.clientWidth,
      height: 480,
      layout: {
        background: { type: ColorType.Solid, color: '#0d1117' },
        textColor: '#8b949e',
        fontSize: 11,
        fontFamily: 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto',
      },
      grid: {
        vertLines: { color: '#161b22', style: 1 },
        horzLines: { color: '#161b22', style: 1 },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: '#388bfd',
          width: 1,
          style: 3,
          labelBackgroundColor: '#1f6feb',
        },
        horzLine: {
          color: '#388bfd',
          width: 1,
          style: 3,
          labelBackgroundColor: '#1f6feb',
        },
      },
      rightPriceScale: {
        borderColor: '#30363d',
        scaleMargins: {
          top: 0.12,
          bottom: 0.15,
        },
        autoScale: true,
      },
      timeScale: {
        borderColor: '#30363d',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // 1. Add Japanese Candlestick Series (exact colors from image 1)
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      priceLineVisible: true,
      lastValueVisible: true,
      priceLineWidth: 1,
      priceLineColor: '#26a69a',
    });
    candleSeriesRef.current = candleSeries;

    // 2. Add EMA 120 Line Series (blue line like image 1)
    const emaSeries = chart.addSeries(LineSeries, {
      color: '#2962FF',
      lineWidth: 2,
      priceLineVisible: true,
      title: 'EMA 120',
      lastValueVisible: true,
    });
    emaSeriesRef.current = emaSeries;

    // Crosshair move handler for OHLC header
    chart.subscribeCrosshairMove((param) => {
      if (!param || !param.time || !param.seriesData) {
        setHoveredOhlc(null);
        return;
      }
      const candleData: any = param.seriesData.get(candleSeries);
      if (candleData && candleData.open !== undefined) {
        const change = candleData.close - candleData.open;
        const changePct = (change / candleData.open) * 100;
        setHoveredOhlc({
          open: candleData.open,
          high: candleData.high,
          low: candleData.low,
          close: candleData.close,
          change,
          changePct,
          isUp: change >= 0,
        });
      }

      const emaData: any = param.seriesData.get(emaSeries);
      if (emaData && emaData.value !== undefined) {
        setDisplayEma(emaData.value);
      }
    });

    // Handle container resize
    const handleResize = () => {
      if (chartRef.current && container) {
        chartRef.current.applyOptions({
          width: container.clientWidth,
        });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, []);

  // Fetch real candles from backend and populate chart
  useEffect(() => {
    let isMounted = true;

    const loadCandles = async () => {
      try {
        const data = await fetchChartCandles({
          symbol: symbol || 'BTCUSD',
          resolution: activeTimeframe,
          limit: 250,
        });

        if (!isMounted) return;

        if (candleSeriesRef.current && data.candles && data.candles.length > 0) {
          candleSeriesRef.current.setData(data.candles as any);

          // Compute latest candle info and cache for real-time tick updates
          const last = data.candles[data.candles.length - 1];
          lastBarRef.current = { ...last };
          const change = last.close - last.open;
          const changePct = (change / last.open) * 100;
          setLatestCandle({
            open: last.open,
            high: last.high,
            low: last.low,
            close: last.close,
            change,
            changePct,
            isUp: change >= 0,
          });
        }

        if (emaSeriesRef.current && data.ema && data.ema.length > 0) {
          emaSeriesRef.current.setData(data.ema as any);
          setDisplayEma(data.latest_ema);
        }

        // Fit content on initial load
        if (chartRef.current) {
          chartRef.current.timeScale().fitContent();
        }
      } catch (err) {
        console.error('Error fetching candles for chart:', err);
      }
    };

    loadCandles();
    const interval = setInterval(loadCandles, 15000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [symbol, activeTimeframe, recentTrades.length]);

  // Real-time dynamic candle & price line movement on the chart (updates as price moves)
  useEffect(() => {
    if (!candleSeriesRef.current || !lastBarRef.current || !currentPrice || currentPrice <= 0) return;

    const currentBar = lastBarRef.current;
    const nowSec = Math.floor(Date.now() / 1000);

    // Frame duration in seconds
    let tfSec = 3600;
    if (activeTimeframe === '30s') tfSec = 30;
    else if (activeTimeframe === '1m') tfSec = 60;
    else if (activeTimeframe === '3m') tfSec = 180;
    else if (activeTimeframe === '5m') tfSec = 300;
    else if (activeTimeframe === '15m') tfSec = 900;
    else if (activeTimeframe === '4h') tfSec = 14400;
    else if (activeTimeframe === '1D') tfSec = 86400;

    let targetTime = currentBar.time;
    let isNewCandle = false;

    // Check if candle period rolled over
    if (nowSec >= currentBar.time + tfSec) {
      targetTime = Math.floor(nowSec / tfSec) * tfSec;
      isNewCandle = true;
    }

    const updatedBar = isNewCandle
      ? {
          time: targetTime,
          open: currentPrice,
          high: currentPrice,
          low: currentPrice,
          close: currentPrice,
        }
      : {
          time: targetTime,
          open: currentBar.open,
          high: Math.max(currentBar.high, currentPrice),
          low: Math.min(currentBar.low, currentPrice),
          close: currentPrice,
        };

    lastBarRef.current = updatedBar;

    try {
      // 1. Physically update the active candlestick & move the current price line on the chart
      candleSeriesRef.current.update(updatedBar as any);

      // Color the price line green if bullish, red if bearish
      const isUp = currentPrice >= updatedBar.open;
      candleSeriesRef.current.applyOptions({
        priceLineColor: isUp ? '#26a69a' : '#ef5350',
      });

      // 2. Dynamically update the header bar OHLC stats
      const change = currentPrice - updatedBar.open;
      const changePct = (change / updatedBar.open) * 100;
      setLatestCandle({
        open: updatedBar.open,
        high: updatedBar.high,
        low: updatedBar.low,
        close: currentPrice,
        change,
        changePct,
        isUp,
      });

      // 3. Move the latest point of the EMA 120 line to match the active bar
      if (emaSeriesRef.current && currentEma > 0) {
        emaSeriesRef.current.update({
          time: targetTime,
          value: currentEma,
        } as any);
        setDisplayEma(currentEma);
      }
    } catch (err) {
      console.debug('Error moving price on chart:', err);
    }
  }, [currentPrice, currentEma, activeTimeframe]);

  // Update real-time price & position TP/SL lines
  useEffect(() => {
    if (!candleSeriesRef.current) return;

    // Clear old lines
    if (tpLineRef.current) {
      candleSeriesRef.current.removePriceLine(tpLineRef.current);
      tpLineRef.current = null;
    }
    if (slLineRef.current) {
      candleSeriesRef.current.removePriceLine(slLineRef.current);
      slLineRef.current = null;
    }

    // Add active position lines
    if (position) {
      tpLineRef.current = candleSeriesRef.current.createPriceLine({
        price: position.target_price,
        color: '#10b981',
        lineWidth: 2,
        lineStyle: 2, // Dashed
        axisLabelVisible: true,
        title: 'TP (+1500)',
      });

      slLineRef.current = candleSeriesRef.current.createPriceLine({
        price: position.stop_loss_price,
        color: '#ef4444',
        lineWidth: 2,
        lineStyle: 2, // Dashed
        axisLabelVisible: true,
        title: 'SL (-100)',
      });
    }
  }, [position]);

  // Toggle EMA visibility
  useEffect(() => {
    if (emaSeriesRef.current) {
      emaSeriesRef.current.applyOptions({
        visible: showEma,
      });
    }
  }, [showEma]);

  // Active display OHLC values (hovered or latest)
  const currentOhlc = hoveredOhlc || latestCandle || {
    open: currentPrice || 73703.5,
    high: (currentPrice || 73703.5) + 180,
    low: (currentPrice || 73703.5) - 48,
    close: currentPrice || 73800.5,
    change: 97.5,
    changePct: 0.13,
    isUp: true,
  };

  return (
    <div className="bg-[#0d1117] border border-[#21262d] rounded-xl overflow-hidden shadow-2xl flex flex-col">
      {/* 1. TOP TIMEFRAME & TOOLBAR (Matching Image 1) */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2 border-b border-[#21262d] bg-[#161b22]/70 text-xs">
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {timeframes.map((tf) => (
            <button
              key={tf}
              onClick={() => setActiveTimeframe(tf)}
              className={`px-2 py-1 rounded text-xs font-semibold transition ${
                activeTimeframe === tf
                  ? 'text-[#f08c00] border-b-2 border-[#f08c00] font-bold'
                  : 'text-[#8b949e] hover:text-[#c9d1d9]'
              }`}
            >
              {tf}
            </button>
          ))}

          <div className="h-4 w-[1px] bg-[#30363d] mx-1.5 hidden sm:block" />

          {/* Quick Icons */}
          <div className="hidden sm:flex items-center gap-1 text-[#8b949e]">
            <button className="p-1 hover:text-white rounded hover:bg-[#21262d]" title="Candles">
              <BarChart3 className="h-3.5 w-3.5" />
            </button>
            <button className="p-1 hover:text-white rounded hover:bg-[#21262d]" title="Indicators">
              <SlidersHorizontal className="h-3.5 w-3.5" />
            </button>
            <button className="p-1 hover:text-white rounded hover:bg-[#21262d]" title="Undo">
              <Undo2 className="h-3.5 w-3.5" />
            </button>
            <button className="p-1 hover:text-white rounded hover:bg-[#21262d]" title="Redo">
              <Redo2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* 1-Click Trade Switch (Matching Image 1 top right) */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-[#21262d] px-2.5 py-1 rounded-md">
            <span className="text-[11px] text-[#8b949e] font-medium">1-Click Trade</span>
            <button
              onClick={() => setOneClickTrade(!oneClickTrade)}
              className={`relative inline-flex h-4 w-7 shrink-0 cursor-pointer rounded-full border border-transparent transition-colors duration-200 ease-in-out ${
                oneClickTrade ? 'bg-[#238636]' : 'bg-[#30363d]'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  oneClickTrade ? 'translate-x-3.5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* 2. OHLC HEADER BAR (Exact format from Image 1) */}
      <div className="px-4 py-2 border-b border-[#21262d]/70 flex flex-wrap items-center justify-between gap-3 text-xs font-mono bg-[#0d1117]">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-bold text-white text-sm tracking-tight">{symbol}</span>
          <span className="text-[#8b949e]">
            O <span className={currentOhlc.isUp ? 'text-[#26a69a]' : 'text-[#ef5350]'}>{currentOhlc.open.toLocaleString()}</span>
          </span>
          <span className="text-[#8b949e]">
            H <span className={currentOhlc.isUp ? 'text-[#26a69a]' : 'text-[#ef5350]'}>{currentOhlc.high.toLocaleString()}</span>
          </span>
          <span className="text-[#8b949e]">
            L <span className={currentOhlc.isUp ? 'text-[#26a69a]' : 'text-[#ef5350]'}>{currentOhlc.low.toLocaleString()}</span>
          </span>
          <span className="text-[#8b949e]">
            C <span className={currentOhlc.isUp ? 'text-[#26a69a]' : 'text-[#ef5350]'}>{currentOhlc.close.toLocaleString()}</span>
          </span>
          <span className={`font-bold ${currentOhlc.isUp ? 'text-[#26a69a]' : 'text-[#ef5350]'}`}>
            {currentOhlc.isUp ? '+' : ''}{currentOhlc.change.toFixed(1)} ({currentOhlc.isUp ? '+' : ''}{currentOhlc.changePct.toFixed(2)}%)
          </span>
        </div>

        {/* Legend Tag for EMA 120 (from Image 1) */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#1f6feb]/15 border border-[#1f6feb]/40 text-[#58a6ff] text-[11px]">
            <span className="h-2 w-2 rounded-full bg-[#2962FF]" />
            <span className="font-semibold">EMA 120 close 0</span>
            <span className="font-bold text-white">${displayEma.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 })}</span>
            <button onClick={() => setShowEma(!showEma)} className="text-[#8b949e] hover:text-white ml-1">
              <Eye className="h-3 w-3" />
            </button>
          </div>
        </div>
      </div>

      {/* 3. CHART CANVAS CONTAINER + FLOATING QUICK TRADE BUTTONS (Matching Image 1) */}
      <div className="relative w-full">
        {/* Floating Sell/Buy Quote Box (Top-Left of chart canvas, like Image 1) */}
        <div className="absolute top-3 left-4 z-20 flex items-center shadow-2xl rounded-lg overflow-hidden border border-[#30363d]/80 bg-[#161b22]/90 backdrop-blur-sm select-none font-mono">
          {/* SELL BUTTON (Red) */}
          <button className="px-3 py-1.5 bg-[#ef5350] hover:bg-[#d32f2f] text-white flex flex-col items-center leading-none transition">
            <span className="text-xs font-black">{bidPrice}</span>
            <span className="text-[9px] uppercase font-bold tracking-wider mt-0.5">SELL</span>
          </button>

          {/* SPREAD & SIZE INDICATOR */}
          <div className="px-2.5 py-1 flex flex-col items-center justify-center bg-[#0d1117] text-[#8b949e] border-x border-[#30363d]">
            <span className="text-[10px] font-bold text-white">{spread}</span>
            <span className="text-[9px] text-[#58a6ff] font-bold">
              {liveTicker?.ask_size ? Math.max(1, Math.round(liveTicker.ask_size / 500)) : '3'}
            </span>
          </div>

          {/* BUY BUTTON (Blue) */}
          <button className="px-3 py-1.5 bg-[#2962FF] hover:bg-[#1e50e2] text-white flex flex-col items-center leading-none transition">
            <span className="text-xs font-black">{askPrice}</span>
            <span className="text-[9px] uppercase font-bold tracking-wider mt-0.5">BUY</span>
          </button>
        </div>

        {/* TradingView Lightweight Chart Container */}
        <div ref={chartContainerRef} className="w-full h-[480px]" />
      </div>
    </div>
  );
};
