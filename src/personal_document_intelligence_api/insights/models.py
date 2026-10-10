from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class InsightTakeaway:
    title: str
    explanation: str
    source_turn_numbers: tuple[int, ...]


@dataclass(frozen=True)
class InsightAction:
    rank: int
    title: str
    rationale: str
    priority: Literal["high", "medium", "low"]
    kind: Literal["explicit", "recommendation", "open_question"]
    source_turn_numbers: tuple[int, ...]


@dataclass(frozen=True)
class ConversationInsights:
    takeaways: tuple[InsightTakeaway, ...]
    actions: tuple[InsightAction, ...]
