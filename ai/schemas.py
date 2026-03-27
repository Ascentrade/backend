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

