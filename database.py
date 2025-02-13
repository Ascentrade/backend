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

import os

# PostgreSQL Database
import asyncpg

from dataclasses import dataclass

# For .env file
from dotenv import load_dotenv
load_dotenv()

from log_config import getNewLogger


@dataclass
class SecurityExchangeResult:
	"""Class to return data and/or errors for sub-database requests"""
	code: str
	exchange_code: str
	exchange: int
	id: int

	exception: Exception

	def __init__(
		self,
		code:str=None,
		exchange_code:str=None,
		exchange:int=None,
		id:int=None,
		exception:Exception=None
	):
		self.code = code.upper() if code != None else None
		self.exchange_code = exchange_code.upper() if exchange_code != None else None
		self.exchange = exchange
		self.id = id
		self.exception = exception


@dataclass
class UpdateResult:
	"""Class to handle results from DB operations"""
	success: bool
	id: int
	exception: Exception

	def __init__(
		self,
		success:bool=False,
		id:int=0,
		exception:Exception=None
	):
		self.success = success
		self.id = id
		self.exception = exception


class DatabaseConnector():

	def __init__(self):
		self.dbPool:asyncpg.Pool = None
		self.logger = getNewLogger("database")


	async def openPool(self) -> asyncpg.Pool:
		if self.dbPool == None:
			try:
				self.dbPool = await asyncpg.create_pool('postgresql://{0}:{1}@{2}:{3}/{4}'.format(
					os.environ.get('postgres_username'),
					os.environ.get('postgres_password'),
					os.environ.get('postgres_address'),
					os.environ.get('postgres_port'),
					os.environ.get('postgres_database'))
				)

				async with self.dbPool.acquire() as con:
					data = await con.fetchrow('SELECT VERSION();')
					self.logger.info(f'Connected to {data[0]}')

			except Exception as e:
				self.logger.error('Failed get database connection pool')
				self.logger.error(e)
				self.dbPool = None
				raise Exception('No database connection!')

		return self.dbPool


	def getPool(self):
		return self.dbPool


	async def closePool(self):
		if self.dbPool != None:
			await self.dbPool.close()


	async def getSecurityAndExchange(self, code:str=None, exchange_code:str=None) -> SecurityExchangeResult:
		"""Function to grab exchange and security IDs from the database

		Args:
			con (Pool): A single database connection from the pool
			code (str): Ticker symbol of the stock
			exchange_code (str): Code of the exchange (e.g. 'NASDAQ') or a virtual exchange code (e.g. 'US')

		Returns:
			SecurityExchangeResult: Dataclass with results
		"""
		result = SecurityExchangeResult(code=code, exchange_code=exchange_code)
		try:
			if code != None and len(code) > 0 and exchange_code != None and len(exchange_code) > 0:
				async with self.dbPool.acquire() as con:
					data = await con.fetch("""SELECT s.id AS security_id, e.id AS exchange_id FROM securities s JOIN exchanges e ON s.exchange=e.id
												WHERE s.code=$1 AND (e.code=$2 OR e.virtual_exchange=$2) ORDER BY s.last_update DESC;""", code, exchange_code)
					# Take the first entry ordered by last_update if any
					if len(data) >= 1:
						result.id = data[0]['security_id']
						result.exchange = data[0]['exchange_id']

					if len(data) == 0:
						msg = f'Found no matching stocks for getSecurityAndExchange({code}, {exchange_code})'
						self.logger.debug(msg)
						result.exception = Exception(msg)
					elif len(data) > 1:
						msg = f'Found multiple matching stocks for getSecurityAndExchange({code}, {exchange_code}): {data}, take last updated one!'
						self.logger.warning(msg)
						result.exception = Exception(msg)
			else:
				raise Exception('Invalid input data for getSecurityAndExchange()')
		except Exception as e:
			self.logger.error(e)
			result.exception = e
		return result


	async def getCurrencyId(self, isoCode:str) -> int:
		"""Query a currency ID from the database

		Args:
			con (Connection): Database connection from pool
			isoCode (str): ISO3 code of a currency.

		Raises:
			Exception: If currency ISO code is None or wrong length.

		Returns:
			int: Valid id of the currency or None if not found/invalid.
		"""
		id = None
		try:
			if isoCode != None and len(isoCode) == 3:
				async with self.dbPool.acquire() as con:
					data = await con.fetch('SELECT id FROM currencies WHERE iso_code=$1;', isoCode.upper())
					id = data[0]['id'] if len(data) == 1 else None
			else:
				raise Exception('Invalid currency ISO code')
		except Exception as e:
			self.logger.error(e)
		return id


	async def getCountryId(self, alpha3:str) -> int:
		"""Query a country ID from the database

		Args:
			con (Connection): Database connection from pool
			alpha3 (str): Alpha3 code of a country.

		Raises:
			Exception: If country alpha3 is None or wrong length.

		Returns:
			int: Valid id of the currency or None if not found/invalid.
		"""
		id = None
		try:
			if alpha3 != None and len(alpha3) == 3:
				async with self.dbPool.acquire() as con:
					data = await con.fetch('SELECT id FROM countries WHERE alpha3_code=$1;', alpha3.upper())
					id = data[0]['id'] if len(data) == 1 else None
			else:
				raise Exception('Invalid country alpha3 code')
		except Exception as e:
			self.logger.error(e)
		return id


	async def getExchangeId(self, code:str) -> int:
		"""Query a exchange ID from the database

		Args:
			con (Connection): Database connection from pool
			code (str): Exchange code

		Raises:
			Exception: If exchange code is invalid.

		Returns:
			int: Valid id of the exchange or None if not found/invalid.
		"""
		id = None
		try:
			if code != None:
				async with self.dbPool.acquire() as con:
					data = await con.fetch('SELECT id FROM exchanges WHERE code=$1;', code.upper())
					id = data[0]['id'] if len(data) == 1 else None
			else:
				raise Exception('Invalid exchange code')
		except Exception as e:
			self.logger.error(e)
		return id


	async def updateTable(self, table:str, id:int, data:dict, excludeKeys:list=['id']) -> UpdateResult:
		"""Update an entry in a database table

		Args:
			con (Connection): Connection from the pool
			table (str): Database table name
			id (int): ID of the entry
			data (dict): Data to update
			excludeKeys (list, optional): Keys to ignore in the update. Defaults to ['id'].

		Returns:
			UpdateResult: {'success':bool, 'exception:Exception, id:int}
		"""
		self.logger.debug(f'updateTable({table}, {id}, {data}, {excludeKeys})')
		try:
			errors = []
			for key in data.keys():
				if key not in excludeKeys:
					try:
						statement = f'UPDATE {table} SET {key} = COALESCE($1, {key}) WHERE id=$2;'
						async with self.dbPool.acquire() as con:
							await con.execute(statement, data[key], id)
					except Exception as e:
						self.logger.error(e)
						errors.append(e)
			# Return True or the first error
			return UpdateResult(True if len(errors)==0 else False, id, None if len(errors)==0 else errors[0])
		except Exception as e:
			return UpdateResult(exception=e)


	async def insertEntry(self, table:str, data:dict, excludeKeys:list=[]) -> UpdateResult:
		"""Insert a new entry into a database table

		Args:
			con (Connection): Connection from the pool
			table (str): Database table name
			data (dict): Data dictionary
			excludeKeys (list, optional): Keys to ignore in the insert. Defaults to [].

		Returns:
			UpdateResult: {'success':bool, 'exception:Exception, id:int}
		"""
		self.logger.debug(f'insertEntry({table}, {data}, {excludeKeys})')
		try:
			# Cleanup data dictionary
			for k in excludeKeys:
				if k in data.keys():
					del data[k]
			# Prepare statement
			columns = ','.join(data.keys())
			placeholder = ','.join([ f'${i}' for i in range(1,len(data.keys())+1) ])
			# INSERT INTO securities (code,name,type,exchange,currency,country) VALUES ($1,$2,$3,$4,$5,$6) RETURNING id;
			statement = f'INSERT INTO {table} ({columns}) VALUES ({placeholder}) RETURNING id;'
			async with self.dbPool.acquire() as con:
				result = await con.fetch(statement, *data.values())
				return UpdateResult(True, result[0]['id'])
		except Exception as e:
			self.logger.error(e)
			return UpdateResult(exception=e)


	async def forceUpdateEntries(self, table:str, identifier:dict, data:list[dict], constraint:str) -> UpdateResult:
		"""Force update entries in a table

		Args:
			con (Connection): Database connection from the pool
			table (str): Database table name
			identifier (dict): Dict to add to every **data** element
			data (list): List with objects to update
			constraint (str): Name of the database table constraint for conflict update

		Returns:
			UpdateResult: {'success':bool, 'exception:Exception}
		"""
		try:
			self.logger.debug(f'forceUpdateEntries: {table}, {identifier}, {len(data)} entries')
			if len(data) > 0:
				#for entry in data:
				firstEntry = identifier | data[0]
				order = firstEntry.keys()
				#self.logger.debug(f'update {table} with {entry}')
				columns = ','.join(order)
				excluded = ','.join([f'{k}=EXCLUDED.{k}' for k in order])
				# ($1, $2, $3)
				placeholder = '(' + ','.join([ f'${i}' for i in range(1, len(order)+1) ]) + ')'
				sql = f'''INSERT INTO {table} ({columns}) VALUES {placeholder} ON CONFLICT ON CONSTRAINT {constraint} DO UPDATE SET {excluded};'''

				# Create a list of tuples with the data
				tupleList = []
				for entry in data:
					d = identifier | entry
					# Tuple contains data in the same order like the first entry
					tupleList.append(tuple([d[field] for field in order]))

				# Database write
				async with self.dbPool.acquire() as con:
					await con.executemany(sql, tupleList)
				return UpdateResult(True)
			else:
				return UpdateResult(exception='No entries to update in list')
		except Exception as e:
			self.logger.error(e)
			return UpdateResult(exception=e)