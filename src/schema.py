"""Data structures for generated test cases.

The same Pydantic models do two jobs:
1. Their JSON schema is passed to Ollama so Llama is constrained to this shape.
2. They validate whatever comes back before the app shows it to the user.
"""
from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


class TestType(str, Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    BOUNDARY = "Boundary"
    VALIDATION = "Validation"


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TestCase(BaseModel):
    test_case_id: str = Field(description="Identifier such as TC-001")
    scenario: str = Field(description="One-line summary of what is being tested")
    preconditions: str = Field(description="State the system must be in before the test")
    test_steps: List[str] = Field(description="Ordered, atomic steps a tester can follow")
    test_data: str = Field(description="Concrete input values used in the steps")
    expected_result: str = Field(description="Observable outcome that decides pass or fail")
    test_type: TestType
    priority: Priority

    @field_validator("scenario", "expected_result")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value.strip()

    @field_validator("test_steps")
    @classmethod
    def has_steps(cls, steps: List[str]) -> List[str]:
        cleaned = [s.strip() for s in steps if s and s.strip()]
        if not cleaned:
            raise ValueError("at least one test step is required")
        return cleaned


class TestSuite(BaseModel):
    test_cases: List[TestCase]
