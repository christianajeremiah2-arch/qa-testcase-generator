import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

sections = [
("The problem",
"Software QA engineers spend a large share of their time turning business requirements into detailed test cases by hand. The work is repetitive, slows down test cycles, and coverage depends on who writes the cases and how much time they have. Edge cases and boundary values are often missed under deadline pressure."),
("What I built",
"I built a local prototype that generates structured test cases from a requirement or user story using Meta's Llama 3.1 (8B) model running through Ollama, with Python for the logic and Streamlit for the interface. Each case has an ID, scenario, preconditions, steps, test data, expected result, test type (positive, negative, boundary or validation) and priority. A JSON schema constrains the model's output, and the app validates every response, retries once on invalid output, removes duplicates and warns when a requested test type is missing. Where a requirement is vague, the prompt tells the model to raise a CLARIFY case instead of inventing a rule. The tester edits and ticks each case as reviewed, then downloads the set as Excel, CSV or JSON. Because inference runs locally, requirements do not leave the machine."),
("What I would NOT trust it with",
"I would not trust it to decide what correct behaviour is. It can produce expected results and boundary values that sound right but are wrong, so it cannot replace a tester who knows the business rules. I would not use its output unreviewed for payment, identity, health or other regulated systems, or treat it as proof of full test coverage. Nor would I send confidential client requirements to a cloud model, which is why it runs locally."),
("Which module helped most?",
"Module 1, Section 3 (AI for Your Studies and Projects). The prompting ladder of task, context, audience, constraints, format and examples shaped my system prompt. The hallucination lesson and the \"fast intern, final human\" principle shaped the mandatory review step built into the app."),
]
words = sum(len(re.findall(r"\S+", b)) for _, b in sections)
print("body words:", words)

ink = HexColor("#1F2A37"); accent = HexColor("#0E7C3A"); muted = HexColor("#5B6573")
title = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=ink)
sub = ParagraphStyle("s", fontName="Helvetica", fontSize=10, leading=14, textColor=muted)
h = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=accent, spaceBefore=10, spaceAfter=4)
body = ParagraphStyle("b", fontName="Helvetica", fontSize=10.5, leading=15.5, textColor=ink, alignment=4)

doc = SimpleDocTemplate("Capstone_Artefact_QA_Test_Case_Generator.pdf", pagesize=A4,
    leftMargin=22*mm, rightMargin=22*mm, topMargin=20*mm, bottomMargin=20*mm,
    title="AI-Powered QA Test Case Generator", subject="Meta AI Academy Capstone Artefact")
story = [Paragraph("AI-Powered QA Test Case Generator", title), Spacer(1,3),
         Paragraph("Meta AI Academy Capstone Artefact &nbsp;|&nbsp; Llama 3.1 via Ollama, Python, Streamlit", sub),
         Spacer(1,6), HRFlowable(width="100%", thickness=1, color=accent), Spacer(1,4)]
for head, text in sections:
    story += [Paragraph(head, h), Paragraph(text, body)]
doc.build(story)
