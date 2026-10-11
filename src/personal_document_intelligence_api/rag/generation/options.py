from dataclasses import dataclass
from typing import Literal

ReasoningEffort = Literal["none", "low", "medium", "high", "xhigh", "max"]


@dataclass(frozen=True)
class GenerationOptions:
    model: str
    reasoning_effort: ReasoningEffort


@dataclass(frozen=True)
class GenerationModel:
    id: str
    label: str
    reasoning_efforts: tuple[ReasoningEffort, ...]
    default_effort: ReasoningEffort = "medium"


# Capabilities verified against the official OpenAI model pages on 2026-10-11.
GENERATION_MODELS = {
    model.id: model
    for model in (
        GenerationModel(
            "gpt-6-luna", "GPT-6 Luna", ("none", "low", "medium", "high", "xhigh", "max")
        ),
        GenerationModel(
            "gpt-6-sol", "GPT-6 Sol", ("none", "low", "medium", "high", "xhigh", "max")
        ),
        GenerationModel("gpt-6-astra", "GPT-6 Astra", ("low", "medium", "high", "xhigh", "max")),
    )
}


def resolve_generation_options(
    *,
    model: str | None,
    reasoning_effort: ReasoningEffort | None,
    allowed_models: list[str],
    default_model: str,
    default_effort: ReasoningEffort,
) -> GenerationOptions:
    selected_model = model or default_model
    if selected_model not in allowed_models or selected_model not in GENERATION_MODELS:
        raise ValueError("The selected answer model is not available.")
    spec = GENERATION_MODELS[selected_model]
    effort = reasoning_effort or (
        default_effort if selected_model == default_model else spec.default_effort
    )
    if effort not in spec.reasoning_efforts:
        raise ValueError(f"{spec.label} does not support '{effort}' reasoning effort.")
    return GenerationOptions(selected_model, effort)
