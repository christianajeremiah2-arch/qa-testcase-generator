"""Calls Llama through Ollama and returns validated test cases."""
import json
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from pydantic import ValidationError

from .prompts import build_messages
from .schema import TestCase, TestSuite

MIN_REQUIREMENT_CHARS = 30
MAX_REQUIREMENT_CHARS = 6000
DEFAULT_MODEL = "llama3.1:8b"
ALL_TEST_TYPES = ["Positive", "Negative", "Boundary", "Validation"]


class InputError(ValueError):
    """The requirement text is not usable."""


class GenerationError(RuntimeError):
    """The model could not produce valid test cases."""


@dataclass
class GenerationResult:
    test_cases: List[TestCase]
    model: str
    attempts: int
    warnings: List[str] = field(default_factory=list)


def validate_requirement(text: Optional[str]) -> str:
    if text is None or not text.strip():
        raise InputError("Please enter a requirement or user story.")
    cleaned = text.strip()
    if len(cleaned) < MIN_REQUIREMENT_CHARS:
        raise InputError(
            f"The requirement is too short ({len(cleaned)} characters). "
            f"Give at least {MIN_REQUIREMENT_CHARS} characters so the model has enough context.")
    if len(cleaned) > MAX_REQUIREMENT_CHARS:
        raise InputError(
            f"The requirement is too long ({len(cleaned)} characters). "
            f"Split it into smaller stories of up to {MAX_REQUIREMENT_CHARS} characters.")
    if not any(ch.isalpha() for ch in cleaned):
        raise InputError("The requirement must contain readable text.")
    return cleaned


def _default_chat() -> Callable:
    import ollama  # imported here so tests can run without Ollama installed
    return ollama.chat


def _renumber(cases: List[TestCase]) -> List[TestCase]:
    for i, case in enumerate(cases, start=1):
        case.test_case_id = f"TC-{i:03d}"
    return cases


def _dedupe(cases: List[TestCase]) -> List[TestCase]:
    seen, unique = set(), []
    for case in cases:
        key = case.scenario.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(case)
    return unique


def generate_test_cases(
    requirement: str,
    test_types: Optional[List[str]] = None,
    model: str = DEFAULT_MODEL,
    min_cases: int = 6,
    max_cases: int = 12,
    temperature: float = 0.2,
    max_attempts: int = 2,
    chat_fn: Optional[Callable] = None,
) -> GenerationResult:
    requirement = validate_requirement(requirement)
    test_types = test_types or ALL_TEST_TYPES
    chat = chat_fn or _default_chat()
    messages = build_messages(requirement, test_types, min_cases, max_cases)

    last_error = ""
    for attempt in range(1, max_attempts + 1):
        try:
            response = chat(
                model=model,
                messages=messages,
                format=TestSuite.model_json_schema(),
                options={"temperature": temperature},
            )
        except ConnectionError as exc:
            raise GenerationError(
                "Cannot reach Ollama. Start it with 'ollama serve' and try again.") from exc
        except Exception as exc:  # ollama.ResponseError, e.g. model not pulled
            msg = str(exc)
            if "not found" in msg.lower():
                raise GenerationError(
                    f"Model '{model}' is not installed. Run: ollama pull {model}") from exc
            raise GenerationError(f"Ollama returned an error: {msg}") from exc

        content = response["message"]["content"]
        try:
            suite = TestSuite.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)[:300]
            continue

        cases = _dedupe(suite.test_cases)
        if not cases:
            last_error = "The model returned no test cases."
            continue

        warnings = []
        produced = {c.test_type.value for c in cases}
        missing = [t for t in test_types if t not in produced]
        if missing:
            warnings.append(f"No {', '.join(missing)} test cases were produced. Add them manually or regenerate.")
        clarify = [c.test_case_id for c in cases if c.scenario.upper().startswith("CLARIFY")]
        if clarify:
            warnings.append("Some cases flag gaps in the requirement (CLARIFY). Confirm these with the BA or product owner.")
        if len(cases) < min_cases:
            warnings.append(f"Only {len(cases)} test cases were produced (target was {min_cases} or more).")

        return GenerationResult(_renumber(cases), model, attempt, warnings)

    raise GenerationError(
        f"The model did not return valid test cases after {max_attempts} attempts. Last error: {last_error}")
