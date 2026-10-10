import re
from collections.abc import Sequence

from personal_document_intelligence_api.insights.models import (
    ConversationInsights,
    InsightAction,
    InsightTakeaway,
)

_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
_MARKDOWN = re.compile(r"[*_`#>]+")
_CITATION = re.compile(r"\s*\[(?:Source|Sources)\s+[^]]+]", re.IGNORECASE)
_ACTION_WORDS = (
    "should ", "next ", "consider ", "create ", "review ", "verify ", "use ",
    "sebaiknya ", "selanjutnya ", "buat ", "tinjau ", "periksa ", "gunakan ",
)
_URGENT_WORDS = ("must ", "required", "critical", "urgent", "harus ", "wajib ")
_INSUFFICIENT_PHRASES = (
    "cannot be found",
    "insufficient",
    "not enough information",
    "tidak dapat ditemukan",
    "informasi tidak cukup",
)


def _clean(text: str) -> str:
    text = _BULLET.sub("", text.strip())
    text = _CITATION.sub("", text)
    text = _MARKDOWN.sub("", text)
    return " ".join(text.split())


def _candidate_lines(answer: str) -> list[str]:
    lines = [_clean(line) for line in answer.splitlines() if _clean(line)]
    bullets = [
        _clean(line)
        for line in answer.splitlines()
        if _BULLET.match(line) and len(_clean(line)) >= 24
    ]
    if bullets:
        return bullets
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(lines))
    return [sentence.strip() for sentence in sentences if len(sentence.strip()) >= 36]


def _title(text: str) -> str:
    if ":" in text[:100]:
        candidate = text.split(":", 1)[0]
    else:
        candidate = " ".join(text.split()[:10])
    return candidate[:157].rstrip(" ,.;:") + ("…" if len(candidate) > 157 else "")


def build_conversation_insights(
    turns: Sequence[tuple[str, str]],
) -> ConversationInsights:
    seen: set[str] = set()
    takeaways: list[InsightTakeaway] = []
    actions: list[tuple[str, str, str, str, tuple[int, ...]]] = []

    for turn_number, (question, answer) in enumerate(turns, start=1):
        candidates = _candidate_lines(answer)
        for candidate in candidates:
            key = re.sub(r"\W+", " ", candidate.lower()).strip()
            if key in seen:
                continue
            seen.add(key)
            lowered = candidate.lower()
            if len(takeaways) < 8 and not any(
                phrase in lowered for phrase in _INSUFFICIENT_PHRASES
            ):
                takeaways.append(
                    InsightTakeaway(
                        title=_title(candidate),
                        explanation=candidate[:800],
                        source_turn_numbers=(turn_number,),
                    )
                )

            if any(word in lowered for word in _ACTION_WORDS):
                priority = "high" if any(word in lowered for word in _URGENT_WORDS) else "medium"
                actions.append(
                    (
                        _title(candidate),
                        candidate[:800],
                        priority,
                        "recommendation",
                        (turn_number,),
                    )
                )

        lower_answer = answer.lower()
        if any(phrase in lower_answer for phrase in _INSUFFICIENT_PHRASES):
            cleaned_question = _clean(question)
            actions.append(
                (
                    _title(cleaned_question),
                    "Resolve this open question with additional project evidence.",
                    "high",
                    "open_question",
                    (turn_number,),
                )
            )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    deduplicated_actions: list[tuple[str, str, str, str, tuple[int, ...]]] = []
    action_keys: set[str] = set()
    for action in sorted(actions, key=lambda item: priority_order[item[2]]):
        key = action[0].lower()
        if key not in action_keys:
            action_keys.add(key)
            deduplicated_actions.append(action)

    return ConversationInsights(
        takeaways=tuple(takeaways),
        actions=tuple(
            InsightAction(
                rank=rank,
                title=title,
                rationale=rationale,
                priority=priority,  # type: ignore[arg-type]
                kind=kind,  # type: ignore[arg-type]
                source_turn_numbers=sources,
            )
            for rank, (title, rationale, priority, kind, sources) in enumerate(
                deduplicated_actions[:10], start=1
            )
        ),
    )
