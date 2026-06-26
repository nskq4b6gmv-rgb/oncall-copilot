import os
import glob
import re

# Resolve docs/ relative to the repo root (works no matter the cwd).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_chunks():
    # Split each markdown doc into paragraph-sized chunks; remember the source file.
    chunks = []
    for path in glob.glob(os.path.join(ROOT, "docs", "*.md")):
        name = os.path.basename(path)
        text = open(path, encoding="utf-8").read()
        for para in re.split(r"\n\s*\n", text):     # blank line = chunk boundary
            para = para.strip()
            if len(para) > 20:
                chunks.append({"source": name, "text": para})
    return chunks


CHUNKS = _load_chunks()


def retrieve(question, k=4):
    # Keyword retrieval: transparent, zero-dependency, fine for a small KB.
    # (No embeddings API needed — works great with OpenRouter, which has no embeddings endpoint.)
    words = set(re.findall(r"\w+", question.lower()))
    scored = []
    for ch in CHUNKS:
        hay = ch["text"].lower()
        score = sum(1 for w in words if w in hay)
        if score:
            scored.append((score, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [ch for _, ch in scored[:k]]
    if not top:
        return ""    # empty context -> the system prompt tells the model to refuse
    return "\n\n".join(f"[{ch['source']}]\n{ch['text']}" for ch in top)


# --- Optional semantic upgrade (LOCAL embeddings, no API/cost) ---
# pip install sentence-transformers, then use retrieve_semantic() instead of retrieve().
#
# import math
# from sentence_transformers import SentenceTransformer
# _model = SentenceTransformer("all-MiniLM-L6-v2")
# def _embed(texts): return _model.encode(texts).tolist()
# def _cos(a, b):
#     dot = sum(x*y for x, y in zip(a, b))
#     na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
#     return dot / (na*nb + 1e-9)
# _VECS = _embed([c["text"] for c in CHUNKS]) if CHUNKS else []
# def retrieve_semantic(question, k=4):
#     qv = _embed([question])[0]
#     scored = sorted(zip((_cos(qv, v) for v in _VECS), CHUNKS), key=lambda x: x[0], reverse=True)
#     top = [c for _, c in scored[:k]]
#     return "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in top)
