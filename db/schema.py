"""
Database schema initialization utilities.

This project intentionally does not perform automatic database migrations.
If the live database schema diverges from the SQLAlchemy models, update it manually
or rebuild the database to match the current models.
"""

from logging_config import get_logger

from db.session import Base, engine

logger = get_logger(__name__)


async def init_database() -> None:
	"""
	Create tables from SQLAlchemy models if they don't exist.

	Note: SQLAlchemy's `create_all` will not modify existing tables/columns.
	"""
	try:
		async with engine.begin() as conn:
			await conn.run_sync(Base.metadata.create_all)
	except Exception as e:
		logger.error(f"Failed to initialize database schema: {e}")
		logger.info("Proceeding with application startup despite database error.")

