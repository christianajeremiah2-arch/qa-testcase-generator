# AI-Powered QA Test Case Generator

A local prototype that turns software requirements and user stories into structured test cases (positive, negative, boundary and validation) using Meta's Llama model through Ollama, with a Streamlit interface for human review and export to Excel, CSV and JSON.

Capstone project, Meta AI Academy.

---

## Project structure

```
qa-testcase-generator/
├── app.py                  Streamlit interface
├── src/
│   ├── schema.py           Pydantic models (test case shape, enforced on Llama's output)
│   ├── prompts.py          Prompt built on the course's prompting ladder
│   ├── generator.py        Input validation, Ollama call, retry, checks
│   └── exporter.py         Table, Excel, CSV, JSON export
├── samples/                Sample requirements (incl. one deliberately vague one)
├── tests/                  Pytest suite (runs without Ollama)
├── evaluation/             Evaluation sheet to fill in
└── requirements.txt
```

---

## Step-by-step build guide

### Step 1. Install Ollama and pull a Llama model
1. Download Ollama from https://ollama.com and install it.
2. Pull a model:
   ```bash
   ollama pull llama3.1:8b     # better quality, needs about 8 GB RAM
   ollama pull llama3.2:3b     # lighter option for low-spec laptops
   ```
3. Confirm it runs: `ollama run llama3.1:8b "Say hello"`.

Ollama starts a local server on port 11434. Your requirements never leave your machine, which matters if you test with real client requirements.

### Step 2. Set up the Python project
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3. Define the output shape first (`src/schema.py`)
Decide what a test case looks like before writing any prompt: ID, scenario, preconditions, steps, test data, expected result, test type, priority. The Pydantic model is passed to Ollama as a JSON schema (structured outputs), so Llama is constrained to that shape, and the same model validates what comes back. This is what makes the output reliable enough to export.

### Step 4. Write the prompt (`src/prompts.py`)
The system prompt follows the course's prompting ladder:
- **Task:** turn the requirement into test cases.
- **Context:** cases will be reviewed, then executed or automated.
- **Audience and tone:** a tester new to the feature.
- **Constraints:** test only what is stated; mark gaps as `CLARIFY:` rather than invent limits; observable expected results; concrete test data; at/below/above for boundaries.
- **Format:** JSON matching the schema.
- **Example:** one good test case.

The `CLARIFY` rule is the main defence against hallucinated business rules.

### Step 5. Build the generator (`src/generator.py`)
It handles, in order:
1. **Input validation:** empty, too short (< 30 chars), too long (> 6,000 chars), no readable text.
2. **The model call:** `ollama.chat(..., format=TestSuite.model_json_schema(), options={"temperature": 0.2})`. Low temperature gives more consistent output.
3. **Error handling:** Ollama not running, model not pulled, invalid JSON. Invalid output is retried once, then a clear error is shown.
4. **Post-checks:** duplicate scenarios removed, IDs renumbered TC-001 onwards, warnings when a requested test type is missing or CLARIFY cases appear.

### Step 6. Build the interface (`app.py`)
Run `streamlit run app.py`. The page has settings in the sidebar, a requirement box with sample loader, coverage counts per test type, an editable table with a **Reviewed** tick-box, and download buttons. The Reviewed column goes into the export, so anyone receiving the file can see what a human has checked.

### Step 7. Test the application
```bash
pytest -q
```
The suite uses a fake model, so it runs without Ollama. It covers invalid inputs, valid output, retry after bad JSON, failure after repeated bad output, an invalid test type, Ollama offline, model missing, duplicates, and export formats.

Then test manually:
- Each file in `samples/`.
- `04_ambiguous.txt`: check that the model raises CLARIFY cases instead of inventing a size limit.
- Stop Ollama and click Generate: confirm the error message.
- Enter a wrong model name: confirm the "ollama pull" message.

### Step 8. Evaluate output quality
Fill in `evaluation/evaluation_sheet.csv` for each sample. For every generated case judge: is it relevant to the requirement, does it invent a rule, are boundary values correct (e.g. NGN 99, 100, 101), can a tester follow the steps. Also record time to review and fix against time to write manually. These numbers are your evidence; do not report a time saving you have not measured.

If you have time, compare `llama3.1:8b` against `llama3.2:3b` on the same requirements.

### Step 9. Version control and documentation
```bash
git init
git add .
git commit -m "Initial prototype: Llama test case generator"
git branch -M main
git remote add origin https://github.com/<your-username>/qa-testcase-generator.git
git push -u origin main
```
Add screenshots of the app and your filled evaluation sheet to the repository.

### Step 10. Prepare the submission
- A short demo (screen recording) showing a requirement, generated cases, an edit, and the download.
- Results from the evaluation sheet.
- The 300-word artefact (see `artefact/`).

---

## Limitations
- Output quality depends on how complete the requirement is.
- Llama can still produce plausible but wrong expected results and boundary values. Every case needs review.
- Not suitable as the only source of test design for regulated or safety-critical systems.
- Generation speed depends on your hardware.
