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

import pandas as pd
import yfinance as yf

from logging_config import get_logger

logger = get_logger(__name__)


def get_from_yahoo(symbol: str, period: str) -> pd.DataFrame:
	"""
	Download daily OHLCV for ``symbol`` from Yahoo Finance over ``period``.
	Raises RuntimeError if no rows are returned, or if the latest row contains NaNs
	(Yahoo sometimes returns an incomplete last bar).
	"""
	df = yf.download(
		symbol,
		period=period,
		interval="1d",
		progress=False,
		group_by="column",
		auto_adjust=True,
		actions=False,
	)
	logger.debug("%s DataFrame: %s", symbol, df)
	if df is None or df.empty:
		raise RuntimeError(f"No data returned from yfinance for {symbol}")
	# Remove symbol from index
	df.columns = df.columns.droplevel(1)
	# Check if the latest row contains NaNs
	last = df.iloc[-1]
	nan_cols = last.index[last.isna()].tolist()
	if nan_cols:
		raise RuntimeError(
			f"Incomplete last row from yfinance for {symbol} at {last}"
		) 
	return df
