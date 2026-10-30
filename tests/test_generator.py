"""Tests run without Ollama: a fake chat function stands in for the model."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.exporter import to_csv, to_dataframe, to_excel  # noqa: E402
from src.generator import (GenerationError, InputError,  # noqa: E402
                           generate_test_cases, validate_requirement)

REQ = "As a user I want to log in with email and password so that I can see my dashboard."


def case(i, ttype="Positive", scenario=None):
    return {"test_case_id": f"X{i}", "scenario": scenario or f"Scenario {i}",
            "preconditions": "User exists", "test_steps": ["Open page", "Click login"],
            "test_data": "a@b.com", "expected_result": "Dashboard shows",
            "test_type": ttype, "priority": "High"}


def fake_chat(payloads):
    calls = iter(payloads)

    def _chat(**kwargs):
        item = next(calls)
        if isinstance(item, Exception):
            raise item
        return {"message": {"content": item if isinstance(item, str) else json.dumps(item)}}
    return _chat


# ---- Input validation ----
@pytest.mark.parametrize("bad", [None, "", "   ", "too short", "1234567890" * 4, "x" * 7000])
def test_invalid_inputs_rejected(bad):
    with pytest.raises(InputError):
        validate_requirement(bad)


def test_valid_input_is_trimmed():
    assert validate_requirement(f"  {REQ}  ") == REQ


# ---- Generation ----
def test_happy_path_renumbers_ids():
    data = {"test_cases": [case(1), case(2, "Negative"), case(3, "Boundary"), case(4, "Validation")]}
    result = generate_test_cases(REQ, chat_fn=fake_chat([data]), min_cases=4)
    assert [c.test_case_id for c in result.test_cases] == ["TC-001", "TC-002", "TC-003", "TC-004"]
    assert result.warnings == []


def test_retry_after_invalid_json():
    data = {"test_cases": [case(1), case(2, "Negative"), case(3, "Boundary"), case(4, "Validation")]}
    result = generate_test_cases(REQ, chat_fn=fake_chat(["not json", data]), min_cases=4)
    assert result.attempts == 2


def test_fails_after_max_attempts():
    with pytest.raises(GenerationError):
        generate_test_cases(REQ, chat_fn=fake_chat(["bad", "{}"]))


def test_missing_types_and_duplicates_flagged():
    data = {"test_cases": [case(1), case(2, scenario="Scenario 1")]}
    result = generate_test_cases(REQ, chat_fn=fake_chat([data]), min_cases=1)
    assert len(result.test_cases) == 1
    assert any("Negative" in w for w in result.warnings)


def test_invalid_enum_triggers_retry_then_error():
    bad = {"test_cases": [case(1, "Smoke")]}
    with pytest.raises(GenerationError):
        generate_test_cases(REQ, chat_fn=fake_chat([bad, bad]))


def test_connection_error_message():
    with pytest.raises(GenerationError, match="ollama serve"):
        generate_test_cases(REQ, chat_fn=fake_chat([ConnectionError("refused")]))


def test_model_not_found_message():
    with pytest.raises(GenerationError, match="ollama pull"):
        generate_test_cases(REQ, chat_fn=fake_chat([Exception("model 'x' not found")]))


# ---- Export ----
def test_exports():
    data = {"test_cases": [case(1), case(2, "Negative")]}
    result = generate_test_cases(REQ, chat_fn=fake_chat([data]), min_cases=1)
    df = to_dataframe(result.test_cases)
    assert "1. Open page" in df.loc[0, "Test Steps"]
    assert to_csv(df).startswith(b"Test Case ID")
    assert to_excel(df, REQ)[:2] == b"PK"  # xlsx is a zip file
