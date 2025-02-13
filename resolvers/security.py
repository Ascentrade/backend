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

from datetime import date
from log_config import logger

from graphql.type import GraphQLResolveInfo

from ariadne import load_schema_from_path
from ariadne_graphql_modules import ObjectType, DeferredType

from context import getDbPoolFromContext


class Security(ObjectType):
	__schema__ = load_schema_from_path('./schema/security.gql')

	__requires__ = [
		DeferredType('BigInt'),
		DeferredType('Currency'),
		DeferredType('Country'),
		DeferredType('Date'),
		DeferredType('Decimal'),
		DeferredType('Exchange'),
		DeferredType('JSON'),
		DeferredType('GICSCode'),
		DeferredType('SecurityType'),
		DeferredType('Time'),
		DeferredType('SecurityQuote'),
		DeferredType('Split'),
		DeferredType('Dividend'),
		DeferredType('AnalystRating'),
		DeferredType('ETFData'),
		DeferredType('Datetime'),
		DeferredType('OutstandingShares')
	]

	@staticmethod
	async def resolve_currency(obj, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM currencies WHERE id=$1;', obj['currency'])
				return dict(data[0]) if len(data) == 1 else None
		except Exception as e:
			logger.error('Error at @security.field(currency)')
			logger.error(e)
		return None


	@staticmethod
	async def resolve_country(obj, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM countries WHERE id=$1;', obj['country'])
				return dict(data[0]) if len(data) == 1 else None
		except Exception as e:
			logger.error('Error at @security.field(country)')
			logger.error(e)
		return None
	

	@staticmethod
	async def resolve_quotes(obj, info:GraphQLResolveInfo, start:date=date(1970,1,1), end:date=date(2100,12,31)):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT date, open, high, low, close, split_adjusted_open, split_adjusted_high, split_adjusted_low, split_adjusted_close, adjusted_close, volume FROM quotes WHERE security=$1 AND date >= $2 AND date <= $3 ORDER BY date ASC;', obj['id'], start, end)
				return [dict(e) for e in data]
		except Exception as e:
			logger.error('Error at @security.field(quotes)')
			logger.error(e)
		return []
	

	@staticmethod
	async def resolve_last_quote(obj, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM quotes WHERE security=$1 ORDER BY date DESC LIMIT 1;', obj['id'])
				return dict(data[0])
		except Exception as e:
			logger.error('Error at @security.field(last_quote)')
			logger.error(e)
		return None
	

	@staticmethod
	async def resolve_splits(obj, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT date, old, new FROM splits WHERE security=$1 ORDER BY date ASC;', obj['id'])
				return [dict(e) for e in data]
		except Exception as e:
			logger.error('Error at @security.field(splits)')
			logger.error(e)
		return []
	

	@staticmethod
	async def resolve_dividends(obj, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT date, declaration_date, record_date, payment_date, period, adjusted_value, value FROM dividends WHERE security=$1 ORDER BY date ASC;', obj['id'])
				return [dict(e) for e in data]
		except Exception as e:
			logger.error('Error at @security.field(dividends)')
			logger.error(e)
		return []
	

	@staticmethod
	async def resolve_analyst_ratings(obj, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT date_added, rating, target_price, strong_buy, buy, hold, sell, strong_sell FROM analyst_ratings WHERE security=$1 ORDER BY date_added ASC;', obj['id'])
				return [dict(e) for e in data]
		except Exception as e:
			logger.error('Error at @security.field(analyst_ratings)')
			logger.error(e)
		return []
	

	@staticmethod
	async def resolve_etf_data(obj, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT company_name, company_url, etf_url, yield, dividend_paying_frequency, inception_date, total_assets, holdings_count FROM etf_data WHERE security=$1;', obj['id'])
				return dict(data[0]) if len(data) > 0 else None
		except Exception as e:
			logger.error('Error at @security.field(etf_data)')
			logger.error(e)
		return None
	

	@staticmethod
	async def resolve_indicators(obj, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM indicators WHERE security=$1 ORDER BY date DESC LIMIT 1;', obj['id'])
				result = None
				if data != None and len(data) > 0:
					result = dict(data[0])
					# Remove foreign key
					del result['security']
				return result
		except Exception as e:
			logger.error('Error at @security.field(indicators)')
			logger.error(e)
		return None
	

	@staticmethod
	async def resolve_exchange(obj, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM exchanges WHERE id=$1 LIMIT 1;', obj['exchange'])
				result = None
				if data != None and len(data) > 0:
					result = dict(data[0])
				return result
		except Exception as e:
			logger.error('Error at @security.field(exchange)')
			logger.error(e)
		return None
	

	@staticmethod
	async def resolve_exchange_code(obj, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT code AS exchange_code FROM exchanges WHERE id=$1 LIMIT 1;', obj['exchange'])
				result = None
				if data != None and len(data) > 0:
					result =data[0]['exchange_code']
				return result
		except Exception as e:
			logger.error('Error at @security.field(exchange_code)')
			logger.error(e)
		return None
	

	@staticmethod
	async def resolve_outstanding_shares(obj, info:GraphQLResolveInfo, start:date=date(1970,1,1), end:date=date(2100,12,31)):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT date, outstanding_shares FROM outstanding_shares WHERE security=$1 AND date >= $2 AND date <= $3 ORDER BY date ASC;', obj['id'], start, end)
				return [dict(e) for e in data]
		except Exception as e:
			logger.error('Error at @security.field(outstanding_shares)')
			logger.error(e)
		return []