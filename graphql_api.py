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
from utils import parseBoolean
from log_config import getNewLogger

# For .env file
from dotenv import load_dotenv
load_dotenv()

# GraphQL
from graphql import GraphQLError
from ariadne import load_schema_from_path, format_error
from ariadne_graphql_modules import make_executable_schema
from ariadne.asgi import GraphQL

# Custom Scalars
from scalars import custom_scalars

# Resolvers
from resolvers import custom_resolvers


class GraphQLApi():
	def __init__(self):
		# Create executable schema instance
		self.type_defs = load_schema_from_path("./schema/common.gql")
		self.schema = make_executable_schema(self.type_defs, *custom_scalars, *custom_resolvers)

		gqlLogger = getNewLogger('gql')

		self.gqlApp = GraphQL(
			self.schema,
			logger=gqlLogger,
			error_formatter=self.customErrorFormatter,
			debug=parseBoolean(os.environ.get('debug')),
			introspection=parseBoolean(os.environ.get('introspection'))
		)

	@staticmethod
	def customErrorFormatter(error: GraphQLError, debug: bool = False) -> dict:
		"""Custom GraphQL error formatter for Ariadne. Docs: https://ariadnegraphql.org/docs/error-messaging

		Args:
			error (GraphQLError): Original GraphQL error
			debug (bool, optional): Debug output. Defaults to False.

		Returns:
			dict: Custom format
		"""
		if debug:
			# If debug is enabled, reuse Ariadne's formatting logic (not required)
			return format_error(error, debug)

		# Create formatted error data
		formatted = error.formatted
		# Replace original error message with custom one
		formatted["message"] = "INTERNAL SERVER ERROR"
		return formatted