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

from context import getDbConnectorFromContext


class Exchange(ObjectType):
	__schema__ = load_schema_from_path('./schema/exchange.gql')

	__requires__ = [
		DeferredType('Currency'),
		DeferredType('Country'),
		DeferredType('Time'),
		DeferredType('ExchangeHoliday')
	]

	@staticmethod
	async def resolve_currency(obj, info:GraphQLResolveInfo):
		try:
			dbCon = getDbConnectorFromContext(info)
			async with dbCon.dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM currencies WHERE id=$1;', obj['currency'])
				return dict(data[0]) if len(data) == 1 else None
		except Exception as e:
			logger.error('Error at @exchange.field(currency)')
			logger.error(e)
		return None


	@staticmethod
	async def resolve_country(obj, info:GraphQLResolveInfo):
		try:
			dbCon = getDbConnectorFromContext(info)
			async with dbCon.dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM countries WHERE id=$1;', obj['country'])
				return dict(data[0]) if len(data) == 1 else None
		except Exception as e:
			logger.error('Error at @exchange.field(country)')
			logger.error(e)
		return None


	@staticmethod
	async def resolve_holidays(obj, info:GraphQLResolveInfo):
		try:
			dbCon = getDbConnectorFromContext(info)
			async with dbCon.dbPool.acquire() as con:
				data = await con.fetch('SELECT * FROM exchange_holidays WHERE exchange=$1;', obj['id'])
				return [dict(e) for e in data] if len(data) > 0 else []
		except Exception as e:
			logger.error('Error at @exchange.field(holidays)')
			logger.error(e)
		return []