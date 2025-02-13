"""
 @copyright Copyright (C) 2024 Dennis Greguhn <dev@greguhn.de>
 
 @author Dennis Greguhn <dev@greguhn.de>
 
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

import numpy as np
import pandas as pd
from decimal import Decimal

from log_config import logger


def SimpleMovingAverage(df:pd.DataFrame, period:Decimal, source:str='adjusted_close') -> tuple[bool, pd.DataFrame, list[str]]:
	"""Simple Moving Average (SMA) Indicator

	Args:
		df (pd.DataFrame): Pandas DataFrame with historical quotes.
		period (int): Period of N elements to use.
		source (str, optional): Source data to use (defaults to **adjusted_close**) 

	Returns:
		tuple[bool, pd.DataFrame, list[str]]: True/False if success, Output DataFrame with column **sma** and **rising** added, column names added to DataFrame.
	"""
	keys = ['sma', 'rising']
	try:
		N = int(period)
		if len(df) > N:
			df['sma'] = df[source].rolling(N).mean()
			df['rising'] = df['sma'].pct_change(fill_method=None) > 0.0
		else:
			for k in keys:
				df[k] = None
		return True, df, keys
	except Exception as e:
		logger.error(f'Error while calculating indicator "SimpleMovingAverage"')
		logger.error(e)
		for k in keys:
			df[k] = None
	return False, df, keys


def ExponentialMovingAverage(df:pd.DataFrame, period:Decimal, source:str='adjusted_close') -> tuple[bool, pd.DataFrame, list[str]]:
	"""Exponential Moving Average (EMA) Indicator

	Args:
		df (pd.DataFrame): Pandas DataFrame with historical quotes.
		period (int): Period of N elements to use.
		source (str, optional): Source data to use (defaults to **adjusted_close**) 

	Returns:
		tuple[bool, pd.DataFrame, list[str]]: True/False if success, Output DataFrame with column **ema** and **rising** added, column names added to DataFrame.
	"""
	keys = ['ema', 'rising']
	try:
		N = int(period)
		if len(df) > N:
			df['ema'] = df[source].ewm(span=period, adjust=False).mean()
			df['rising'] = df['ema'].pct_change(fill_method=None) > 0.0
		else:
			for k in keys:
				df[k] = None
		return True, df, keys
	except Exception as e:
		logger.error(f'Error while calculating indicator "ExponentialMovingAverage"')
		logger.error(e)
		for k in keys:
			df[k] = None
	return False, df, keys


def BollingerBands(df:pd.DataFrame, period:Decimal=Decimal(20), std:Decimal=Decimal(2), source:str='adjusted_close') -> tuple[bool, pd.DataFrame, list[str]]:
	"""Bollinger Bands (BB), Simple Moving Average (SMA) and Bollinger %B

	Args:
		df (pd.DataFrame): Pandas DataFrame with historical quotes.
		period (Decimal): Period of N elements to use.
		std (Decimal): Standard Deviations for Bollinger Bands
		source (str, optional): Source data to use (defaults to **adjusted_close**) 

	Returns:
		tuple[bool, pd.DataFrame]: True/False if success, Output DataFrame with columns **sma**, **bb_upper**, **bb_lower**, **bb_pc** and **bb_expanding** added, List of column names added to the DataFrame.
	"""
	keys = ['sma', 'bb_upper', 'bb_lower', 'bb_pc', 'bb_expanding']
	try:
		N = int(period)
		stdev = float(std)
		if len(df) > N:
			df['std'] = df[source].rolling(N).std(ddof=0)
			df['sma'] = df[source].rolling(N).mean()
			df['bb_upper'] = df['sma'] + stdev * df['std']
			df['bb_lower'] = df['sma'] - stdev * df['std']
			# Expanding
			df['bb_expanding'] = df['std'].pct_change(fill_method=None) > 0.0
			# Calculate symmetric %B
			df['bb_pc'] = (df[source].astype(float) - df['sma']) / df['std']
			# Cleanup DataFrame
			df = df.drop('std', axis=1)
		else:
			for k in keys:
				df[k] = None
		return True, df, keys
	except Exception as e:
		logger.error(f'Error while calculating indicator "BollingerBands"')
		logger.error(e)
		for k in keys:
			df[k] = None
	return False, df, keys


def RSI(df:pd.DataFrame, period:Decimal=Decimal(14), source:str='close') -> tuple[bool, pd.DataFrame, list[str]]:
	"""Relative Strength Index (RSI)

	Args:
		df (pd.DataFrame): Pandas DataFrame with historical quotes.
		period (Decimal, optional): RSI period. Defaults to Decimal(14).
		source (str, optional): Source for RSI calculation. Defaults to 'close'.

	Returns:
		tuple[bool, pd.DataFrame]: True/False if success, Output DataFrame with columns **rsi** added, List of column names added to the DataFrame.
	"""
	try:
		N = int(period)
		if len(df) > N:
			df['change'] = df[source].diff()
			df['gain'] = df.change.mask(df.change < 0, 0.0)
			df['loss'] = -df.change.mask(df.change > 0, -0.0)

			def rma(x, n):
				a = np.full_like(x, np.nan)
				a[n] = x[1:n+1].mean()
				for i in range(n+1, len(x)):
					a[i] = (a[i-1] * (n - 1) + x[i]) / n
				return a

			df['avg_gain'] = rma(df.gain.to_numpy(), N)
			df['avg_loss'] = rma(df.loss.to_numpy(), N)

			df['rs'] = df.avg_gain / df.avg_loss
			df['rsi'] = 100 - (100 / (1 + df.rs))

			del df['change']
			del df['gain']
			del df['loss']
			del df['avg_gain']
			del df['avg_loss']
			del df['rs']
		else:
			df['rsi'] = None
		return True, df, ['rsi']

	except Exception as e:
		logger.error(f'Error while calculating indicator "RSI"')
		logger.error(e)
		df['rsi'] = None
	return False, df, ['rsi']


def ADXDMI(df:pd.DataFrame, period:Decimal=Decimal(14)) -> tuple[bool, pd.DataFrame, list[str]]:
	"""ADX/DMI Indicator

	Args:
		df (pd.DataFrame): Pandas DataFrame with historical quotes.
		period (Decimal): Period of N elements to use (defaults to 14)

	Returns:
		tuple[bool, pd.DataFrame]: True/False if success, Output DataFrame with columns **dmi_p**, **dmi_m**, **adx**, **adx_crossing_date** and **dmi_crossing_date** added, List of column names added to the DataFrame.
	"""
	keys = ['dmi_p', 'dmi_m', 'dmi_bull', 'adx', 'adx_crossing_date', 'dmi_crossing_date']
	try:
		alpha = float(1/period)
		# True Range
		df['H-L'] = df['high'] - df['low']
		df['H-C'] = np.abs(df['high'] - df['close'].shift(1))
		df['L-C'] = np.abs(df['low'] - df['close'].shift(1))
		df['TR'] = df[['H-L', 'H-C', 'L-C']].max(axis=1)
		del df['H-L'], df['H-C'], df['L-C']
		# Average True Range
		df['ATR'] = df['TR'].ewm(alpha=alpha, adjust=False).mean()
		# +-DX
		df['H-pH'] = df['high'] - df['high'].shift(1)
		df['pL-L'] = df['low'].shift(1) - df['low']
		df['+DX'] = np.where(
			(df['H-pH'] > df['pL-L']) & (df['H-pH']>0),
			df['H-pH'],
			0.0
		)
		df['-DX'] = np.where(
			(df['H-pH'] < df['pL-L']) & (df['pL-L']>0),
			df['pL-L'],
			0.0
		)
		# +- DMI
		df['S+DM'] = df['+DX'].ewm(alpha=alpha, adjust=False).mean()
		df['S-DM'] = df['-DX'].ewm(alpha=alpha, adjust=False).mean()
		df['dmi_p'] = (df['S+DM']/df['ATR'])*100
		df['dmi_m'] = (df['S-DM']/df['ATR'])*100
		# ADX
		df['DX'] = (np.abs(df['dmi_p'] - df['dmi_m'])/(df['dmi_p'] + df['dmi_m']))*100
		df['adx'] = df['DX'].ewm(alpha=alpha, adjust=False).mean()
		df['dmi_bull'] = df['dmi_p'] > df['dmi_m']
		# Remove temporary columns
		df = df.drop(['H-pH','pL-L','S+DM','S-DM','DX','ATR','TR','-DX','+DX'], axis=1)

		# Calculate last change date
		df['adx_crossing_date'] = None
		df['dmi_crossing_date'] = None
		first = True
		search = None
		dmiFound = False
		adxFound = False
		valueBefore = None
		for i, value in df.sort_index(ascending=False).iterrows():
			if first == True:
				search = value['dmi_bull']
				first = False
			else:
				# Find last DMI crossing
				if value['dmi_bull'] is not search and dmiFound == False:
					df.loc[df.index[-1], 'dmi_crossing_date'] = valueBefore['date']
					dmiFound = True
					# Stop to search for ADX crossing after DMI crossed
					if adxFound == False:
						break
				if adxFound == False:
					# Find ADX crossing
					if value['dmi_bull'] == True:
						# Bullish Golden Crossing
						if value['adx'] <= value['dmi_m'] and valueBefore['adx'] > valueBefore['dmi_m']:
							df.loc[df.index[-1], 'adx_crossing_date'] = valueBefore['date']
							adxFound = True
					else:
						# Bearish Golden Crossing
						if value['adx'] <= value['dmi_p'] and valueBefore['adx'] > valueBefore['dmi_p']:
							df.loc[df.index[-1], 'adx_crossing_date'] = valueBefore['date']
							adxFound = True
			if adxFound and dmiFound:
				break
			valueBefore = value
		return True, df, keys
	except Exception as e:
		logger.error(f'Error while calculating indicator "ADXDMI"')
		logger.error(e)
		for k in keys:
			df[k] = None
	return False, df, keys


def PSAR(df:pd.DataFrame, af:Decimal=Decimal('0.02'), max:Decimal=Decimal('0.2')) -> tuple[bool, pd.DataFrame, list[str]]:
	"""Parabolic Stop And Return Indicator

	Args:
		df (pd.DataFrame): Pandas DataFrame with historical quotes.
		af (Decimal, optional): Scaling factor. (Defaults to 0.02)
		max (Decimal, optional): Maximum factor. (Defaults to 0.2)

	Returns:
		tuple[bool, pd.DataFrame]: True/False if success, Output DataFrame with columns **psar**, **psar_bull** and **psar_change_date** added, List of column names added to the DataFrame.
	"""
	keys = ['psar', 'psar_bull', 'psar_change_date']
	try:
		df.loc[0, 'psar'] = df.loc[0, 'low']
		df['psar_bull'] = True
		df.loc[0, 'AF'] = float(af)
		df.loc[0, 'EP'] = df.loc[0, 'high']
		for a in range(1, len(df)):
			if df.loc[a-1, 'psar_bull'] == True:
				df.loc[a, 'psar'] = df.loc[a-1, 'psar'] + (df.loc[a-1, 'AF']*(df.loc[a-1, 'EP']-df.loc[a-1, 'psar']))
				df.loc[a, 'psar_bull'] = True
				if df.loc[a, 'low'] < df.loc[a-1, 'psar'] or df.loc[a, 'low'] < df.loc[a, 'psar']:
					df.loc[a, 'psar_bull'] = False
					df.loc[a, 'psar'] = df.loc[a-1, 'EP']
					df.loc[a, 'EP'] = df.loc[a-1, 'low']
					df.loc[a, 'AF'] = float(af)
				else:
					if df.loc[a, 'high'] > df.loc[a-1, 'EP']:
						df.loc[a, 'EP'] = df.loc[a, 'high']
						if df.loc[a-1, 'AF'] <= (float(max) - float(af)):
							df.loc[a, 'AF'] = df.loc[a-1, 'AF'] + float(af)
						else:
							df.loc[a, 'AF'] = df.loc[a-1, 'AF']
					elif df.loc[a, 'high'] <= df.loc[a-1, 'EP']:
						df.loc[a, 'AF'] = df.loc[a-1, 'AF']
						df.loc[a, 'EP'] = df.loc[a-1, 'EP']
			elif df.loc[a-1, 'psar_bull'] == False:
				df.loc[a, 'psar'] = df.loc[a-1, 'psar'] - (df.loc[a-1, 'AF']*(df.loc[a-1, 'psar']-df.loc[a-1, 'EP']))
				df.loc[a, 'psar_bull'] = False
				if df.loc[a, 'high'] > df.loc[a-1, 'psar'] or df.loc[a, 'high'] > df.loc[a, 'psar']:
					df.loc[a, 'psar_bull'] = True
					df.loc[a, 'psar'] = df.loc[a-1, 'EP']
					df.loc[a, 'EP'] = df.loc[a-1, 'high']
					df.loc[a, 'AF'] = float(af)
				else:
					if df.loc[a, 'low'] < df.loc[a-1, 'EP']:
						df.loc[a, 'EP'] = df.loc[a, 'low']
						if df.loc[a-1, 'AF'] < float(max):
							df.loc[a, 'AF'] = df.loc[a-1, 'AF'] + float(af)
						else:
							df.loc[a, 'AF'] = df.loc[a-1, 'AF']
					elif df.loc[a, 'low'] >= df.loc[a-1, 'EP']:
						df.loc[a, 'AF'] = df.loc[a-1, 'AF']
						df.loc[a, 'EP'] = df.loc[a-1, 'EP']
		# Remove temporary columns
		df = df.drop(['AF','EP'], axis=1)

		# Calculate last change date
		df['psar_change_date'] = None
		first = True
		search = None
		valueBefore = None
		for i, value in df.sort_index(ascending=False).iterrows():
			if first == True:
				search = value['psar_bull']
				first = False
			else:
				if value['psar_bull'] is not search:
					df.loc[df.index[-1], 'psar_change_date'] = valueBefore['date']
					#df['psar_change_date'] = valueBefore['date']
					break
			valueBefore = value

		return True, df, keys
	except Exception as e:
		logger.error(f'Error while calculating indicator "PSAR"')
		logger.error(e)
		for k in keys:
			df[k] = None
	return False, df, keys


def Slope(df:pd.DataFrame, source:str) -> tuple[bool, pd.DataFrame, list[str]]:
	"""Slope indicator

	Args:
		df (pd.DataFrame): Pandas DataFrame with historical quotes.
		source (str): Source data to use for slope calculation.

	Returns:
		tuple[bool, pd.DataFrame]: True/False if success, Output DataFrame with columns **slope**, List of column names added to the DataFrame.
	"""
	try:
		df['slope'] = df[source].diff() > 0
		return True, df, ['slope']
	except Exception as e:
		logger.error(f'Error while calculating indicator "Slope"')
		logger.error(e)
		df['slope'] = None
	return False, df, ['slope']


def Larger(df:pd.DataFrame, source1:str, source2:str) -> tuple[bool, pd.DataFrame, list[str]]:
	"""Larger indicator source1 > source2

	Args:
		df (pd.DataFrame): Pandas DataFrame with historical quotes.
		source1 (str): Source1 data to use for slope calculation.
		source2 (str): Source2 data to use for slope calculation.

	Returns:
		tuple[bool, pd.DataFrame]: True/False if success, Output DataFrame with columns **larger**, List of column names added to the DataFrame.
	"""
	try:
		df['larger'] = df[source1] > df[source2]
		return True, df, ['larger']
	except Exception as e:
		logger.error(f'Error while calculating indicator "Larger"')
		logger.error(e)
		df['larger'] = None
	return False, df, ['larger']


def HighLow(df:pd.DataFrame, interval:int, sourceHigh:str='high', sourceLow:str='low', sourcePercentage:str='close') -> tuple[bool, pd.DataFrame, list[str]]:
	"""High/Low of the last N elements

	Args:
		df (pd.DataFrame): Pandas DataFrame with historical quotes.
		interval (int): Number of how many elements to use for calculation.
		sourceHigh (str, optional): High source data to use for calculation. Defaults to 'high'.
		sourceLow (str, optional): Low source data to use for calculation. Defaults to 'low'.
		sourcePercentage (str, optional): Percentage (Close) source data to use for calculation of percentage distance to high/low. Defaults to 'close'.

	Returns:
		tuple[bool, pd.DataFrame]: True/False if success, Output DataFrame with columns **window_high**, **window_high_pc**, **window_low** and **window_low_pc**, List of column names added to the DataFrame.
	"""
	keys = ['window_high', 'window_high_pc', 'window_low', 'window_low_pc']
	try:
		df['window_high'] = df[sourceHigh].rolling(window=interval).max()
		df['window_high_pc'] = (df[sourcePercentage]/df['window_high'] - 1.0) * 100.0
		df['window_low'] = df[sourceLow].rolling(window=interval).min()
		df['window_low_pc'] = (df[sourcePercentage]/df['window_low'] - 1.0) * 100.0
		return True, df, keys
	except Exception as e:
		logger.error(f'Error while calculating indicator "HighLow"')
		logger.error(e)
		for k in keys:
			df[k] = None
	return False, df, keys


def CumulativeReturn(df:pd.DataFrame, interval:int, source:str='close') -> tuple[bool, pd.DataFrame, list[str]]:
	"""Cumulative percentage return of the last N days

	Args:
		df (pd.DataFrame): Pandas DataFrame with historical quotes.
		interval (int): Number of how many elements to use for calculation.
		source (str, optional): Source data to use for calculation. Defaults to 'close'.

	Returns:
		tuple[bool, pd.DataFrame]: True/False if success, Output DataFrame with columns **cum_return**, List of column names added to the DataFrame.
	"""
	keys = ['cum_return']
	try:
		df['logReturns'] = np.log(df[source]/df[source].shift(1))
		df['cumulative_return'] = df['logReturns'].rolling(window=interval).sum()
		del df['logReturns']
		return True, df, keys
	except Exception as e:
		logger.error(f'Error while calculating indicator "CumulativeReturn"')
		logger.error(e)
		for k in keys:
			df[k] = None
	return False, df, keys