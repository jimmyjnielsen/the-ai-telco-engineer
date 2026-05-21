#!/usr/bin/env python3
"""Compute per-generation idea novelty for Op-G4 (f1) and Op-G4* (f2).

For each generation, extracts the 5 proposed ideas from manager.log and
computes how novel they are relative to all ideas from previous generations,
using TF-IDF cosine similarity. Outputs idea_novelty.json in paper/figures/.

Usage (run from repo root on connectivity1):
    python idea_novelty.py
"""

import json
import math
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent
OUTPUT = REPO / "paper" / "figures" / "idea_novelty.json"

TASKS = {
    "Op-G4":  REPO / "tasks" / "link_adaptation_f1" / "workspaces" / "manager.log",
    "Op-G4*": REPO / "tasks" / "link_adaptation_f2" / "workspaces" / "manager.log",
}


def extract_ideas(log_path: Path) -> dict[int, list[str]]:
    """Return {gen: [description, ...]} extracted from manager.log."""
    text = log_path.read_text(errors="replace")

    # Find all idea response blocks (both initial and from-results)
    pattern = re.compile(
        r"\[RESPONSE \((?:initial ideas|ideas from results)\)\]\n(\[.*?\])\n\n={60}",
        re.DOTALL,
    )
    blocks = pattern.findall(text)

    # Each block is a JSON array; pair with generation index in order
    ideas_by_gen: dict[int, list[str]] = {}
    for gen, block in enumerate(blocks):
        try:
            items = json.loads(block)
            ideas_by_gen[gen] = [item["description"] for item in items]
        except (json.JSONDecodeError, KeyError):
            ideas_by_gen[gen] = []

    return ideas_by_gen


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def tfidf_vectors(all_docs: list[list[str]]) -> list[dict[str, float]]:
    """Compute TF-IDF vectors for each document (list of tokens)."""
    N = len(all_docs)
    df: Counter = Counter()
    for doc in all_docs:
        df.update(set(doc))

    idf = {term: math.log((N + 1) / (count + 1)) + 1 for term, count in df.items()}

    vectors = []
    for doc in all_docs:
        tf = Counter(doc)
        total = len(doc) or 1
        vec = {term: (tf[term] / total) * idf[term] for term in tf}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append({term: v / norm for term, v in vec.items()})
    return vectors


def cosine(v1: dict, v2: dict) -> float:
    return sum(v1.get(t, 0) * v for t, v in v2.items())


def novelty_per_gen(ideas_by_gen: dict[int, list[str]]) -> list[tuple[int, float]]:
    """For each gen G, return mean(1 - max_sim(idea, all previous ideas)).

    Gen 0 gets novelty = 1.0 (no previous ideas to compare against).
    """
    all_prev_descriptions: list[str] = []
    result = []

    for gen in sorted(ideas_by_gen):
        current = ideas_by_gen[gen]
        if not all_prev_descriptions:
            result.append((gen, 1.0))
        else:
            all_docs = [tokenize(d) for d in all_prev_descriptions + current]
            vectors = tfidf_vectors(all_docs)
            prev_vecs = vectors[: len(all_prev_descriptions)]
            curr_vecs = vectors[len(all_prev_descriptions):]
            gen_novelties = []
            for cv in curr_vecs:
                max_sim = max(cosine(cv, pv) for pv in prev_vecs)
                gen_novelties.append(1.0 - max_sim)
            result.append((gen, sum(gen_novelties) / len(gen_novelties)))

        all_prev_descriptions.extend(current)

    return result


def main():
    output: dict = {}
    for label, log_path in TASKS.items():
        if not log_path.exists():
            print(f"  {label}: manager.log not found at {log_path}")
            continue
        print(f"  Processing {label} ...")
        ideas = extract_ideas(log_path)
        print(f"    Extracted ideas for {len(ideas)} generations")
        novelty = novelty_per_gen(ideas)
        output[label] = novelty
        for gen, nov in novelty:
            print(f"    gen {gen:2d}: novelty = {nov:.3f}")

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nWrote {OUTPUT}")


if __name__ == "__main__":
    main()
