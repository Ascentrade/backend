import os
import asyncio
import uvicorn
from fastapi import Depends, FastAPI
from starlette.requests import HTTPConnection
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.schema.config import StrawberryConfig

from dotenv import load_dotenv
load_dotenv()

# Setup logging before other imports
from logging_config import setup_logging, get_logger
setup_logging()

logger = get_logger(__name__)

from db.session import get_session, AsyncSession
from db.schema import init_database
from resolvers.query_resolvers import Query
from scalars.scalars import BigInt
from utils import get_bool_env
from ai.market_summary_job import run_daily_market_summary_scheduler, run_market_summary_job_once

# https://strawberry.rocks/docs/integrations/fastapi

@asynccontextmanager
async def lifespan(app: FastAPI):
	"""
	Context manager for the lifespan of the FastAPI application.
	"""
	# Initialize database by creating tables from models
	logger.info("Starting application lifespan...")
	
	await init_database()
	run_at_startup = get_bool_env("RUN_AT_STARTUP", True)
	startup_market_task = None
	if run_at_startup:
		startup_market_task = asyncio.create_task(run_market_summary_job_once())
	else:
		logger.info("Skipping startup market summary run (RUN_AT_STARTUP=false)")

	scheduler_stop_event = asyncio.Event()
	daily_scheduler_task = asyncio.create_task(run_daily_market_summary_scheduler(scheduler_stop_event))

	logger.info("Application startup complete.")
	try:
		yield
	finally:
		scheduler_stop_event.set()
		daily_scheduler_task.cancel()
		tasks = [daily_scheduler_task]
		if startup_market_task is not None:
			tasks.append(startup_market_task)
		await asyncio.gather(*tasks, return_exceptions=True)
		logger.info("Application shutdown initiated.")

config = StrawberryConfig(
	auto_camel_case=True,
	scalar_map={
		BigInt: strawberry.scalar(
			name="BigInt",
			description="64-bit integer, serialized as string to avoid JSON precision loss",
			serialize=lambda v: None if v is None else str(v),
			parse_value=lambda v: int(v),
		),
	},
)

schema = strawberry.Schema(query=Query, config=config)

async def get_context(
	connection: HTTPConnection,
	session: AsyncSession = Depends(get_session),
):
	return {
		"session": session,
		"request": connection,
	}


graphql_app = GraphQLRouter(
	schema,
	context_getter=get_context,
	graphql_ide=os.environ.get("GRAPHQL_IDE", None)
)

# Configure CORS based on DEBUG environment variable
is_debug = get_bool_env("DEBUG", False)

app = FastAPI(
	title='Ascentrade AI Backend',
	version='0.1.0',
	lifespan=lifespan,
	debug=is_debug
)

if is_debug:
	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=False,
		allow_methods=["*"],
		allow_headers=["*"]
	)
else:
	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"]
	)

app.include_router(graphql_app, prefix="/graphql")

@app.get("/health")
async def health_check():
	return {"status": "ok"}


def main():
	"""Start the FastAPI app with Uvicorn."""
	log_level = os.environ.get("LOG_LEVEL", "INFO").lower()
	logger.info(f"Starting server on {os.environ.get('HOST')}:{os.environ.get('PORT')} with log level: {log_level}")
	uvicorn.run(
		"main:app",
		host=os.environ.get("HOST"),
		port=int(os.environ.get("PORT")),
		reload=True,
		log_level=log_level
	)

if __name__ == "__main__":
	main()
