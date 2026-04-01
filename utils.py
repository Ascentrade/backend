"""
 @copyright Copyright (C) 2026 Dennis Einloft <dev@greguhn.de>
 
 @author Dennis Einloft <dev@greguhn.de>
 
 @license AGPL-3.0-or-later
 
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as
 published by the Free Software Foundation, either version 3 of the
 License, or (at your option) any later version.
 
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.
 
 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import annotations
from typing import Any
import os
import math
import pandas as pd


def get_bool_env(key: str, default: bool = False) -> bool:
	"""
	Parse a boolean value from an environment variable.
	
	Accepts case-insensitive values:
	- True: "1", "t", "T", "true", "True", "TRUE"
	- False: "0", "f", "F", "false", "False", "FALSE"
	
	Args:
		key: The environment variable key
		default: Default value if the key is not set or value is invalid
		
	Returns:
		The parsed boolean value
	"""
	value = os.environ.get(key, "").strip().lower()
	
	if value in ("1", "t", "true"):
		return True
	elif value in ("0", "f", "false"):
		return False
	else:
		return default


def _safe_pct_distance(price: float, ma: float) -> float:
	# Avoid division by zero; return 0 if MA is invalid.
	if ma == 0:
		return 0.0
	return ((price - ma) / ma) * 100.0


def coerce_ohlcv(d):
	out = d.copy()
	for col in ("Open", "High", "Low", "Close", "Adj Close", "Volume"):
		if col in out.columns:
			out[col] = pd.to_numeric(out[col], errors="coerce")
	return out


def get_latest_and_prev_close(sym_df):
	if "Adj Close" in sym_df.columns:
		close_s = sym_df["Adj Close"].astype(float)
	elif "Close" in sym_df.columns:
		close_s = sym_df["Close"].astype(float)
	else:
		raise RuntimeError("Dataframe missing both 'Adj Close' and 'Close'")

	close_s = close_s.dropna()
	if len(close_s) < 2:
		raise RuntimeError(f"Not enough datapoints to compute close change (got {len(close_s)})")

	latest_ts = close_s.index[-1]
	return close_s.iloc[-1], close_s.iloc[-2], latest_ts


def event_to_dates(event: tuple[str, str] | None) -> tuple[str | None, str | None]:
	if event is None:
		return None, None
	kind, dt = event
	return (dt, None) if kind == "above" else (None, dt)


def _crossed_above(prev_price: float, prev_ma: float, price: float, ma: float) -> bool:
	return prev_price <= prev_ma and price > ma


def _crossed_below(prev_price: float, prev_ma: float, price: float, ma: float) -> bool:
	return prev_price >= prev_ma and price < ma


def _last_cross_date(
	index: Any,
	close_values: Any,
	ma_values: Any,
	kind: str,
) -> str | None:
	"""
	Return the index value (as string) where `close` last crossed the MA.

	kind:
	- 'above' => close crosses above MA
	- 'below' => close crosses below MA
	"""

	last_date = None
	for i in range(1, len(close_values)):
		prev_close = float(close_values[i - 1])
		prev_ma = float(ma_values[i - 1])
		curr_close = float(close_values[i])
		curr_ma = float(ma_values[i])

		if kind == "above":
			crossed = _crossed_above(prev_close, prev_ma, curr_close, curr_ma)
		elif kind == "below":
			crossed = _crossed_below(prev_close, prev_ma, curr_close, curr_ma)
		else:
			raise ValueError("kind must be 'above' or 'below'")

		if crossed:
			last_date = index[i]

	return str(last_date) if last_date is not None else None


def _last_cross_date_between(
	index: Any,
	a_values: Any,
	b_values: Any,
	kind: str,
) -> str | None:
	"""
	Return the index value (as string) where `a` last crossed `b`.

	kind:
	- 'above' => a crosses above b
	- 'below' => a crosses below b
	"""

	last_date = None
	for i in range(1, len(a_values)):
		prev_a = float(a_values[i - 1])
		prev_b = float(b_values[i - 1])
		curr_a = float(a_values[i])
		curr_b = float(b_values[i])

		if kind == "above":
			crossed = _crossed_above(prev_a, prev_b, curr_a, curr_b)
		elif kind == "below":
			crossed = _crossed_below(prev_a, prev_b, curr_a, curr_b)
		else:
			raise ValueError("kind must be 'above' or 'below'")

		if crossed:
			last_date = index[i]

	return str(last_date) if last_date is not None else None


def _last_cross_event(
	index: Any,
	a_values: Any,
	b_values: Any,
) -> tuple[str, str] | None:
	"""
	Return the most recent crossing event between series `a` and `b`.

	- If `a` crossed above `b` most recently => ('above', <date_str>)
	- If `a` crossed below `b` most recently => ('below', <date_str>)
	- If no crossing event exists => None
	"""

	last_kind: str | None = None
	last_date = None

	for i in range(1, len(a_values)):
		prev_a = float(a_values[i - 1])
		prev_b = float(b_values[i - 1])
		curr_a = float(a_values[i])
		curr_b = float(b_values[i])

		if _crossed_above(prev_a, prev_b, curr_a, curr_b):
			last_kind = "above"
			last_date = index[i]
		elif _crossed_below(prev_a, prev_b, curr_a, curr_b):
			last_kind = "below"
			last_date = index[i]

	if last_kind is None or last_date is None:
		return None

	return last_kind, str(last_date)


def _last_cross_date_level(index: Any, values: Any, level: float, kind: str) -> str | None:
	"""Last date `values` crossed above or below a constant horizontal `level`."""

	last_date = None
	for i in range(1, len(values)):
		prev_a = float(values[i - 1])
		curr_a = float(values[i])
		if math.isnan(prev_a) or math.isnan(curr_a):
			continue
		if kind == "above":
			crossed = _crossed_above(prev_a, level, curr_a, level)
		elif kind == "below":
			crossed = _crossed_below(prev_a, level, curr_a, level)
		else:
			raise ValueError("kind must be 'above' or 'below'")
		if crossed:
			last_date = index[i]
	return str(last_date) if last_date is not None else None


def _last_starts_rising_date(index: Any, values: Any) -> str | None:
	"""Most recent bar where `values` pivots from flat/down into rising (trough at i-1)."""

	last_date = None
	for i in range(2, len(values)):
		p0 = float(values[i - 2])
		p1 = float(values[i - 1])
		p2 = float(values[i])
		if math.isnan(p0) or math.isnan(p1) or math.isnan(p2):
			continue
		if p1 <= p0 and p2 > p1:
			last_date = index[i]
	return str(last_date) if last_date is not None else None


def _last_starts_falling_date(index: Any, values: Any) -> str | None:
	"""Most recent bar where `values` pivots from flat/up into falling (peak at i-1)."""

	last_date = None
	for i in range(2, len(values)):
		p0 = float(values[i - 2])
		p1 = float(values[i - 1])
		p2 = float(values[i])
		if math.isnan(p0) or math.isnan(p1) or math.isnan(p2):
			continue
		if p1 >= p0 and p2 < p1:
			last_date = index[i]
	return str(last_date) if last_date is not None else None


def _only_latest_date_among(dates_by_key: dict[str, str | None]) -> dict[str, str | None]:
	"""Keep only the chronologically latest non-null date; set all other keys to None."""

	out = {k: None for k in dates_by_key}
	present = {k: v for k, v in dates_by_key.items() if v is not None}
	if not present:
		return out
	winner = max(present, key=lambda k: pd.Timestamp(present[k]))
	out[winner] = present[winner]
	return out

