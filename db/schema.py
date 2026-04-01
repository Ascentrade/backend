"""
 @copyright Copyright (C) 2026 Dennis Einloft <dev@greguhn.de>
 
 @author Dennis Einloft <dev@greguhn.de>
 
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

