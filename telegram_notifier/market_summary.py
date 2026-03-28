from __future__ import annotations

from telegram_notifier.notifier import TelegramNotifier


def market_summary_notifier_from_env() -> TelegramNotifier | None:
	"""Return a notifier for market-summary pushes when TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set."""
	return TelegramNotifier.from_env()
