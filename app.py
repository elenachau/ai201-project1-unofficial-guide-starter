"""
Milestone 5 — Gradio interface for The Unofficial Guide.

Run from the project root so the relative chroma_db/ and data/ paths resolve:
    python app.py
Then open http://localhost:7860

Ask a question about UNR CS professors/courses. The system retrieves the most relevant
student-review chunks, generates a grounded answer (Groq llama-3.3-70b-versatile), and shows
which documents the answer was retrieved from.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import gradio as gr
from generate import ask


def handle_query(question):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", "", ""

    result = ask(question)
    answer = result["answer"]

    if result["sources"]:
        sources = "\n".join(f"• {s}" for s in result["sources"])
    else:
        sources = "(no sources — the documents didn't cover this question)"

    # show the actual retrieved chunks so the grounding is inspectable
    retrieved = "\n\n".join(
        f"[{i}] {h['source']} (#{h['position']}, distance {h['distance']:.3f})\n{h['text']}"
        for i, h in enumerate(result["chunks"], 1)
    )
    return answer, sources, retrieved


EXAMPLES = [
    "What is the overall quality of Erin Keith on Rate My Professors?",
    "Is attendance mandatory for CS219 in Bashira Akter's course?",
    "What do students say about Sara Davis's pacing?",
    "Who do students recommend for CS 135, Davis or Keith?",
    "What percent of students would take Papachristos again?",
]

with gr.Blocks(title="The Unofficial Guide — UNR CS") as demo:
    gr.Markdown(
        "# 🎓 The Unofficial Guide — UNR Computer Science\n"
        "Ask about CS professors and courses at the University of Nevada, Reno. "
        "Answers come **only** from student reviews (Rate My Professors + r/unr). "
        "If the reviews don't cover your question, the system will say so."
    )
    inp = gr.Textbox(label="Your question", placeholder="e.g. How hard is CS 135 with Erin Keith?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=6)
    sources = gr.Textbox(label="Retrieved from", lines=3)
    with gr.Accordion("Show retrieved chunks (the evidence)", open=False):
        retrieved = gr.Textbox(label="Top-5 retrieved chunks", lines=12)

    gr.Examples(examples=EXAMPLES, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources, retrieved])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources, retrieved])


if __name__ == "__main__":
    demo.launch()
