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
import json
from secrets import token_hex

from utils import parseBoolean, parseInt
from log_config import getNewLogger

# For .env file
from dotenv import load_dotenv
load_dotenv()

# Database
from database import DatabaseConnector

# Valkey
import valkey

# ASGI Application
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Task Handler
from tasks import TaskHandler

from graphql_api import GraphQLApi


@asynccontextmanager
async def lifespan(app: FastAPI):
	# App startup code
	app.state.logger.info('on_startup()')

	# Create database instance
	dbCon = DatabaseConnector()
	app.state.dbCon = dbCon
	await dbCon.openPool()

	# Task handler initialization
	th = TaskHandler(dbCon)
	await th.loadJobs()
	app.state.taskHandler = th

	# Init Valkey cache
	app.state.pubsub = None
	if os.environ.get('valkey_host') != None and os.environ.get('valkey_host') != '':
		app.state.valkey = valkey.Valkey(
			host = os.environ.get('valkey_host'),
			port = int(os.environ.get('valkey_port')),
			db = int(os.environ.get('valkey_db'))
		)
		app.state.pubsub = app.state.valkey.pubsub()
	
	yield
	
	# Cleanup
	app.state.logger.info('on_shutdown()')
	await app.state.taskHandler.shutdown()
	await app.state.dbCon.closePool()


def createApp() -> FastAPI:
	# Define the FastAPI application
	app = FastAPI(
		title = 'Ascentrade GraphQL API',
		description='Backend API for data updaters and frontend services.',
		lifespan=lifespan,
		license_info={
			'name': 'Affero General Public License 3.0',
			'url': 'https://www.gnu.org/licenses/agpl-3.0.de.html',
		},
		debug = parseBoolean(os.environ.get('debug'))
	)

	# Create app logger
	logger = getNewLogger('gql')
	app.state.logger = logger

	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	# Generate auth token for updaters if not exist
	TOKEN_PATH = os.environ.get('token_path')
	if os.path.exists(TOKEN_PATH) == False:
		app.state.authToken = token_hex(16)
		with open(TOKEN_PATH, 'w') as f:
			f.write(app.state.authToken)
		logger.warning(f'Generated a new auth token: {app.state.authToken[:4]}...{app.state.authToken[-4:]}')
	else:
		with open(TOKEN_PATH, 'r') as f:
			app.state.authToken = f.readline()
		logger.info(f'Found auth token: {app.state.authToken[:4]}...{app.state.authToken[-4:]}')

	@app.middleware("http")
	async def authMiddleware(request: Request, call_next):
		# Add code before processing request
		#print(request)
		#print(request.state)
		#print(request.method)
		#print(request.url.query)
		#print(request.query_params)
		#print(request.path_params)
		#print(request.headers)

		response = Response(json.dumps({'status': 500, 'message':'server error'}), 500, media_type='application/json')

		try:
			# Block all mutation calls to GraphQL
			if request.method == 'POST':
				data = await request.body()
				jobj = json.loads(data.decode('utf-8'))
				# jobj['operationName'] -> user defined operation name, NOT GraphQL query/mutation
				if jobj['query'].startswith('mutation'):
					# We need some authorization to do modifications
					if 'x-auth-token' in request.headers.keys() and request.headers['x-auth-token'] == app.state.authToken:
						pass
					else:
						app.state.logger.warning(f'Unauthorized mutation {jobj}')
						return Response(json.dumps({'status': 401, 'message':'not authenticated'}), 401, media_type='application/json')
			
			response = await call_next(request)
		except:
			pass

		# Add code after processing the request
		#response.headers["X-Foo-Header"] = 'Bar'

		return response

	app.state.graphQlApi = GraphQLApi()
	app.mount(os.environ.get('gql_path'), app.state.graphQlApi.gqlApp)
	return app