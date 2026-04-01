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

from __future__ import annotations

import datetime as dt
import os

from telegram import Bot

from logging_config import get_logger
logger = get_logger(__name__)


def sentiment_from_score(score: int) -> tuple[str, str]:
	"""
	Map a -100..100 score to delta-text sentiment and icon.
	"""
	if score <= -60:
		return "SHORT", "🔴"
	if score <= -20:
		return "MILD-SHORT", "🟠"
	if score <= 20:
		return "NEUTRAL", "⚪"
	if score <= 60:
		return "MILD-LONG", "🟡"
	return "LONG", "🟢"


class TelegramNotifier:
	def __init__(self, bot_token: str, chat_id: str) -> None:
		self._chat_id = chat_id
		self._bot = Bot(token=bot_token)

	@classmethod
	def from_env(cls) -> TelegramNotifier | None:
		bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
		chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
		if not bot_token or not chat_id:
			return None
		return cls(bot_token=bot_token, chat_id=chat_id)

	@staticmethod
	def _build_message(summary: str, score: int, confidence: int) -> str:
		now_utc = dt.datetime.now(dt.timezone.utc).strftime("%A %Y-%m-%d %H:%M UTC")
		delta_text, delta_icon = sentiment_from_score(score)

		return (
			f"🤖 {now_utc}\n"
			f"--------------------------------\n"
			f"{summary}\n"
			f"--------------------------------\n"
			f"{delta_icon} {delta_text} {score}/100 ({confidence}% confidence)\n"
			f"--------------------------------\n"
			f"-> More on https://ascentrade.app"
		)

	async def send_market_summary(self, summary: str, score: int, confidence: int) -> None:
		message = self._build_message(summary=summary, score=score, confidence=confidence)
		await self._bot.send_message(chat_id=self._chat_id, text=message)
		logger.info("Sent market summary push notification to Telegram")
