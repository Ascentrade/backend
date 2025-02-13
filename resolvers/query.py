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

from log_config import logger

from graphql.type import GraphQLResolveInfo

from ariadne import load_schema_from_path
from ariadne_graphql_modules import ObjectType, DeferredType

from context import getDbPoolFromContext


class Query(ObjectType):

	__schema__ = load_schema_from_path('./schema/query.gql')

	__requires__ = [
		DeferredType("Currency"),
		DeferredType("Country"),
		DeferredType("Exchange"),
		DeferredType("GICSCode"),
		DeferredType("Security"),
	]
 

	@staticmethod
	def resolve_ping(*_):
		return 'pong'


	@staticmethod
	async def resolve_searchSecurity(_, info:GraphQLResolveInfo, searchText:str='', limit:int=50):
		try:
			if searchText == None or len(searchText) == 0:
				logger.warning('searchSecurity query without search text, skipping')
				return []
			logger.debug(f'searchSecurity({searchText}, {limit})')
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch("SELECT * FROM securities WHERE is_delisted=FALSE AND code ILIKE '%' || $1 || '%' ORDER BY length(code) ASC LIMIT $2;", searchText, limit)
				return [dict(e) for e in data] if len(data) > 0 else []
		except Exception as e:
			logger.error('Error at @query.field(searchSecurity)')
			logger.error(e)
		return []


	@staticmethod
	async def resolve_screenerSecurities(_, info:GraphQLResolveInfo, name:str=None):
		try:
			dbPool = getDbPoolFromContext(info)
			data = []
			async with dbPool.acquire() as con:
				if name == None or name == '':
					data = await con.fetch("SELECT DISTINCT ON (s.id) s.*, i.* FROM securities s JOIN indicators i ON i.security=s.id WHERE is_delisted=FALSE ORDER BY s.id ASC, i.date DESC")
				elif name == 'sector-etfs':
					data = await con.fetch("SELECT DISTINCT ON (s.id) s.* FROM securities s JOIN indicators i ON i.security=s.id WHERE is_delisted=FALSE AND (code='XLC' OR code='XLY' OR code='XLP' OR code='XLE' OR code='XLF' OR code='XLV' OR code='XLI' OR code='XLB' OR code='XLRE' OR code='XLK' OR code='XLU') ORDER BY s.id ASC, i.date DESC")
				elif name == 'adx-long-crossing':
					data = await con.fetch("SELECT * FROM (SELECT DISTINCT ON (s.id) s.*, i.* FROM securities s JOIN indicators i ON i.security=s.id WHERE is_delisted=FALSE AND dmi_bull_d IS TRUE AND adx_slope_d IS TRUE AND adx_crossing_date_d IS NOT NULL ORDER BY s.id ASC, i.date DESC) sub ORDER BY adx_crossing_date_d DESC")
				elif name == 'adx-short-crossing':
					data = await con.fetch("SELECT * FROM (SELECT DISTINCT ON (s.id) s.*, i.* FROM securities s JOIN indicators i ON i.security=s.id WHERE is_delisted=FALSE AND dmi_bull_d IS FALSE AND adx_slope_d IS TRUE AND adx_crossing_date_d IS NOT NULL ORDER BY s.id ASC, i.date DESC) sub ORDER BY adx_crossing_date_d DESC")
				elif name == 'adx-bull':
					data = await con.fetch("SELECT DISTINCT ON (s.id) s.* FROM securities s JOIN indicators i ON i.security=s.id WHERE is_delisted=FALSE AND dmi_bull_d IS TRUE AND adx_slope_d IS TRUE AND psar_bull_d IS TRUE AND dmi_bull_w IS TRUE AND adx_slope_w IS TRUE AND psar_bull_w IS TRUE AND dmi_bull_m IS TRUE AND adx_slope_m IS TRUE AND psar_bull_m IS TRUE ORDER BY s.id ASC, i.date DESC")
				elif name == 'adx-bear':
					data = await con.fetch("SELECT DISTINCT ON (s.id) s.* FROM securities s JOIN indicators i ON i.security=s.id WHERE is_delisted=FALSE AND dmi_bull_d IS FALSE AND adx_slope_d IS TRUE AND psar_bull_d IS FALSE AND dmi_bull_w IS FALSE AND adx_slope_w IS TRUE AND psar_bull_w IS FALSE AND dmi_bull_m IS FALSE AND adx_slope_m IS TRUE AND psar_bull_m IS FALSE ORDER BY s.id ASC, i.date DESC")
				else:
					logger.warning(f'Unknown screener name {name}')
			return [dict(e) for e in data] if len(data) > 0 else []
		except Exception as e:
			logger.error('Error at @query.field(screenerSecurities)')
			logger.error(e)
		return []


	@staticmethod
	async def resolve_currencies(_, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM currencies;')
				return [dict(e) for e in data] if len(data) > 0 else []
		except Exception as e:
			logger.error('Error at @query.field(currencies)')
			logger.error(e)
		return []


	@staticmethod
	async def resolve_currency(_, info:GraphQLResolveInfo, id:int=None):
		try:
			if id:
				dbPool = getDbPoolFromContext(info)
				async with dbPool.acquire() as con:
					data = await con.fetch('SELECT * FROM currencies WHERE id=$1;', id)
					return dict(data[0]) if len(data) > 0 else None
		except Exception as e:
			logger.error('Error at @query.field(currency)')
			logger.error(e)
		return None


	@staticmethod
	async def resolve_countries(_, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM countries;')
				return [dict(e) for e in data] if len(data) > 0 else []
		except Exception as e:
			logger.error('Error at @query.field(countries)')
			logger.error(e)
		return []


	@staticmethod
	async def resolve_country(_, info:GraphQLResolveInfo, id:int=None):
		try:
			if id:
				dbPool = getDbPoolFromContext(info)
				async with dbPool.acquire() as con:
					data = await con.fetch('SELECT * FROM countries WHERE id=$1;', id)
					return dict(data[0]) if len(data) > 0 else None
		except Exception as e:
			logger.error('Error at @query.field(country)')
			logger.error(e)
		return None


	@staticmethod
	async def resolve_exchanges(_, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT *, (CASE WHEN virtual_exchange IS NULL THEN FALSE ELSE (code=virtual_exchange) END) AS virtual FROM exchanges;')
				return [dict(e) for e in data] if len(data) > 0 else []
		except Exception as e:
			logger.error('Error at @query.field(exchanges)')
			logger.error(e)
		return []


	@staticmethod
	async def resolve_exchange(_, info:GraphQLResolveInfo, id:int=None):
		try:
			if id:
				dbPool = getDbPoolFromContext(info)
				async with dbPool.acquire() as con:
					data = await con.fetch('SELECT * FROM exchanges WHERE id=$1;', id)
					return dict(data[0]) if len(data) > 0 else None
		except Exception as e:
			logger.error('Error at @query.field(exchange)')
			logger.error(e)
		return None


	@staticmethod
	async def resolve_gics_codes(_, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM gics_codes ORDER BY id ASC;')
				return [dict(e) for e in data] if len(data) > 0 else []
		except Exception as e:
			logger.error('Error at @query.field(gics_codes)')
			logger.error(e)
		return []


	@staticmethod
	async def resolve_gics_code(_, info:GraphQLResolveInfo, id:int=None):
		try:
			if id:
				dbPool = getDbPoolFromContext(info)
				async with dbPool.acquire() as con:
					data = await con.fetch('SELECT * FROM gics_codes WHERE id=$1;', id)
					return dict(data[0]) if len(data) > 0 else None
		except Exception as e:
			logger.error('Error at @query.field(gics_code)')
			logger.error(e)
		return None


	@staticmethod
	async def resolve_securities(_, info:GraphQLResolveInfo):
		try:
			dbPool = getDbPoolFromContext(info)
			async with dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM securities;')
				return [dict(e) for e in data] if len(data) > 0 else []
		except Exception as e:
			logger.error('Error at @query.field(securities)')
			logger.error(e)
		return []


	@staticmethod
	async def resolve_security(_, info:GraphQLResolveInfo, id:int=None):
		try:
			if id:
				dbPool = getDbPoolFromContext(info)
				async with dbPool.acquire() as con:
					data = await con.fetch('SELECT * FROM securities WHERE id=$1;', id)
					return dict(data[0]) if len(data) > 0 else None
		except Exception as e:
			logger.error('Error at @query.field(security)')
			logger.error(e)
		return None