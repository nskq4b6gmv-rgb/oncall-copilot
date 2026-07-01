"""Retrieval before/after: keyword vs hybrid (keyword + local embeddings).

Measures RETRIEVAL quality directly (no LLM, no cost): for each labelled case, does
the retrieved context contain the "gold marker" phrases that only live in the correct
paragraph? Recall@k = fraction of gold markers found. Run: python -m evals.retrieval_compare
"""
import json
import os
import re
from src import retriever

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODES = ["keyword", "hybrid"]


def _recall(context, gold):
    low = context.lower()
    hits = [g for g in gold if g.lower() in low]
    return len(hits), len(gold)


def _sources(context):
    return sorted(set(re.findall(r"\[([^\]\n]+)\]", context)))


def run():
    cases = [json.loads(l) for l in open(os.path.join(ROOT, "evals", "retrieval_cases.jsonl"))]
    print(f"{'difficulty':8} {'question':44} " + "  ".join(f"{m:^14}" for m in MODES))
    print("-" * 92)
    totals = {m: [0, 0] for m in MODES}
    for c in cases:
        cells = []
        for m in MODES:
            ctx = retriever.retrieve(c["question"], mode=m)
            found, total = _recall(ctx, c["gold"])
            src_ok = "✓" if c["expect_source"] in _sources(ctx) else "✗"
            totals[m][0] += found
            totals[m][1] += total
            cells.append(f"{found}/{total} src:{src_ok}")
        print(f"{c['difficulty']:8} {c['question'][:44]:44} " + "  ".join(f"{x:^14}" for x in cells))
    print("-" * 92)
    summary = []
    for m in MODES:
        f, t = totals[m]
        summary.append(f"{f}/{t} = {f / t:.0%}")
    print(f"{'':8} {'Recall@4 (gold markers found)':44} " + "  ".join(f"{x:^14}" for x in summary))


if __name__ == "__main__":
    run()
