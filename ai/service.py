import json
from .provider import LLMProvider
from .prompts import SYSTEM_PROMPT
from .schemas import MarketOutlook
from logging_config import get_logger

logger = get_logger(__name__)


class AIService:
    def __init__(self):
        self.llm = LLMProvider()

    async def evaluate_market_state(self, market_state: dict) -> MarketOutlook:

        user_prompt = f"""
        Evaluate the following market state and give a market outlook for the next few days.

        {json.dumps(market_state)}
        """

        raw_response = await self.llm.chat(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        logger.info(f"AI response for market state received: {json.dumps(raw_response)}")

        # Validate the response using the MarketOutlook schema
        try:
            return MarketOutlook(**raw_response)
        except Exception as e:
            logger.error(f"Failed to validate AI response: {e}")
            logger.error(f"Raw response was: {json.dumps(raw_response, indent=2)}")
            raise
