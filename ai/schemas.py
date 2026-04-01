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

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MarketOutlook:
    """
    Strict schema for the LLM response.

    Matches the JSON required by `ai.prompts.SYSTEM_PROMPT`.
    """

    summary: str
    confidence: int
    score: int

    def __post_init__(self) -> None:
        # Simple runtime validation since we intentionally avoid pydantic.
        if not isinstance(self.summary, str) or not self.summary.strip():
            raise TypeError("summary must be a non-empty string")

        if not isinstance(self.confidence, int):
            raise TypeError("confidence must be an integer")
        if self.confidence < 0 or self.confidence > 100:
            raise ValueError("confidence must be between 0 and 100")

        if not isinstance(self.score, int):
            raise TypeError("score must be an integer")
        if self.score < -100 or self.score > 100:
            raise ValueError("score must be between -100 and 100")

    @classmethod
    def from_llm_dict(cls, raw: dict[str, Any]) -> "MarketOutlook":
        # Convenience helper to convert LLM response to MarketOutlook object
        return cls(**raw)

