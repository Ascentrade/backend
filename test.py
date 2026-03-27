import asyncio
import json
import os

from dotenv import load_dotenv

from ai.market_summary_job import build_market_summary
from logging_config import get_logger, setup_logging

load_dotenv()
setup_logging()
logger = get_logger(__name__)


async def main() -> None:
	persist_to_db = os.environ.get("PERSIST_MARKET_SUMMARY_TO_DB", "0").strip().lower() in {"1", "true", "t"}
	market_state, decision = await build_market_summary(persist_to_db=persist_to_db)
	logger.info("Finished computing market state using shared pipeline")
	print(json.dumps(market_state, indent=2))
	print(json.dumps(decision, indent=2))


if __name__ == "__main__":
	asyncio.run(main())
