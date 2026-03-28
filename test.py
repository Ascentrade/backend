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
