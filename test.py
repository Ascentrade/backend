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

import asyncio
import json

from dotenv import load_dotenv

from ai.market_summary_job import build_market_summary
from logging_config import get_logger, setup_logging
from utils import get_bool_env

load_dotenv()
setup_logging()
logger = get_logger(__name__)


async def main() -> None:
	persist_to_db = get_bool_env("PERSIST_MARKET_SUMMARY_TO_DB", False)
	send_telegram = get_bool_env("SEND_TELEGRAM_NOTIFICATIONS", False)
	market_state, decision = await build_market_summary(
		persist_to_db=persist_to_db,
		send_telegram_notifications=send_telegram,
	)
	logger.info("Finished computing market state using shared pipeline")
	print(json.dumps(market_state, indent=2))
	print(json.dumps(decision, indent=2))


if __name__ == "__main__":
	asyncio.run(main())
