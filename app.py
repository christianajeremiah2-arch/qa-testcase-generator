"""Streamlit UI for the AI-powered QA Test Case Generator.

Run with:  streamlit run app.py
"""
from pathlib import Path

import streamlit as st

from src.exporter import coverage_summary, to_csv, to_dataframe, to_excel, to_json
from src.generator import (ALL_TEST_TYPES, DEFAULT_MODEL, GenerationError,
                           InputError, generate_test_cases)

SAMPLES_DIR = Path(__file__).parent / "samples"

st.set_page_config(page_title="QA Test Case Generator", page_icon="🧪", layout="wide")
st.title("QA Test Case Generator")
st.caption("Llama via Ollama, running locally. Every generated case is a draft until a QA engineer reviews it.")

# ---------- Sidebar settings ----------
with st.sidebar:
    st.header("Settings")
    model = st.text_input("Ollama model", value=DEFAULT_MODEL,
                          help="Any Llama model you have pulled, e.g. llama3.1:8b or llama3.2:3b")
    test_types = st.multiselect("Test types to cover", ALL_TEST_TYPES, default=ALL_TEST_TYPES)
    min_cases, max_cases = st.slider("Number of test cases", 3, 25, (6, 12))
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1,
                            help="Lower is more consistent. Keep it low for test design.")
    samples = sorted(p.name for p in SAMPLES_DIR.glob("*.txt"))
    sample = st.selectbox("Load a sample requirement", ["(none)"] + samples)

# ---------- Requirement input ----------
default_text = (SAMPLES_DIR / sample).read_text() if sample != "(none)" else ""
requirement = st.text_area("Requirement or user story", value=default_text, height=220,
                           placeholder="As a registered user, I want to reset my password so that...")

if st.button("Generate test cases", type="primary", disabled=not test_types):
    with st.spinner(f"Generating with {model}. This can take a minute on a laptop..."):
        try:
            result = generate_test_cases(requirement, test_types=test_types, model=model,
                                         min_cases=min_cases, max_cases=max_cases,
                                         temperature=temperature)
            st.session_state["df"] = to_dataframe(result.test_cases)
            st.session_state["requirement"] = requirement
            st.session_state["warnings"] = result.warnings
            st.session_state["meta"] = f"{len(result.test_cases)} cases from {result.model} (attempt {result.attempts})"
        except InputError as exc:
            st.warning(str(exc))
        except GenerationError as exc:
            st.error(str(exc))

# ---------- Review and export ----------
if "df" in st.session_state:
    df = st.session_state["df"]
    st.success(st.session_state["meta"])
    for w in st.session_state.get("warnings", []):
        st.warning(w)

    cols = st.columns(len(ALL_TEST_TYPES))
    counts = coverage_summary(df)
    for col, t in zip(cols, ALL_TEST_TYPES):
        col.metric(t, counts.get(t, 0))

    st.subheader("Review and edit")
    st.caption("Edit any cell, delete weak rows, add missing ones, and tick Reviewed before you export.")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True,
                            column_config={"Test Steps": st.column_config.TextColumn(width="large"),
                                           "Reviewed": st.column_config.CheckboxColumn()})

    reviewed = int(edited["Reviewed"].sum()) if not edited.empty else 0
    st.write(f"Reviewed: **{reviewed} of {len(edited)}**")
    if reviewed < len(edited):
        st.info("Some cases are not yet reviewed. Exported files will include the Reviewed column so this is visible.")

    c1, c2, c3 = st.columns(3)
    c1.download_button("Download Excel", to_excel(edited, st.session_state["requirement"]),
                       "test_cases.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    c2.download_button("Download CSV", to_csv(edited), "test_cases.csv", "text/csv")
    c3.download_button("Download JSON", to_json(edited), "test_cases.json", "application/json")
