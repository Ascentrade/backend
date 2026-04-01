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
