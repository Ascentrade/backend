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
from multiprocessing import Pool
from indicator_factory import IndicatorFactory
from log_config import logger

from graphql.type import GraphQLResolveInfo

from ariadne import load_schema_from_path
from ariadne_graphql_modules import ObjectType, DeferredType

from utils import securityInputFilter, parseBoolean
from context import getDbConnectorFromContext, getIndicatorFactoryFromContext, getTaskHandlerFromContext

from tasks import BackgroundJobData


class Mutation(ObjectType):
	__schema__ = load_schema_from_path('./schema/mutation.gql')

	__requires__ = [
		DeferredType('SecurityInput'),
		DeferredType('SecurityQuotesInput'),
		DeferredType('SplitsInput'),
		DeferredType('DividendsInput'),
		DeferredType('OutstandingSharesInput'),
		DeferredType('UpdateResult')
	]

	@staticmethod
	async def resolve_updateSecurity(_, info:GraphQLResolveInfo, data):
		# GraphQLResolveInfo(field_name='updateSecurity', field_nodes=[FieldNode at 13:195], return_type=<GraphQLNonNull <GraphQLObjectType 'UpdateResult'>>, parent_type=<GraphQLObjectType 'Mutation'>, path=Path(prev=None, key='updateSecurity', typename='Mutation'), schema=<graphql.type.schema.GraphQLSchema object at 0x7fd0b65b89a0>, fragments={}, root_value=None, operation=OperationDefinitionNode at 0:197, variable_values={}, context={'request': <starlette.requests.Request object at 0x7fd0b4225910>}, is_awaitable=<function is_awaitable at 0x7fd0b723e430>)
		# {'code': 'AAPL', 'type': 'Stock', 'name': 'Apple', 'exchange_code': 'US', 'currency_iso_code': 'USD', 'country_alpha3': 'USA'}
		try:
			data = securityInputFilter(data)
			dbCon = getDbConnectorFromContext(info)

			# Query existing fields
			selector = await dbCon.getSecurityAndExchange(data['code'], data['exchange_code'])
			logger.debug(selector)

			# Check for valid exchange or search for
			if selector.exchange != None:
				data['exchange'] = selector.exchange
			else:
				eId = await dbCon.getExchangeId(data['exchange_code'])
				if eId != None:
					data['exchange'] = eId
				else:
					msg = f'Unknown exchange {data["exchange_code"]}'
					logger.error(msg)
					return {'success':False, 'error':msg}
			# Exchange code was now replaced by id
			del data['exchange_code']

			# Query currency
			if 'currency_iso_code' in data.keys():
				id = await dbCon.getCurrencyId(data['currency_iso_code'])
				data['currency'] = id
				del data['currency_iso_code']

			# Query country
			if 'country_alpha3' in data.keys():
				id = await dbCon.getCountryId(data['country_alpha3'])
				data['country'] = id
				del data['country_alpha3']

			# Update or add into database
			if selector.id != None:
				result = await dbCon.updateTable('securities', selector.id, data)
			else:
				result = await dbCon.insertEntry('securities', data)
			logger.debug(result)

			return {'success':result.success, 'error':result.exception}
		except Exception as e:
			logger.error('Error at @mutation.field(updateSecurity)')
			logger.error(e)
			return {'success':False, 'error':e}


	@staticmethod
	async def resolve_updateSecurityQuotes(_, info:GraphQLResolveInfo, data):
		try:
			data = securityInputFilter(data)
			dbCon = getDbConnectorFromContext(info)
		
			# Query existing fields
			selector = await dbCon.getSecurityAndExchange(data['code'], data['exchange_code'])
			logger.debug(selector)

			if selector.id == None:
				return {'success':False, 'error':f'No security {data["code"]}:{data["exchange_code"]} found'} 
			logger.debug('Start quote update...')
			result = await dbCon.forceUpdateEntries('quotes', {'security':selector.id}, data['quotes'], 'security_date_uq')
			logger.debug('Quote update finished!')
			logger.debug(result)

			# Queue indicator calculation
			if parseBoolean(os.environ.get('indicatorCalculation')) == True:
				th = getTaskHandlerFromContext(info)
				await th.addJob(BackgroundJobData('quotes', selector.id))

			return {'success':result.success, 'error':result.exception}
		except Exception as e:
			logger.error('Error at @mutation.field(updateSecurityQuotes)')
			logger.error(e)
			return {'success':False, 'error':e}
	

	@staticmethod
	async def resolve_updateSplits(_, info:GraphQLResolveInfo, data):
		try:
			data = securityInputFilter(data)
			dbCon = getDbConnectorFromContext(info)

			# Query existing fields
			selector = await dbCon.getSecurityAndExchange(data['code'], data['exchange_code'])
			logger.debug(selector)

			if selector.id == None:
				return {'success':False, 'error':f'No security {data["code"]}:{data["exchange_code"]} found'} 

			result = await dbCon.forceUpdateEntries('splits', {'security':selector.id}, data['splits'], 'splits_security_date_uq')
			logger.debug(result)

			return {'success':result.success, 'error':result.exception}
		except Exception as e:
			logger.error('Error at @mutation.field(updateSplits)')
			logger.error(e)
			return {'success':False, 'error':e}


	@staticmethod
	async def resolve_updateDividends(_, info:GraphQLResolveInfo, data):
		try:
			data = securityInputFilter(data)
			dbCon = getDbConnectorFromContext(info)
		
			# Query existing fields
			selector = await dbCon.getSecurityAndExchange(data['code'], data['exchange_code'])
			logger.debug(selector)

			if selector.id == None:
				return {'success':False, 'error':f'No security {data["code"]}:{data["exchange_code"]} found'} 

			result = await dbCon.forceUpdateEntries('dividends', {'security':selector.id}, data['dividends'], 'dividends_security_date_uq')
			logger.debug(result)

			return {'success':result.success, 'error':result.exception}
		except Exception as e:
			logger.error('Error at @mutation.field(updateDividends)')
			logger.error(e)
			return {'success':False, 'error':e}


	@staticmethod
	async def resolve_updateOutstandingShares(_, info:GraphQLResolveInfo, data):
		try:
			data = securityInputFilter(data)
			dbCon = getDbConnectorFromContext(info)
		
			# Query existing fields
			selector = await dbCon.getSecurityAndExchange(data['code'], data['exchange_code'])
			logger.debug(selector)

			if selector.id == None:
				return {'success':False, 'error':f'No security {data["code"]}:{data["exchange_code"]} found'} 

			result = await dbCon.forceUpdateEntries('outstanding_shares', {'security':selector.id}, data['outstanding_shares'], 'outstanding_shares_security_date_uq')
			logger.debug(result)

			return {'success':result.success, 'error':result.exception}
		except Exception as e:
			logger.error('Error at @mutation.field(updateOutstandingShares)')
			logger.error(e)
			return {'success':False, 'error':e}