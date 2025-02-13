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

import logging
from indicator_factory import IndicatorFactory
from log_config import logger

from asyncpg import Pool
from tasks import TaskHandler

from database import DatabaseConnector
from graphql.type import GraphQLResolveInfo


def getDbPoolFromContext(info:GraphQLResolveInfo) -> Pool:
	"""Exctracts the database pool from FastAPI app state

	Args:
		info (GraphQLResolveInfo): Input resolve info object

	Returns:
		Pool: Pool connection to database or None if error
	"""
	try:
		return info.context['request'].app.state.dbCon.dbPool
	except Exception as e:
		logger.error(e)
	return None


def getLoggerFromContext(info:GraphQLResolveInfo) -> logging.Logger:
	"""Extract the logger object from GraphQLResolveInfo

	Args:
		info (GraphQLResolveInfo): Input resolve info

	Returns:
		logging.Logger: Logger instance or None
	"""
	try:
		return info.context['request'].app.state.logger
	except Exception as e:
		logger.error(e)
	return None


def getTaskHandlerFromContext(info:GraphQLResolveInfo) -> TaskHandler:
	"""Extract the TaskHandler object from GraphQLResolveInfo

	Args:
		info (GraphQLResolveInfo): Input resolve info

	Returns:
		TaskHandler: TaskHandler instance or None
	"""
	try:
		return info.context['request'].app.state.taskHandler
	except Exception as e:
		logger.error(e)
	return None


def getDbConnectorFromContext(info:GraphQLResolveInfo) -> DatabaseConnector:
	try:
		return info.context['request'].app.state.dbCon
	except:
		raise Exception('Error while getting DatabaseConnector from context')


def getIndicatorFactoryFromContext(info:GraphQLResolveInfo) -> IndicatorFactory:
	try:
		return info.context['request'].app.state.indicatorFactory
	except:
		raise Exception('Error while getting IndicatorFactory from context')