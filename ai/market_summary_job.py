from __future__ import annotations

import asyncio
import datetime as dt

import numpy as np
import pandas as pd
import yfinance as yf
from sqlalchemy import delete
from ta.momentum import RSIIndicator
from ta.trend import ADXIndicator, EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands

import fear_and_greed

from ai.prompts import SYSTEM_PROMPT
from ai.service import AIService
from db.models import AiResponseModel, HistoricalDataModel
from db.session import AsyncSessionLocal
from logging_config import get_logger
from telegram_notifier import market_summary_notifier_from_env
from utils import (
	_last_starts_falling_date,
	_last_starts_rising_date,
	_last_cross_date_level,
	_last_cross_event,
	_only_latest_date_among,
	_safe_pct_distance,
	coerce_ohlcv,
	event_to_dates,
	get_latest_and_prev_close,
)

logger = get_logger(__name__)


def _build_market_state() -> tuple[dict, pd.DataFrame]:
	symbols_to_download = ["^GSPC", "^VVIX", "^VIX", "^VIX3M"]
	df = yf.download(
		symbols_to_download,
		period="3y",
		interval="1d",
		progress=False,
		group_by="ticker",
		auto_adjust=True,
		actions=False,
	)

	if df is None or df.empty:
		raise RuntimeError("No data returned from yfinance")

	spx_df = coerce_ohlcv(df["^GSPC"])
	vix_df = coerce_ohlcv(df["^VIX"])
	vix3m_df = coerce_ohlcv(df["^VIX3M"])
	vvix_df = coerce_ohlcv(df["^VVIX"])

	close_s = spx_df["Close"].astype(float)
	high_s = spx_df["High"].astype(float)
	low_s = spx_df["Low"].astype(float)

	ema20 = EMAIndicator(close=close_s, window=20, fillna=False).ema_indicator()
	sma50 = SMAIndicator(close=close_s, window=50, fillna=False).sma_indicator()
	sma200 = SMAIndicator(close=close_s, window=200, fillna=False).sma_indicator()
	rsi = RSIIndicator(close=close_s, window=14, fillna=False).rsi()

	bb = BollingerBands(close=close_s, window=20, window_dev=2, fillna=False)
	bb_pc = bb.bollinger_pband()

	adx_i = ADXIndicator(high=high_s, low=low_s, close=close_s, window=14, fillna=False)
	adx = adx_i.adx()
	dmip = adx_i.adx_pos()
	dmim = adx_i.adx_neg()

	indicator_df = pd.DataFrame(
		{
			"open": spx_df["Open"].astype(float),
			"high": high_s,
			"low": low_s,
			"close": close_s,
			"volume": spx_df["Volume"].astype(float) if "Volume" in spx_df.columns else np.nan,
			"ema20": ema20,
			"sma50": sma50,
			"sma200": sma200,
			"rsi": rsi,
			"bb_pc": bb_pc,
			"adx": adx,
			"dmip": dmip,
			"dmim": dmim,
		},
		index=spx_df.index,
	)

	# Keep only complete bars while preserving full available history.
	historical_df = indicator_df.dropna(subset=["open", "high", "low", "close"]).copy()
	state_df = indicator_df.dropna(subset=["close", "ema20", "sma50", "sma200"]).copy()
	if len(state_df) < 2:
		raise RuntimeError(f"Not enough datapoints to compute indicators for ^GSPC (got {len(state_df)})")

	latest = state_df.iloc[-1]
	prev = state_df.iloc[-2]

	price = float(latest["close"])
	price_prev = float(prev["close"])

	if "Open" in spx_df.columns:
		today_open = float(spx_df["Open"].iloc[-1])
		yesterday_close_for_gap = float(spx_df["Close"].iloc[-2])
		gap_percent = _safe_pct_distance(today_open, yesterday_close_for_gap)
	else:
		gap_percent = None

	ema20_v = float(latest["ema20"])
	sma50_v = float(latest["sma50"])
	sma200_v = float(latest["sma200"])

	slope_window = min(5, len(state_df))
	x = np.arange(slope_window, dtype=float)
	ema20_slope = float(np.polyfit(x, state_df["ema20"].iloc[-slope_window:].to_numpy(dtype=float), 1)[0])
	sma50_slope = float(np.polyfit(x, state_df["sma50"].iloc[-slope_window:].to_numpy(dtype=float), 1)[0])
	sma200_slope = float(np.polyfit(x, state_df["sma200"].iloc[-slope_window:].to_numpy(dtype=float), 1)[0])
	adx_slope = float(np.polyfit(x, state_df["adx"].iloc[-slope_window:].to_numpy(dtype=float), 1)[0])
	dmip_slope = float(np.polyfit(x, state_df["dmip"].iloc[-slope_window:].to_numpy(dtype=float), 1)[0])
	dmim_slope = float(np.polyfit(x, state_df["dmim"].iloc[-slope_window:].to_numpy(dtype=float), 1)[0])
	rsi_slope = float(np.polyfit(x, state_df["rsi"].iloc[-slope_window:].to_numpy(dtype=float), 1)[0])

	today_change_percent = _safe_pct_distance(price, price_prev)

	close_values = state_df["close"].to_numpy(dtype=float)
	ema20_values = state_df["ema20"].to_numpy(dtype=float)
	sma50_values = state_df["sma50"].to_numpy(dtype=float)
	sma200_values = state_df["sma200"].to_numpy(dtype=float)
	index_values = state_df.index

	price_ema20_above, price_ema20_below = event_to_dates(_last_cross_event(index_values, close_values, ema20_values))
	price_sma50_above, price_sma50_below = event_to_dates(_last_cross_event(index_values, close_values, sma50_values))
	price_sma200_above, price_sma200_below = event_to_dates(_last_cross_event(index_values, close_values, sma200_values))
	ema20_sma50_above, ema20_sma50_below = event_to_dates(_last_cross_event(index_values, ema20_values, sma50_values))
	ema20_sma200_above, ema20_sma200_below = event_to_dates(_last_cross_event(index_values, ema20_values, sma200_values))
	sma50_sma200_above, sma50_sma200_below = event_to_dates(_last_cross_event(index_values, sma50_values, sma200_values))

	rsi_values = state_df["rsi"].to_numpy(dtype=float)
	adx_values = state_df["adx"].to_numpy(dtype=float)
	rsi_level_dates = _only_latest_date_among(
		{
			"rsi_crossed_below_30": _last_cross_date_level(index_values, rsi_values, 30.0, "below"),
			"rsi_crossed_above_30": _last_cross_date_level(index_values, rsi_values, 30.0, "above"),
			"rsi_crossed_above_70": _last_cross_date_level(index_values, rsi_values, 70.0, "above"),
			"rsi_crossed_below_70": _last_cross_date_level(index_values, rsi_values, 70.0, "below"),
		}
	)
	adx_trend_dates = _only_latest_date_among(
		{
			"adx_started_rising": _last_starts_rising_date(index_values, adx_values),
			"adx_started_falling": _last_starts_falling_date(index_values, adx_values),
		}
	)

	adx_latest = latest["adx"]
	dmip_latest = latest["dmip"]
	dmim_latest = latest["dmim"]
	rsi_latest = latest["rsi"]
	adx_prev = prev["adx"]
	rsi_prev = prev["rsi"]

	spx_state = {
		"symbol": "SPX",
		"timestamp": str(latest.name),
		"open": latest["open"],
		"high": latest["high"],
		"low": latest["low"],
		"close": latest["close"],
		"ema20": ema20_v,
		"sma50": sma50_v,
		"sma200": sma200_v,
		"rsi": None if pd.isna(rsi_latest) else float(rsi_latest),
		"rsi_slope": rsi_slope,
		"rsi_change": None
		if pd.isna(rsi_latest) or pd.isna(rsi_prev)
		else float(rsi_latest) - float(rsi_prev),
		"rsi_crossed_below_30": rsi_level_dates["rsi_crossed_below_30"],
		"rsi_crossed_above_30": rsi_level_dates["rsi_crossed_above_30"],
		"rsi_crossed_above_70": rsi_level_dates["rsi_crossed_above_70"],
		"rsi_crossed_below_70": rsi_level_dates["rsi_crossed_below_70"],
		"adx": None if pd.isna(adx_latest) else float(adx_latest),
		"dmip": None if pd.isna(dmip_latest) else float(dmip_latest),
		"dmim": None if pd.isna(dmim_latest) else float(dmim_latest),
		"adx_slope": adx_slope,
		"dmip_slope": dmip_slope,
		"dmim_slope": dmim_slope,
		"adx_change": None if pd.isna(adx_latest) or pd.isna(adx_prev) else float(adx_latest) - float(adx_prev),
		"adx_started_rising": adx_trend_dates["adx_started_rising"],
		"adx_started_falling": adx_trend_dates["adx_started_falling"],
		"ema20_slope": ema20_slope,
		"sma50_slope": sma50_slope,
		"sma200_slope": sma200_slope,
		"gap_percent": gap_percent,
		"today_change_percent": today_change_percent,
		"last_day_percentage_change": today_change_percent,
		"pct_distance_from_ema20": _safe_pct_distance(price, ema20_v),
		"pct_distance_from_sma50": _safe_pct_distance(price, sma50_v),
		"pct_distance_from_sma200": _safe_pct_distance(price, sma200_v),
		"price_crossed_above_ema20": price_ema20_above,
		"price_crossed_below_ema20": price_ema20_below,
		"price_crossed_above_sma50": price_sma50_above,
		"price_crossed_below_sma50": price_sma50_below,
		"price_crossed_above_sma200": price_sma200_above,
		"price_crossed_below_sma200": price_sma200_below,
		"ema20_crossed_above_sma50": ema20_sma50_above,
		"ema20_crossed_below_sma50": ema20_sma50_below,
		"ema20_crossed_above_sma200": ema20_sma200_above,
		"ema20_crossed_below_sma200": ema20_sma200_below,
		"sma50_crossed_above_sma200": sma50_sma200_above,
		"sma50_crossed_below_sma200": sma50_sma200_below,
	}

	vix_latest_s, vix_prev_s, vix_ts = get_latest_and_prev_close(vix_df)
	vix3m_latest_s, _vix3m_prev_s, _vix3m_ts = get_latest_and_prev_close(vix3m_df)
	vvix_latest_s, vvix_prev_s, _vvix_ts = get_latest_and_prev_close(vvix_df)

	vix_latest = float(vix_latest_s)
	vix_prev = float(vix_prev_s)
	vix3m_latest = float(vix3m_latest_s)
	vvix_latest = float(vvix_latest_s)
	vvix_prev = float(vvix_prev_s)

	vix_state = {
		"symbol": "VIX",
		"timestamp": str(vix_ts),
		"vix": vix_latest,
		"vix3m": vix3m_latest,
		"vvix": vvix_latest,
		"vix_vix3m": (vix_latest / vix3m_latest) if vix3m_latest != 0.0 else None,
		"vix_change": vix_latest - vix_prev,
		"vix_pct_change": _safe_pct_distance(vix_latest, vix_prev),
		"vvix_change": vvix_latest - vvix_prev,
		"vvix_pct_change": _safe_pct_distance(vvix_latest, vvix_prev),
	}

	# Fear and Greed Index
	fear_and_greed_index: dict | None = None
	try:
		fgi = fear_and_greed.get()
		fear_and_greed_index = {
			"value": float(fgi.value),
			"description": fgi.description,
			"last_update": fgi.last_update.replace(tzinfo=None).isoformat(),
		}
	except Exception as e:
		logger.error("Error getting Fear and Greed Index: %s", e)
		fear_and_greed_index = None

	return {
		"SPX": spx_state,
		"VIX": vix_state,
		"Fear and Greed Index": fear_and_greed_index,
	}, historical_df


async def run_market_summary_job_once() -> None:
	await build_market_summary(persist_to_db=True, send_telegram_notifications=True)


async def build_market_summary(
	persist_to_db: bool = True,
	send_telegram_notifications: bool = False,
) -> tuple[dict, dict]:
	"""
	Shared pipeline used by both the app scheduler and test script.
	Returns market_state and AI decision dict.
	"""
	logger.info(
		"Building market summary (persist_to_db=%s, send_telegram=%s)",
		persist_to_db,
		send_telegram_notifications,
	)
	market_state, historical_df = _build_market_state()
	ai = AIService()
	decision = await ai.evaluate_market_state(market_state)

	if send_telegram_notifications:
		notifier = market_summary_notifier_from_env()
		if notifier is not None:
			await notifier.send_market_summary(
				summary=decision.summary,
				score=decision.score,
				confidence=decision.confidence,
			)
		else:
			logger.info("Telegram notification skipped: bot token or chat id not configured")

	if persist_to_db:
		async with AsyncSessionLocal() as session:
			await session.execute(delete(HistoricalDataModel))
			for idx, row in historical_df.iterrows():
				date_value = idx.date() if isinstance(idx, (pd.Timestamp, dt.datetime)) else idx
				session.add(
					HistoricalDataModel(
						date=date_value,
						open=float(row["open"]),
						high=float(row["high"]),
						low=float(row["low"]),
						close=float(row["close"]),
						volume=None if pd.isna(row["volume"]) else float(row["volume"]),
						ema_20=None if pd.isna(row["ema20"]) else float(row["ema20"]),
						sma_50=None if pd.isna(row["sma50"]) else float(row["sma50"]),
						sma_200=None if pd.isna(row["sma200"]) else float(row["sma200"]),
						rsi=None if pd.isna(row["rsi"]) else float(row["rsi"]),
						bb_pc=None if pd.isna(row["bb_pc"]) else float(row["bb_pc"]),
						adx=None if pd.isna(row["adx"]) else float(row["adx"]),
						dmip=None if pd.isna(row["dmip"]) else float(row["dmip"]),
						dmim=None if pd.isna(row["dmim"]) else float(row["dmim"]),
					)
				)

			session.add(
				AiResponseModel(
					timestamp=dt.datetime.utcnow(),
					prompt=SYSTEM_PROMPT,
					data=market_state,
					response=decision.summary,
					confidence=decision.confidence,
					score=decision.score,
				)
			)
			await session.commit()
		logger.info("Persisted historical data and AI response to database")

	return market_state, {
		"summary": decision.summary,
		"confidence": decision.confidence,
		"score": decision.score,
	}


def _seconds_until_next_run(run_times_utc: list[tuple[int, int]]) -> float:
	now = dt.datetime.now(dt.timezone.utc)
	next_runs = [
		now.replace(hour=hour_utc, minute=minute_utc, second=0, microsecond=0)
		for hour_utc, minute_utc in run_times_utc
	]
	future_runs = [run for run in next_runs if run > now]
	next_run = min(future_runs) if future_runs else min(next_runs) + dt.timedelta(days=1)
	return (next_run - now).total_seconds()


async def run_daily_market_summary_scheduler(stop_event: asyncio.Event) -> None:
	run_times_utc = [(18, 0), (23, 0)]

	while not stop_event.is_set():
		sleep_seconds = _seconds_until_next_run(run_times_utc)
		logger.info("Next daily market summary run in %.0f seconds", sleep_seconds)

		try:
			await asyncio.wait_for(stop_event.wait(), timeout=sleep_seconds)
			break
		except asyncio.TimeoutError:
			pass

		try:
			await run_market_summary_job_once()
		except Exception as exc:
			logger.exception("Daily market summary job failed: %s", exc)
