# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

The domain that I choose was student reviews of CS professors at the University of Nevada-Reno for incoming Freshman. This knowledge is valuable since many professors and course subject material are available in the course catalog, but these reviews are directly from student experiences. It gives insight from peer to peer which seems more trustworthy than seeing what the course offers.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Erin Keith – Rate My Professors Profile | Deep repository tracking grading stringency, lab structures, and test styles for introductory sequences. | [https://www.ratemyprofessors.com/professor/2641005](https://www.ratemyprofessors.com/professor/2641005) |
| 2 | Sara Davis – Rate My Professors Profile | Compiles alternative perspectives on intro-level programming, tracking her pacing, slide clarity, and responsiveness. | [https://www.ratemyprofessors.com/professor/2418536](https://www.ratemyprofessors.com/professor/2418536) |
| 3 | r/unr Thread: "CS 135 - Professor Davis or Keith?" | A direct head-to-head comparison evaluating lecturing style versus project guidance for the two main freshman options. | [https://www.reddit.com/r/unr/comments/dvh9mx/cs_135_professor_davis_or_keith/](https://www.reddit.com/r/unr/comments/dvh9mx/cs_135_professor_davis_or_keith/) |
| 4 | r/unr Thread: "CS135 Erin Keith Vs Siming" | Student analysis detailing historical syllabus rigidity, project weights, and advice on navigating exams. | [https://www.reddit.com/r/unr/comments/8wdzw7/cs135_erin_keith_vs_siming/](https://www.reddit.com/r/unr/comments/8wdzw7/cs135_erin_keith_vs_siming/) |
| 5 | Christos Papachristos – RMP Faculty Profile | Collects student feedback for the immediate sophomore step (CS 202). Reviews explicitly breakdown his rigorous testing expectations and the adjustment to object-oriented logic. | [https://www.ratemyprofessors.com/professor/2245367](https://www.ratemyprofessors.com/professor/2245367) |
| 6 | r/unr Thread: "How is the CS department here?" | Student advice summarizing the importance of leveraging Teaching Assistants (TAs) and joining peer Discord servers early. | [https://www.reddit.com/r/unr/comments/e44kg7/how_is_the_cs_department_here/](https://www.reddit.com/r/unr/comments/e44kg7/how_is_the_cs_department_here/) |
| 7 | Siming Liu – RMP Faculty Profile | Compiles student feedback on his version of the CS 135 (Intro to Programming) gateway. Reviews contrast his project assignments, code structure rules, and responsiveness to students debugging syntax during office hours. | [https://www.ratemyprofessors.com/professor/2301919](https://www.ratemyprofessors.com/professor/2301919) |
| 8 | r/unr Thread: "CS 135" | Contains crucial peer warnings about navigating the introductory course. Highlights the danger of falling behind on weekly projects and why relying on AI code tools prevents you from passing handwritten tests. | [https://www.reddit.com/r/unr/comments/h9v9cz/cs_135/](https://www.reddit.com/r/unr/comments/h9v9cz/cs_135/) |
| 9 | r/unr Thread: "CS202 Sara Davis Rant" | An unfiltered look at the extreme pacing of taking core programming classes during the accelerated summer term. Peer reviews break down the structural difficulties of intermediate C++ concepts like templating and inheritance under strict deadlines. | [https://www.reddit.com/r/unr/comments/1e482bt/cs202_sara_davis_rant/](https://www.reddit.com/r/unr/comments/1e482bt/cs202_sara_davis_rant/) |
| 10 | Emily Hand – RMP Faculty Profile | Tracks student reviews for introductory/early elective environments. Commentary details her helpfulness, approachable lecturing style, and how she introduces freshmen to foundational AI/Machine Learning concepts without overwhelming them. | [https://www.ratemyprofessors.com/professor/2493392](https://www.ratemyprofessors.com/professor/2493392) |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
