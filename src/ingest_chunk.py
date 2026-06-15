"""
Milestone 3 — Ingestion + Chunking pipeline for "The Unofficial Guide".

Pipeline (see planning.md architecture diagram):
    1. Load every .txt in documents/ and snapshot the raw text.
    2. Clean each document by source TYPE:
         - Rate My Professors profile  -> strip site chrome, parse header stats + each review.
         - Reddit r/unr thread         -> strip vote/nav boilerplate, parse each comment.
    3. Structure-aware chunking with CONTEXT INJECTION:
         Each logical unit (a review / a comment / a profile summary) is turned into a
         self-contained passage with the professor name + course (or thread title + user)
         prepended, so a retrieved chunk is answerable on its own. Units longer than the
         target chunk size are split with a token-based sliding window.
    4. Inspect: print a cleaned doc, 5 representative + 5 random chunks, total count, stats.

Chunk spec (from planning.md): 256 tokens target, 64 token overlap.
NOTE on spec: 256/64 is applied as the MAX window *within* a single review/comment so that
chunks never merge two different professors or two unrelated comments. Most reviews are
shorter than 256 tokens and stay whole — a complete review is a complete retrievable thought.
This is recorded in planning.md under Chunking Strategy.
"""

import os
import re
import json
import html
import random

DOCS_DIR = "documents"
OUT_DIR = "data"
CLEAN_DIR = os.path.join(OUT_DIR, "cleaned")
RAW_PATH = os.path.join(OUT_DIR, "raw_documents.json")
CHUNKS_PATH = os.path.join(OUT_DIR, "chunks.json")

CHUNK_SIZE = 256      # target tokens per chunk
CHUNK_OVERLAP = 64    # token overlap between adjacent chunks of a long unit

# Known source metadata (from planning.md). Encoding the thread titles / professor pages
# here is more reliable than guessing them from the messy exported text.
SOURCE_META = {
    "erin_keith.txt":      {"type": "rmp",    "url": "https://www.ratemyprofessors.com/professor/2264014"},
    "sara_davis.txt":      {"type": "rmp",    "url": "https://www.ratemyprofessors.com/professor/2575540"},
    "papachristos.txt":    {"type": "rmp",    "url": "https://www.ratemyprofessors.com/professor/2245066"},
    "bashira_akter.txt":   {"type": "rmp",    "url": "https://www.ratemyprofessors.com/professor/2825729"},
    "cs135.txt":           {"type": "reddit", "title": "CS 135",
                            "url": "https://www.reddit.com/r/unr/comments/h9v9cz/cs_135/"},
    "davis_vs_keith.txt":  {"type": "reddit", "title": "CS 135 - Professor Davis or Keith?",
                            "url": "https://www.reddit.com/r/unr/comments/dvh9mx/cs_135_professor_davis_or_keith/"},
    "keith_vs_siming.txt": {"type": "reddit", "title": "CS135 Erin Keith Vs Siming",
                            "url": "https://www.reddit.com/r/unr/comments/8wdzw7/cs135_erin_keith_vs_siming/"},
    "how_CS_department.txt": {"type": "reddit", "title": "How is the CS department here?",
                            "url": "https://www.reddit.com/r/unr/comments/e44kg7/how_is_the_cs_department_here/"},
    "cse_program_unr.txt": {"type": "reddit", "title": "How is the computer science/engineering program at UNR?",
                            "url": "https://www.reddit.com/r/unr/comments/1h1pybh/how_is_the_computer_scienceengineering_program_at/"},
    "davis_rant.txt":      {"type": "reddit", "title": "CS202 Sara Davis Rant",
                            "url": "https://www.reddit.com/r/unr/comments/1e482bt/cs202_sara_davis_rant/"},
}


# --------------------------------------------------------------------------------------
# Tokenizer: prefer the real bge-m3 tokenizer (matches our embedding model). Fall back to
# a word-based estimate if it can't be loaded (no network / offline).
# --------------------------------------------------------------------------------------
def make_token_counter():
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained("BAAI/bge-m3")
        return (lambda s: len(tok.encode(s, add_special_tokens=False))), "bge-m3 tokenizer"
    except Exception as e:
        print(f"[tokenizer] bge-m3 unavailable ({type(e).__name__}); using word-based estimate.")
        # bge-m3 (multilingual) averages ~1.3 tokens / whitespace-word on English text.
        return (lambda s: max(1, round(len(s.split()) * 1.3))), "word-based estimate (x1.3)"


# --------------------------------------------------------------------------------------
# Generic cleaning helpers
# --------------------------------------------------------------------------------------
def basic_clean(text):
    """Decode HTML entities, strip any stray tags, normalize whitespace. Defensive even
    though these exports are mostly plain text."""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)        # strip HTML tags if any slipped in
    text = text.replace("​", "").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


AGO_RE = re.compile(r"^\s*(?:\d+\s*(?:y|yr|yrs|year|years|mo|month|months|w|wk|week|weeks|"
                    r"d|day|days|h|hr|hours|min|minutes)\s*ago|edited.*ago)\s*$", re.I)
MORE_REPLIES_RE = re.compile(r"^\s*\d+\s+more\s+repl(?:y|ies)\s*$", re.I)
BARE_INT_RE = re.compile(r"^-?\d+$")

REDDIT_BOILER = {
    "upvote", "downvote", "reply", "share", "go to comments", "join the conversation",
    "sort by:", "best", "search comments", "expand comment search", "comments section",
    "•", "op", "award", "report", "save", "follow",
}
DELETED_MARKERS = {
    "comment removed by moderator", "comment deleted by user", "[deleted]", "[removed]",
    "sorry, this post was deleted by the person who originally posted it.",
}


def is_reddit_boiler(line):
    s = line.strip().lower()
    if not s:
        return True
    if s in REDDIT_BOILER:
        return True
    if s in DELETED_MARKERS:           # "Sorry, this post was deleted...", "[deleted]"
        return True
    if BARE_INT_RE.match(s):           # bare vote counts
        return True
    if s.endswith(" avatar"):          # "u/handle avatar"
        return True
    if AGO_RE.match(s):
        return True
    if MORE_REPLIES_RE.match(s):
        return True
    return False


# --------------------------------------------------------------------------------------
# Rate My Professors parser
# --------------------------------------------------------------------------------------
META_KEYS = {"for credit", "attendance", "would take again", "grade", "textbook",
             "online class", "reviewed", "for credit:"}

# A review block begins with the 4-line Quality/<n>/Difficulty/<n> stanza.
REVIEW_RE = re.compile(r"(?m)^Quality\s*$\n^([\d.]+)\s*$\n^Difficulty\s*$\n^([\d.]+)\s*$")
TAG_THUMBS_RE = re.compile(r"^thumbs\s+(up|down)$", re.I)


def parse_rmp(raw, source):
    text = html.unescape(raw)
    header = {}

    m = re.search(r"^\s*([\d.]+)\s*\n\s*/\s*5", text)
    header["quality"] = m.group(1) if m else None
    m = re.search(r"Based on\s+(\d+)\s+ratings", text)
    header["n_ratings"] = m.group(1) if m else None
    m = re.search(r"(\d+)%\s*\n\s*Would take again", text)
    header["would_take_again"] = (m.group(1) + "%") if m else None
    m = re.search(r"([\d.]+)\s*\n\s*Level of Difficulty", text)
    header["difficulty"] = m.group(1) if m else None
    m = re.search(r"\n([^\n]+)\nProfessor in the ([^\n]+) department", text)
    header["professor"] = basic_clean(m.group(1)) if m else source.replace(".txt", "")
    header["department"] = basic_clean(m.group(2)) if m else "Computer Science"

    prof = header["professor"]
    units = []

    # Summary unit — carries the page-level stats (answers "overall quality / % take again").
    summary = (
        f"[Rate My Professors profile — {prof}, {header['department']} department, "
        f"University of Nevada - Reno] "
        f"Overall quality {header['quality']}/5 based on {header['n_ratings']} ratings. "
        f"{header['would_take_again']} of students would take {prof} again. "
        f"Level of difficulty {header['difficulty']}/5."
    )
    units.append({
        "source": source, "type": "rmp", "unit": "profile_summary",
        "professor": prof, "course": None, "text": basic_clean(summary),
    })

    # Individual reviews.
    matches = list(REVIEW_RE.finditer(text))
    for i, mt in enumerate(matches):
        start = mt.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        lines = [ln.strip() for ln in block.split("\n")]
        # lines[0..3] = Quality / q / Difficulty / d
        quality, difficulty = mt.group(1), mt.group(2)
        rest = [ln for ln in lines[4:]]

        # course (strip leading "Computer Icon"), then date
        rest = [ln for ln in rest if ln != ""]
        if not rest:
            continue
        course = re.sub(r"^Computer Icon", "", rest[0]).strip()
        date = rest[1] if len(rest) > 1 else ""

        meta = {}
        idx = 2
        while idx < len(rest):
            ln = rest[idx]
            if ":" in ln and ln.split(":", 1)[0].strip().lower() in META_KEYS:
                k, v = ln.split(":", 1)
                meta[k.strip()] = v.strip()
                idx += 1
            else:
                break

        # review body = first non-tag/thumbs line after the meta fields
        review_text = ""
        if idx < len(rest) and not TAG_THUMBS_RE.match(rest[idx]):
            review_text = rest[idx]
            idx += 1

        # remaining lines until "Thumbs ..." are tags
        tags = []
        while idx < len(rest):
            ln = rest[idx]
            if TAG_THUMBS_RE.match(ln):
                break
            tags.append(ln)
            idx += 1

        if not review_text:
            continue  # block had no substantive review text

        att = meta.get("Attendance", "")
        grade = meta.get("Grade", "")
        passage = (
            f"[Rate My Professors review — {prof}, course {course}] "
            f"Quality {quality}/5, Difficulty {difficulty}/5"
            + (f". Attendance: {att}" if att else "")
            + (f". Grade: {grade}" if grade else "")
            + f". Review: {review_text}"
            + (f" Student tags: {', '.join(tags)}." if tags else "")
        )
        units.append({
            "source": source, "type": "rmp", "unit": "review",
            "professor": prof, "course": course, "date": date,
            "quality": quality, "difficulty": difficulty,
            "text": basic_clean(passage),
        })

    return units


# --------------------------------------------------------------------------------------
# Reddit thread parser
# --------------------------------------------------------------------------------------
def _clean_username(line):
    s = line.strip()
    s = re.sub(r"\s+avatar$", "", s)
    s = re.sub(r"^u/", "", s)
    return s.strip()


def _clean_body(lines):
    kept = [basic_clean(ln) for ln in lines if not is_reddit_boiler(ln)]
    kept = [ln for ln in kept if ln]
    return " ".join(kept).strip()


def parse_reddit(raw, source, title):
    lines = [ln.rstrip() for ln in html.unescape(raw).split("\n")]
    n = len(lines)

    # anchors: index of a "•" immediately followed by an "X ago" line
    anchors = [i for i in range(n - 1) if lines[i].strip() == "•" and AGO_RE.match(lines[i + 1].strip())]

    units = []

    def add_comment(user, body):
        body = body.strip()
        if len(body) < 15 or body.lower() in DELETED_MARKERS:
            return
        passage = f"[Reddit r/unr discussion — \"{title}\"] {user or 'anonymous'}: {body}"
        units.append({
            "source": source, "type": "reddit", "unit": "comment",
            "professor": None, "course": None, "user": user or "anonymous",
            "text": basic_clean(passage),
        })

    # Pre-anchor region (post body / top text before the first threaded comment).
    # Trim the trailing username block (avatar + bare handle + "OP") that precedes the
    # first anchor so it doesn't leak into the post body.
    first = anchors[0] if anchors else n
    pre_end = first
    while pre_end > 0:
        s = lines[pre_end - 1].strip()
        handle_like = s and " " not in s and len(s) < 30  # bare username, no spaces
        if is_reddit_boiler(s) or handle_like:
            pre_end -= 1
        else:
            break
    pre = _clean_body(lines[:pre_end])
    # drop the title if it leads the pre-region
    if pre.lower().startswith(title.lower()):
        pre = pre[len(title):].strip(" -–—:")
    if len(pre) >= 40:
        add_comment("original post", pre)

    for k, a in enumerate(anchors):
        # username: line before "•", skipping an "OP" marker
        u = a - 1
        while u >= 0 and lines[u].strip().lower() in {"op", ""}:
            u -= 1
        user = _clean_username(lines[u]) if u >= 0 else "anonymous"

        body_start = a + 2  # skip "•" and the ago line
        while body_start < n and (lines[body_start].strip().lower() in {"op", ""}
                                  or AGO_RE.match(lines[body_start].strip())):
            body_start += 1

        # body ends just before the next anchor's username block (or EOF)
        body_end = anchors[k + 1] if k + 1 < len(anchors) else n
        if k + 1 < len(anchors):
            # trim back over the next comment's username/avatar lines
            j = body_end - 1
            while j > body_start and (is_reddit_boiler(lines[j])
                                      or lines[j].strip() and not lines[j].strip()[0].isspace()):
                # stop once we've stepped past the short handle/avatar lines
                if not is_reddit_boiler(lines[j]) and len(lines[j].strip()) > 40:
                    break
                j -= 1
            body_end = j + 1

        add_comment(user, _clean_body(lines[body_start:body_end]))

    return units


# --------------------------------------------------------------------------------------
# Chunking: token-based sliding window, only splits units longer than CHUNK_SIZE.
# --------------------------------------------------------------------------------------
def split_unit(text, count_tokens, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    if count_tokens(text) <= size:
        return [text]
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        end = start
        while end < len(words) and count_tokens(" ".join(words[start:end + 1])) <= size:
            end += 1
        if end == start:
            end = start + 1
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        # step back ~overlap tokens for the next window
        j = end
        while j > start + 1 and count_tokens(" ".join(words[j:end])) < overlap:
            j -= 1
        start = max(j, start + 1)
    return chunks


# --------------------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------------------
def main():
    count_tokens, tok_name = make_token_counter()
    print(f"[tokenizer] using: {tok_name}\n")

    files = sorted(f for f in os.listdir(DOCS_DIR) if f.endswith(".txt"))
    raw_snapshot, all_units = [], []

    for fname in files:
        meta = SOURCE_META.get(fname, {"type": "reddit", "title": fname})
        with open(os.path.join(DOCS_DIR, fname), encoding="utf-8") as fh:
            raw = fh.read()
        raw_snapshot.append({"source": fname, "type": meta["type"], "raw_text": raw})

        if meta["type"] == "rmp":
            units = parse_rmp(raw, fname)
        else:
            units = parse_reddit(raw, fname, meta.get("title", fname))

        # write a cleaned, human-readable version for inspection
        with open(os.path.join(CLEAN_DIR, fname), "w", encoding="utf-8") as out:
            out.write(f"# {fname}  ({meta['type']})  — {len(units)} units\n\n")
            out.write("\n\n".join(u["text"] for u in units))

        print(f"  {fname:24s} type={meta['type']:6s} units={len(units)}")
        all_units.extend(units)

    with open(RAW_PATH, "w", encoding="utf-8") as fh:
        json.dump(raw_snapshot, fh, indent=2, ensure_ascii=False)

    # ---- chunk every unit ----
    chunks = []
    for u in all_units:
        for piece in split_unit(u["text"], count_tokens):
            piece = piece.strip()
            if len(piece) == 0:                       # guard: no empty chunks
                continue
            c = {k: v for k, v in u.items() if k != "text"}
            c["text"] = piece
            c["n_tokens"] = count_tokens(piece)
            chunks.append(c)
    for i, c in enumerate(chunks):
        c["id"] = f"chunk_{i:04d}"

    with open(CHUNKS_PATH, "w", encoding="utf-8") as fh:
        json.dump(chunks, fh, indent=2, ensure_ascii=False)

    # ---------------------------------- INSPECTION ----------------------------------
    print("\n" + "=" * 80)
    print("CLEANED DOCUMENT SAMPLE — erin_keith.txt (read this: any nav/HTML left?)")
    print("=" * 80)
    with open(os.path.join(CLEAN_DIR, "erin_keith.txt"), encoding="utf-8") as fh:
        print("\n".join(fh.read().splitlines()[:14]))

    tokcounts = [c["n_tokens"] for c in chunks]
    print("\n" + "=" * 80)
    print(f"TOTAL CHUNKS: {len(chunks)}   (target band: 50–2000)")
    print(f"tokens/chunk: min={min(tokcounts)} max={max(tokcounts)} "
          f"avg={sum(tokcounts)/len(tokcounts):.0f}")
    bytype = {}
    for c in chunks:
        bytype[c["type"]] = bytype.get(c["type"], 0) + 1
    print(f"by type: {bytype}")
    empties = sum(1 for c in chunks if not c["text"].strip())
    htmlish = sum(1 for c in chunks if re.search(r"<[^>]+>|&\w+;", c["text"]))
    tiny = sum(1 for c in tokcounts if c < 10)
    print(f"sanity -> empty:{empties}  html_artifacts:{htmlish}  under_10_tokens:{tiny}")

    print("\n" + "=" * 80)
    print("5 REPRESENTATIVE CHUNKS (1 summary, 2 RMP reviews, 2 reddit comments)")
    print("=" * 80)
    reps = []
    reps += [c for c in chunks if c.get("unit") == "profile_summary"][:1]
    reps += [c for c in chunks if c.get("unit") == "review"][:2]
    reps += [c for c in chunks if c.get("unit") == "comment"][:2]
    for c in reps:
        print(f"\n--- {c['id']}  [{c['source']} | {c.get('unit')} | {c['n_tokens']} tok] ---")
        print(c["text"])

    print("\n" + "=" * 80)
    print("CHECKPOINT — 5 RANDOM CHUNKS (self-contained? readable? attributed?)")
    print("=" * 80)
    random.seed(42)
    for c in random.sample(chunks, 5):
        print(f"\n--- {c['id']}  [{c['source']} | {c.get('unit')} | {c['n_tokens']} tok] ---")
        print(c["text"])

    print(f"\n[done] raw -> {RAW_PATH}   cleaned -> {CLEAN_DIR}/   chunks -> {CHUNKS_PATH}")


if __name__ == "__main__":
    main()
