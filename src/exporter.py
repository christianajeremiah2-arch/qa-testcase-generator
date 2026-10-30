"""Converts test cases to a table and to downloadable files."""
import io
import json
from typing import List

import pandas as pd

from .schema import TestCase

COLUMNS = ["Test Case ID", "Scenario", "Preconditions", "Test Steps",
           "Test Data", "Expected Result", "Test Type", "Priority", "Reviewed"]


def to_dataframe(cases: List[TestCase]) -> pd.DataFrame:
    rows = [{
        "Test Case ID": c.test_case_id,
        "Scenario": c.scenario,
        "Preconditions": c.preconditions,
        "Test Steps": "\n".join(f"{i}. {s}" for i, s in enumerate(c.test_steps, 1)),
        "Test Data": c.test_data,
        "Expected Result": c.expected_result,
        "Test Type": c.test_type.value,
        "Priority": c.priority.value,
        "Reviewed": False,
    } for c in cases]
    return pd.DataFrame(rows, columns=COLUMNS)


def to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def to_excel(df: pd.DataFrame, requirement: str = "") -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Test Cases", index=False)
        sheet = writer.sheets["Test Cases"]
        widths = {"A": 12, "B": 45, "C": 35, "D": 55, "E": 35, "F": 45, "G": 12, "H": 10, "I": 10}
        for col, width in widths.items():
            sheet.column_dimensions[col].width = width
        from openpyxl.styles import Alignment, Font
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        if requirement:
            pd.DataFrame({"Source requirement": [requirement]}).to_excel(
                writer, sheet_name="Requirement", index=False)
    return buffer.getvalue()


def to_json(df: pd.DataFrame) -> bytes:
    return json.dumps(df.to_dict(orient="records"), indent=2).encode("utf-8")


def coverage_summary(df: pd.DataFrame) -> dict:
    return df["Test Type"].value_counts().to_dict() if not df.empty else {}
