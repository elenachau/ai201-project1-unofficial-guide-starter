# The Unofficial Guide — Project 1

A small RAG system that answers questions about Computer Science professors and courses at the
University of Nevada, Reno, using only real student reviews from Rate My Professors and the r/unr
subreddit.

---

## Domain

The domain I chose was student reviews of CS professors at the University of Nevada, Reno for
incoming freshman. This knowledge is valuable since the course catalog tells you what a class
covers, but it does not tell you what the professor is actually like to learn from. The reviews
are directly from student experiences, so it is peer to peer and feels more trustworthy than the
official description. It is also hard to find through official channels since a school is not
going to publish that a professor rants off topic or grades slowly, but students will say it.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Erin Keith — Rate My Professors profile | RMP profile | documents/erin_keith.txt — https://www.ratemyprofessors.com/professor/2264014 |
| 2 | Sara Davis — Rate My Professors profile | RMP profile | documents/sara_davis.txt — https://www.ratemyprofessors.com/professor/2575540 |
| 3 | Christos Papachristos — Rate My Professors profile | RMP profile | documents/papachristos.txt — https://www.ratemyprofessors.com/professor/2245066 |
| 4 | Bashira Akter — Rate My Professors profile | RMP profile | documents/bashira_akter.txt — https://www.ratemyprofessors.com/professor/2825729 |
| 5 | r/unr "CS 135 - Professor Davis or Keith?" | Reddit thread | documents/davis_vs_keith.txt — https://www.reddit.com/r/unr/comments/dvh9mx/cs_135_professor_davis_or_keith/ |
| 6 | r/unr "CS135 Erin Keith Vs Siming" | Reddit thread | documents/keith_vs_siming.txt — https://www.reddit.com/r/unr/comments/8wdzw7/cs135_erin_keith_vs_siming/ |
| 7 | r/unr "How is the CS department here?" | Reddit thread | documents/how_CS_department.txt — https://www.reddit.com/r/unr/comments/e44kg7/how_is_the_cs_department_here/ |
| 8 | r/unr "How is the computer science/engineering program at UNR?" | Reddit thread | documents/cse_program_unr.txt — https://www.reddit.com/r/unr/comments/1h1pybh/how_is_the_computer_scienceengineering_program_at/ |
| 9 | r/unr "CS 135" | Reddit thread | documents/cs135.txt — https://www.reddit.com/r/unr/comments/h9v9cz/cs_135/ |
| 10 | r/unr "CS202 Sara Davis Rant" | Reddit thread | documents/davis_rant.txt — https://www.reddit.com/r/unr/comments/1e482bt/cs202_sara_davis_rant/ |

I collected the text by hand into plain .txt files instead of scraping, since Rate My Professors
is JavaScript rendered and Reddit blocks a lot of requests. The four RMP profiles cover the
header stats plus every individual review, and the six Reddit threads cover the peer discussion
side like how hard CS 135 is, who to take it with, and the rant about the summer pace of CS 202.

---

## Chunking Strategy

**Chunk size:** 256 tokens

**Overlap:** 64 tokens

**Why these choices fit your documents:**
My sources are mostly short reviews and short comments, so I used 256 tokens to keep a chunk
small enough that it does not get diluted with unrelated text, but big enough to hold one full
review or comment. I used 64 tokens of overlap so that if a longer review does get split, the
ideas at the boundary are not cut in half.

The important part is how I applied it. Instead of sliding a 256 token window blindly across the
whole file, I apply the window inside each logical unit, which is one RMP review, one Reddit
comment, or one profile stats summary. The reason is that a raw review body never says the
professor name, it just says something like "She rants off topic", so a plain chunk would not be
answerable on its own. Before chunking I rebuild each unit into a self contained passage and
inject the context. For Rate My Professors I add the professor name, the course, and the rating.
For the Reddit threads I add the thread title and the username. Most reviews are shorter than 256
tokens so they stay as one chunk, since a full review is already a complete thought, and only the
longer units get split with the overlap. Cleaning removed the site boilerplate (vote counts,
Reply/Share, nav menus, the "Sorry this post was deleted" notice, deleted/removed comments) and
decoded HTML entities.

**Final chunk count:** 98 chunks across the 10 documents (50 from Rate My Professors, 48 from
Reddit). The smallest chunk is 23 tokens, the largest is 256, and the average is 114. There were
0 empty chunks, 0 chunks with leftover HTML, and 0 chunks under 10 tokens.

### Sample chunks (5 labeled, with source document)

**Chunk 1 — source: erin_keith.txt (RMP review, 133 tokens)**
> [Rate My Professors review — Erin Keith, course CS135] Quality 4.0/5, Difficulty 2.0/5.
> Attendance: Mandatory. Grade: B-. Review: Erin is such a kind professor that actually wants her
> students to succeed. She rubs people the wrong way because she gets annoyed about silly things
> but i don't think that takes away from her credibility. She is incredibly educated and
> knowledgeable in the field and explains the concepts in a way that is easily digestible.
> Student tags: EXTRA CREDIT, Gives good feedback, Caring, Helpful.

**Chunk 2 — source: bashira_akter.txt (RMP review, 139 tokens)**
> [Rate My Professors review — Bashira Akter, course CS219] Quality 2.0/5, Difficulty 2.0/5.
> Attendance: Not Mandatory. Grade: A. Review: Lectures are an hour of rambling. Slides are more
> useful than the lecture itself and they are all posted online. Projects took multiple months to
> be graded, and project descriptions are vague and unclear. Almost every question or assignment
> was filled with typos and grammatical errors. Very little thought put into assignments. Student
> tags: Beware of pop quizzes, Lecture heavy, Graded by few things, Helpful.

**Chunk 3 — source: sara_davis.txt (RMP review, 141 tokens)**
> [Rate My Professors review — Sara Davis, course CS302] Quality 3.0/5, Difficulty 4.0/5.
> Attendance: Not Mandatory. Grade: Not sure yet. Review: data structures is a mediumish class
> when it comes to difficulty. it isn't that hard but sara does start randomly coding in class,
> but the lecture slides are pretty straightforward and they help a lot (she reuses erin's slides)
> intimidating, gets really pissed for asking clarifying questions (which i get because people do
> ask weird ones). Student tags: Tough grader, Lecture heavy, Test heavy, Helpful.

**Chunk 4 — source: papachristos.txt (RMP profile summary, 60 tokens)**
> [Rate My Professors profile — Christos Papachristos, Computer Engineering department, University
> of Nevada - Reno] Overall quality 2.6/5 based on 21 ratings. 39% of students would take Christos
> Papachristos again. Level of difficulty 3.9/5.

**Chunk 5 — source: cs135.txt (Reddit comment, 254 tokens)**
> [Reddit r/unr discussion — "CS 135"] stephantn: Hi I'm not sure what your major is but like most
> people have said, 135 tends to be a weed out class. For some people, it's pretty easy but I'd say
> a majority of the class tends to struggle with it. It's very common for people to take this class
> twice and there are a lot of resources to help you but you need to find them and be aware of
> them. The information, at first, is very overwhelming especially if you've never coded before.
> [...] If you are an engineering (specifically CS, EE, BME), math, or physics major then I can see
> why your advisor recommended this course for you. Otherwise, you're taking this for fun.

Each chunk leads with an injected context label in brackets so it carries its own professor/course
or thread/user attribution, which is what makes it answerable on its own.

---

## Embedding Model

**Model used:** all-MiniLM-L6-v2 (sentence-transformers), stored in ChromaDB with cosine
distance. I first planned bge-m3 in planning.md but switched to MiniLM, since it is the
lightweight local default at about 80MB instead of 2.3GB, runs on CPU with no API key and no rate
limits, and my data is short English reviews that do not need the multilingual or hybrid features
bge-m3 adds. I normalize the embeddings so cosine distance stays between 0 and 2.

**Production tradeoff reflection:**
If I deployed this for real users and cost was not a constraint, the main tradeoff would be
latency versus accuracy. A bigger model like bge-m3 has a longer context length and stronger
retrieval, which would help on the questions where MiniLM was weak (see the failure case below),
but it is heavier and slower to run. There is also multilingual support to think about. If
reviews came in from platforms in other languages, a multilingual model would let me serve more
students, but it adds computation overhead and some users only want English. So I would weigh
whether to spend the model capacity on accuracy, on multilingual coverage, or on keeping latency
low.

---

## Retrieval Test Results

I queried the ChromaDB store directly (before generation) at top-k 5. Distances are cosine, so
lower is closer. These are the real top results.

**Query A: "What is the overall quality of Erin Keith on Rate My Professors?"**
| rank | distance | source | chunk preview |
|---|---|---|---|
| 1 | 0.290 | erin_keith.txt | review: "Erin is such a kind professor that actually wants her students to succeed..." |
| 2 | 0.302 | erin_keith.txt | profile summary: "Overall quality 2.8/5 based on 172 ratings. 50% would take again..." |
| 3 | 0.319 | erin_keith.txt | review: "Erin is cool but she gets easily sidetracked..." |
| 4 | 0.342 | erin_keith.txt | review (CS333): "Erin Keith is a fantastic professor..." |
| 5 | 0.354 | davis_vs_keith.txt | comment: "Ms Erin is kind of a badass. Actually teach you extra stuff..." |

*Why these are relevant:* Four of the five chunks come from erin_keith.txt, the exact professor
asked about, and rank 2 is the profile summary that holds the literal answer (2.8/5 based on 172
ratings). The embeddings matched on the professor name plus the quality/rating language, and every
chunk is on-topic with a top distance of 0.290, well under 0.5.

**Query B: "What percent of students would take Papachristos again?"**
| rank | distance | source | chunk preview |
|---|---|---|---|
| 1 | 0.456 | papachristos.txt | profile summary: "...39% of students would take Christos Papachristos again..." |
| 2 | 0.584 | papachristos.txt | review (CS446): "...Quality 1.0/5, Difficulty 5.0/5..." |
| 3 | 0.617 | papachristos.txt | review (CS446): "This class was t..." |
| 4 | 0.642 | papachristos.txt | review (CS446): "I really like h..." |
| 5 | 0.646 | papachristos.txt | review (CS446): "All the exams m..." |

*Why these are relevant:* All five chunks come from papachristos.txt, and the rank 1 chunk is the
profile summary that literally contains "39% of students would take Christos Papachristos again,"
which is the answer. The "would take again" phrasing in the query matched the summary most
strongly (0.456), and the lower-ranked review chunks are still about the same professor.

**Query C: "Is attendance mandatory for CS219 in Bashira Akter's course?"**
| rank | distance | source | chunk preview |
|---|---|---|---|
| 1 | 0.513 | bashira_akter.txt | review (CS219): "...Attendance: Not Mandatory. Grade: B-..." |
| 2 | 0.572 | davis_rant.txt | comment about Sara Davis teaching 302 |
| 3 | 0.586 | bashira_akter.txt | profile summary |
| 4 | 0.613 | bashira_akter.txt | review (CPE301): "...Attendance: Not Mandatory..." |
| 5 | 0.615 | bashira_akter.txt | review (CS219): "...Attendance: Not Mandatory..." |

The top result is the exact correct chunk (Bashira Akter, CS219, Attendance: Not Mandatory). Its
distance is 0.513, just over the 0.5 line, which I think is because MiniLM is a smaller model and
the long specific question is harder to match. The one off-source result at rank 2 (davis_rant)
is unrelated, but it did not change the answer since the correct chunk was first.

---

## Grounded Generation

**System prompt grounding instruction:**
The system prompt tells the model it is The Unofficial Guide and it must answer using only the
student review excerpts in the CONTEXT. The exact rules are: answer strictly from the CONTEXT and
never use outside or prior knowledge; if the CONTEXT does not contain enough information, reply
with exactly the sentence "I don't have enough information on that." and nothing else; cite the
source filename in brackets after each claim; and treat the reviews as subjective student opinions
and keep it concise. I run generation at temperature 0 so it does not get creative. The retrieved
chunks are passed in a numbered block where each one is labeled with its source filename, so the
model can see which file each fact came from.

**How source attribution is surfaced in the response:**
Two ways. The model is told to cite the source filename inline like [erin_keith.txt], but I do
not rely on it remembering to do that. After generation, my `ask()` function programmatically
collects the source filenames of the chunks that were actually retrieved and returns them as a
separate sources list, which the Gradio UI shows under "Retrieved from." If the model declines
for lack of information, I suppress the sources list so it does not look like the answer came from
documents. The UI also has an accordion that shows the full retrieved chunks with their distance
scores, so the grounding is inspectable.

### Example responses (with source attribution visible)

**Example 1 — in scope**
> **Q:** What is the overall quality of Erin Keith on Rate My Professors?
> **A:** Students say that Erin Keith has an overall quality rating of 2.8/5 based on 172 ratings
> on Rate My Professors **[erin_keith.txt]**. This suggests that opinions about her are mixed, with
> some students giving her high ratings and others giving her lower ratings **[erin_keith.txt]**.
> According to student reviews, 50% of students would take Erin Keith again **[erin_keith.txt]**.
> **Retrieved from:** erin_keith.txt, davis_vs_keith.txt

**Example 2 — in scope**
> **Q:** Is attendance mandatory for CS219 in Bashira Akter's course?
> **A:** Students say that attendance is not mandatory for CS219 in Bashira Akter's course
> **[bashira_akter.txt]**. This is consistent across two different reviews for the same course,
> where both students mention that attendance is not required **[bashira_akter.txt]**.
> **Retrieved from:** bashira_akter.txt, davis_rant.txt

**Example 3 — out of scope (refusal)**
> **Q:** What is the best dining hall at UNR?
> **A:** I don't have enough information on that.
> **Retrieved from:** (none — sources are suppressed when the system declines)

The dining hall question is outside the documents (they only cover CS professors and courses), so
even though retrieval still returned five CS chunks, the model refused instead of inventing an
answer from training knowledge.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Who teaches CS 135 at UNR? | Erin Keith | Said the professor is "not specified" but mentioned Erin Keith as a good intro prof; pulled the CS 135 discussion thread instead of the profile | Off-target | Partially accurate |
| 2 | Is attendance mandatory for CS219 in Bashira Akter's course? | No | "Attendance is not mandatory for CS219 in Bashira Akter's course [bashira_akter.txt]" | Relevant | Accurate |
| 3 | What is the overall quality of Erin Keith on Rate My Professors? | 2.8/5 | "Overall quality rating of 2.8/5 based on 172 ratings [erin_keith.txt]" | Relevant | Accurate |
| 4 | What is the level of difficulty in a course with Sara Davis on Rate My Professor? | 4 | "Around 4.0/5; the profile lists level of difficulty 4/5 [sara_davis.txt]" | Relevant | Accurate |
| 5 | What percent of students would take Papachristos again on Rate My Professor? | 39% | "39% of students would take Christos Papachristos again [papachristos.txt]" | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

Overall 4 of the 5 questions were accurate and grounded with the right source. Question 1 was the
one that struggled, which is explained below. I also tested an out of domain question ("What is
the best dining hall at UNR?") and the system correctly replied "I don't have enough information
on that." instead of making something up.

---

## Failure Case Analysis

**Question that failed:** "Who teaches CS 135 at UNR?" (expected: Erin Keith)

**What the system returned:** It said the professor for CS 135 was "not specified," then mentioned
Erin Keith as a good intro prof but added it was "not clear if she teaches CS 135." The top
retrieved chunks were all from the CS 135 Reddit discussion thread (cs135.txt) plus the
Keith vs Siming thread, not from the erin_keith.txt profile that contains many CS135 reviews.

**Root cause (tied to a specific pipeline stage):** This is a retrieval and representation problem.
The fact that "Erin Keith teaches CS 135" is never written as a sentence anywhere in my data. In
the RMP profile it only exists as the context label I inject ("Rate My Professors review — Erin
Keith, course CS135"), and the rest of that chunk is the actual review opinion, so the embedding
of the chunk is dominated by the review content, not by the identity fact. Meanwhile the query
"who teaches CS 135" is semantically closest to the Reddit thread literally titled "CS 135" and to
general discussion of the class, so MiniLM ranks those chunks first. Those comments talk about how
hard the class is, not who teaches it, so the model had no clean statement of the instructor and
correctly hedged. The grounding worked, the retrieval did not surface the right evidence.

**What you would change to fix it:** I would add a synthesized profile chunk per professor that
states plainly which courses they are reviewed for, for example "Erin Keith teaches CS135, CS202,
CS326, CS333, CS457 at UNR based on student reviews," so the identity fact has its own embedding
to match against. A stronger or hybrid model like bge-m3 (keyword plus semantic) would also help
match the course code and the word "teaches" more directly.

---

## Spec Reflection

**One way the spec helped you during implementation:**
Writing the chunking strategy in planning.md before coding forced me to look at my real documents
and realize the reviews do not contain the professor name. That is the whole reason I built the
context injection step instead of a plain sliding window. If I had skipped the spec and just let
an AI generate a generic chunker, my chunks would not have been answerable on their own and the
retrieval would have been much worse. The spec made me design for my data instead of for a generic
case.

**One way your implementation diverged from the spec, and why:**
My spec said the embedding model would be bge-m3, but I switched to all-MiniLM-L6-v2 during
Milestone 4. The reason is practical: bge-m3 is around 2.3GB and slow to run locally, while MiniLM
is about 80MB, runs on CPU instantly, and was good enough for short English reviews. The tradeoff
showed up in my failure case, where a stronger model probably would have retrieved better, so I
documented bge-m3 as the upgrade path if I needed more accuracy.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* My planning.md Documents and Chunking Strategy sections, the architecture
  diagram, and pasted samples of a Rate My Professors profile and a Reddit thread, and asked it to
  write the ingestion and chunking script that loads the .txt files, cleans them, and produces
  256 token chunks with 64 overlap.
- *What it produced:* A pipeline that detected the two source types, cleaned the site boilerplate,
  parsed the RMP reviews and Reddit comments, and chunked them, plus an inspection step that prints
  sample chunks and the total count.
- *What I changed or overrode:* The first run produced a bad chunk that mixed the "Sorry this post
  was deleted" boilerplate with a leaked username from the next comment. I directed it to filter
  deleted/removed markers and to trim the trailing username block off the pre comment region, and I
  re-ran and inspected the chunks until they were all clean and self contained. I also kept the
  256/64 numbers but had it apply the window inside each review/comment rather than across the
  whole file.

**Instance 2**

- *What I gave the AI:* My Retrieval Approach section and the grounding requirement (answer from
  retrieved context only, decline when the context does not cover it, cite sources), and asked it
  to wire retrieval into the Groq LLM and build a Gradio interface.
- *What it produced:* An `ask()` function that retrieves the top 5 chunks, builds a context only
  prompt for llama-3.3-70b-versatile, and a Gradio app with an answer box, a sources box, and an
  evidence accordion.
- *What I changed or overrode:* I switched the embedding model from bge-m3 to all-MiniLM-L6-v2 for
  the local lightweight default. I also made the source attribution programmatic instead of
  trusting the model to cite, and added logic to suppress the sources list when the model declines.
  When gradio upgraded huggingface-hub and broke transformers, I pinned huggingface-hub below 1.0
  to fix it.

---

## Query Interface

The interface is a Gradio web app (`app.py`) running at http://localhost:7860.

**Input field:**
- *Your question* — a single text box where the user types a question about a UNR CS professor or
  course. Pressing the Ask button or hitting Enter submits it. There are also clickable example
  questions below the box.

**Output fields:**
- *Answer* — the grounded answer text generated by the LLM, with inline source citations like
  [erin_keith.txt].
- *Retrieved from* — the list of source documents the answer was retrieved from (empty when the
  system declines).
- *Show retrieved chunks (the evidence)* — a collapsible accordion that shows the full top-5
  retrieved chunks with their source, position, and cosine distance, so the grounding is
  inspectable.

**Sample interaction transcript (one complete query and response):**
```
Your question:  What is the level of difficulty in a course with Sara Davis on Rate My Professor?

Answer:         Students say that the level of difficulty in a course with Sara Davis is generally
                around 4.0/5, with one review stating it's "mediumish" [sara_davis.txt]. According
                to the Rate My Professors profile, the overall level of difficulty is 4/5
                [sara_davis.txt]. Students also describe the course as "Tough" and "Test heavy"
                [sara_davis.txt].

Retrieved from: • sara_davis.txt

Show retrieved chunks (the evidence):
  [1] sara_davis.txt (#3, distance 0.316)  [Rate My Professors review — Sara Davis, course CS302]...
  [2] sara_davis.txt (#9, distance 0.331)  [Rate My Professors review — Sara Davis, course CS302]...
  [3] sara_davis.txt (#7, distance 0.340)  [Rate My Professors review — Sara Davis, course CS302]...
  [4] sara_davis.txt (#4, distance 0.361)  [Rate My Professors review — Sara Davis, course CS302]...
  [5] sara_davis.txt (#0, distance 0.371)  [Rate My Professors profile — Sara Davis...]
```

---

## How to Run

```bash
pip install -r requirements.txt
# add your GROQ_API_KEY to .env (see .env.example)

python src/ingest_chunk.py     # Milestone 3: load, clean, chunk -> data/chunks.json
python src/vector_store.py     # Milestone 4: embed + store in ChromaDB + retrieval test
python app.py                  # Milestone 5: Gradio UI at http://localhost:7860
```
