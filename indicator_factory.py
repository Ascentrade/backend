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

import json
from enum import Enum
import logging
import os
from asyncpg import Pool
import psycopg2
from datetime import datetime
import multiprocessing

from indicators.indicators import *
# Add or overwrite base indicators with custom Python
try:
	from custom_indicators import *
except:
	pass

from log_config import getNewLogger
from logging import Logger

from database import DatabaseConnector


class Interval(Enum):
	"""Enum class to handle indicator intervals.
	"""
	DAILY = 0
	WEEKLY = 1
	MONTHLY = 2


@staticmethod
def intervalFromStr(input:str) -> Interval:
	"""Parser function for Interval Enum.

	Args:
		input (str): String to parse as Interval Enum.

	Raises:
		NotImplementedError: Unknown/not implemented interval.

	Returns:
		Interval: Parsed Interval Enum value.
	"""
	if input.lower() in ('d', 'day', 'daily'):
		return Interval.DAILY
	elif input.lower() in ('w', 'week', 'weekly'):
		return Interval.WEEKLY
	elif input.lower() in ('m', 'month', 'monthly'):
		return Interval.MONTHLY
	else:
		raise NotImplementedError


class IndicatorFactory():
	"""Class for automated calculation and storage of financial indicators.
	"""
	dbConnector:DatabaseConnector = None
	logger:Logger = None

	def __init__(self, dbConnector: DatabaseConnector, configFile:str='indicators.json'):
		self.logger = getNewLogger('IndicatorFactory')
		self.logger.info('IndicatorFactory.__init__()')

		self.dbConnector = dbConnector
		self.configFile = configFile

		try:
			with open(configFile, 'r') as f:
				self.config = json.loads(f.read())
		except Exception as e:
			self.logger.error(e)
			self.config = {
				'securities':[]
			}

	@staticmethod
	def resampleDataFrame(data:pd.DataFrame, interval:Interval) -> pd.DataFrame:
		"""Resample daily/weekly quotes to weekly/monthly candles.

		Args:
			data (pd.DataFrame): DataFrame to resample.
			interval (Interval): Interval Enum for resampling.

		Returns:
			pd.DataFrame: Resampled Pandas DataFrame.
		"""
		df = data.copy()
		if interval == Interval.WEEKLY or interval == Interval.MONTHLY:
			delta = '1W' if interval == Interval.WEEKLY else 'ME'
			df = df.resample(rule=delta, on='date').agg({
				'date': 'last',
				'open': 'first', 
				'high': 'max', 
				'low': 'min', 
				'close': 'last',
				'split_adjusted_open': 'first',
				'split_adjusted_high': 'max',
				'split_adjusted_low': 'min',
				'split_adjusted_close': 'last',
				'adjusted_close': 'last',
				'volume': 'sum'
			})
		df.index = range(len(df))
		return df

	@staticmethod
	def parseParameters(input:dict) -> dict:
		"""Parse indicators input parameters from JSON (string) to dict (Decimal).

		Args:
			input (dict): Input dict.

		Returns:
			dict: Dict with Decimal parsed values.
		"""
		output = {}
		for k in input.keys():
			if type(input[k]) == str:
				if input[k].isdecimal():
					output[k] = Decimal(input[k])
				else:
					output[k] = input[k]
			else:
				output[k] = input[k]
		return output

	async def calculate(self, id:int) -> bool:
		"""Function to calculate all specified indicators for a security.

		Args:
			id (int): Primary key (ID) of the security.

		Raises:
			e: Exception if any.

		Returns:
			bool: True/False of success.
		"""
		try:
			self.logger.debug(f'calculate(id={id})')
			rows = []
			async with self.dbConnector.dbPool.acquire() as con:
				# Get all historic quotes for this stock
				# Cast to double precision float for faster calculation
				rows = await con.fetch("""SELECT date,open::double precision,high::double precision,low::double precision,close::double precision,
						   					split_adjusted_open::double precision,split_adjusted_high::double precision,split_adjusted_low::double precision,
						   					split_adjusted_close::double precision,adjusted_close::double precision,volume
											FROM quotes WHERE security=$1 ORDER BY date ASC;""", id)
			# Convert to Pandas DataFrame
			dfDaily = pd.DataFrame([dict(row) for row in rows])

			if len(dfDaily) < 10:
				self.logger.info(f'Skip indicator calculation for ID: {id} (less data)')
				return True

			# Parse date string as date
			dfDaily['date'] = pd.to_datetime(dfDaily['date'])
			# Calculate weekly and monthly candles as well
			dfWeekly = self.resampleDataFrame(dfDaily, Interval.WEEKLY)
			dfMonthly = self.resampleDataFrame(dfDaily, Interval.MONTHLY)
			dfs = [dfDaily, dfWeekly, dfMonthly]

			# Calculate all configured indicators
			for obj in self.config['securities']:
				self.logger.debug(f'Calculate indicator {obj}')
				df:pd.DataFrame = dfs[intervalFromStr(obj['interval']).value]
				params = self.parseParameters(obj['parameters'])
				success, df, keys = globals()[obj['indicator']](df, **params)
				if success == True:
					# Drop keys which will not be mapped
					for k in keys:
						if k not in obj['mapping'].keys():
							df = df.drop([k], axis=1)
					df = df.rename(columns=obj['mapping'])
					dfs[intervalFromStr(obj['interval']).value] = df
				else:
					self.logger.warning(f'Calculating indicator {obj} was not successful')

			# Cleanup and merge DataFrame objects as dict
			data = dict()
			date = datetime.strptime(np.datetime_as_string(dfs[0]['date'].values[-1], unit='D'), '%Y-%m-%d').date()
			for i in range(0, len(dfs)):
				dfs[i] = dfs[i].drop(['date','open','high','low','close','split_adjusted_open','split_adjusted_high','split_adjusted_low','split_adjusted_close','adjusted_close','volume'], axis=1)
				dfs[i] = dfs[i].replace({np.nan: None})
				data.update(dfs[i].iloc[-1].to_dict())

			# Update indicators table
			self.logger.debug(f'Indicator data for security {id} on date {date}: {data}')
			result = await self.dbConnector.forceUpdateEntries('indicators', {'security':id, 'date':date}, [data], 'indicators_security_date_uq')
			return result.success
			
		except Exception as e:
			self.logger.error(e)
			raise e


	@staticmethod
	def calculateMultiprocessing(id:int, config:dict) -> bool:
		try:
			logger = logging.getLogger()
			logger.info(f'calculateMultiprocessing({id})')

			conn = psycopg2.connect(
				database=os.environ.get('postgres_database'),
				user=os.environ.get('postgres_username'), 
				password=os.environ.get('postgres_password'),
				host=os.environ.get('postgres_address'),  
				port=os.environ.get('postgres_port')
			)
			
			cursor = conn.cursor()
			cursor.execute('''SELECT date,open::double precision,high::double precision,low::double precision,close::double precision,
						split_adjusted_open::double precision,split_adjusted_high::double precision,split_adjusted_low::double precision,
						split_adjusted_close::double precision,adjusted_close::double precision,volume::double precision
						FROM quotes WHERE security=%s ORDER BY date ASC;''', (id,))
			records = cursor.fetchall()
			quotes = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in records]
			logger.debug(f'got {len(records)} quotes for id={id}')

			# Convert to Pandas DataFrame
			dfDaily = pd.DataFrame(quotes)

			if len(dfDaily) < 10:
				logger.debug(f'Skip indicator calculation for ID: {id} (less data)')
				return True

			# Parse date string as date
			dfDaily['date'] = pd.to_datetime(dfDaily['date'])
			# Calculate weekly and monthly candles as well
			dfWeekly = IndicatorFactory.resampleDataFrame(dfDaily, Interval.WEEKLY)
			dfMonthly = IndicatorFactory.resampleDataFrame(dfDaily, Interval.MONTHLY)
			dfs = [dfDaily, dfWeekly, dfMonthly]

			# Calculate all configured indicators
			for obj in config['securities']:
				logger.debug(f'Calculate indicator {obj}')
				df:pd.DataFrame = dfs[intervalFromStr(obj['interval']).value]
				params = IndicatorFactory.parseParameters(obj['parameters'])
				success, df, keys = globals()[obj['indicator']](df, **params)
				if success == True:
					# Drop keys which will not be mapped
					for k in keys:
						if k not in obj['mapping'].keys():
							df = df.drop([k], axis=1)
					df = df.rename(columns=obj['mapping'])
					dfs[intervalFromStr(obj['interval']).value] = df
				else:
					logger.warning(f'Calculating indicator {obj} was not successful')
					return False

			# Cleanup and merge DataFrame objects as dict
			data = dict()
			date = datetime.strptime(np.datetime_as_string(dfs[0]['date'].values[-1], unit='D'), '%Y-%m-%d').date()
			for i in range(0, len(dfs)):
				dfs[i] = dfs[i].drop(['date','open','high','low','close','split_adjusted_open','split_adjusted_high','split_adjusted_low','split_adjusted_close','adjusted_close','volume'], axis=1)
				dfs[i] = dfs[i].replace({np.nan: None})
				data.update(dfs[i].iloc[-1].to_dict())
			data['security'] = id
			data['date'] = date
			
			# Write data to database
			columns = ','.join(data.keys())
			excluded = ','.join([f'{k}=EXCLUDED.{k}' for k in data.keys()])
			# (%s, %s, %s)
			placeholder = '(' + ','.join([ f'%s' for _ in range(1, len(data.keys())+1) ]) + ')'
			sql = f'''INSERT INTO indicators ({columns}) VALUES {placeholder} ON CONFLICT ON CONSTRAINT indicators_security_date_uq DO UPDATE SET {excluded};'''

			# Database write
			tupleData = tuple([data[field] for field in data.keys()])
			cursor.execute(sql, tupleData)
			conn.commit()
			cursor.close()
			conn.close()
			return True
		
		except Exception as e:
			logger.error(e)
		return False