"""
Milestone 5 — Grounded generation.

Pipeline (see planning.md architecture diagram):
    question -> retrieve top-k chunks -> build grounded prompt -> Groq LLM -> answer + sources

Grounding is enforced two ways:
  1. The system prompt instructs the model to answer ONLY from the provided context and to
     reply with a fixed "not enough information" sentence when the context doesn't cover the
     question (no outside/training knowledge).
  2. Source attribution is guaranteed programmatically — `ask()` returns the source filenames
     of the retrieved chunks regardless of what the model writes, so attribution never depends
     on the LLM remembering to cite.

LLM: Groq llama-3.3-70b-versatile (free tier, OpenAI-compatible). Needs GROQ_API_KEY in .env.
"""

import os

from dotenv import load_dotenv
from groq import Groq

from vector_store import retrieve, TOP_K

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
NO_INFO = "I don't have enough information on that."

SYSTEM_PROMPT = (
    "You are The Unofficial Guide, an assistant that answers questions about Computer Science "
    "professors and courses at the University of Nevada, Reno, using ONLY the student-review "
    "excerpts provided in the CONTEXT.\n"
    "Rules:\n"
    "1. Answer strictly from the CONTEXT. Never use outside or prior knowledge.\n"
    f"2. If the CONTEXT does not contain enough information to answer, reply with exactly this "
    f"sentence and nothing else: \"{NO_INFO}\"\n"
    "3. After each claim, cite the source filename in brackets, e.g. [erin_keith.txt].\n"
    "4. These are subjective student opinions — attribute them as what students say, and be "
    "concise (2-4 sentences)."
)

_client = None


def get_client():
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key or key == "your_key_here":
            raise RuntimeError("GROQ_API_KEY missing — set it in .env")
        _client = Groq(api_key=key)
    return _client


def build_context(hits):
    """Format retrieved chunks into a numbered, source-labeled context block."""
    blocks = []
    for i, h in enumerate(hits, 1):
        blocks.append(f"[{i}] (source: {h['source']})\n{h['text']}")
    return "\n\n".join(blocks)


def ask(question, k=TOP_K):
    """Retrieve, generate a grounded answer, and return answer + sources + retrieved chunks."""
    hits = retrieve(question, k=k)
    context = build_context(hits)

    user_prompt = (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer using only the CONTEXT above, following the rules."
    )

    resp = get_client().chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    answer = resp.choices[0].message.content.strip()

    # Programmatic source attribution: unique source files of the retrieved chunks,
    # in retrieval order. Suppressed when the model declined for lack of info.
    declined = NO_INFO.rstrip(".").lower() in answer.lower()
    sources = []
    if not declined:
        for h in hits:
            if h["source"] not in sources:
                sources.append(h["source"])

    return {
        "answer": answer,
        "sources": sources,
        "declined": declined,
        "chunks": hits,
    }


if __name__ == "__main__":
    tests = [
        "What is the overall quality of Erin Keith on Rate My Professors?",
        "Is attendance mandatory for CS219 in Bashira Akter's course?",
        "What do students say about Sara Davis's pacing?",
        "What is the best dining hall at UNR?",  # out-of-domain — should decline
    ]
    for q in tests:
        print("\n" + "=" * 90)
        print(f"Q: {q}")
        r = ask(q)
        print(f"\nANSWER:\n{r['answer']}")
        print(f"\nSOURCES: {r['sources'] if r['sources'] else '(none — declined)'}")
        print("RETRIEVED:", ", ".join(f"{h['source']}#{h['position']}" for h in r["chunks"]))
