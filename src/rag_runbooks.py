"""Lightweight RAG over markdown runbooks in ``data/docs`` (Session 3).

Uses chunked documents + lexical overlap scoring (no embedding API; works on EC2 NIM-only).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 180) -> list[str]:
    if not text.strip():
        return []
    chunks: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        end = min(i + chunk_size, n)
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        i = end - overlap
    return chunks


@dataclass
class _Chunk:
    rel_path: str
    text: str
    terms: frozenset[str]


class RunbookIndex:
    def __init__(self, chunks: list[_Chunk]) -> None:
        self._chunks = chunks

    @classmethod
    def from_docs_dir(cls, docs_dir: Path, *, pattern: str = "**/*.md") -> RunbookIndex:
        if not docs_dir.is_dir():
            raise FileNotFoundError(f"Runbook directory not found: {docs_dir}")
        parts: list[_Chunk] = []
        for path in sorted(docs_dir.glob(pattern)):
            if not path.is_file():
                continue
            rel = path.relative_to(docs_dir).as_posix()
            body = path.read_text(encoding="utf-8")
            for piece in _chunk_text(body):
                t = _tokenize(rel + " " + piece)
                parts.append(_Chunk(rel_path=rel, text=piece, terms=t))
        if not parts:
            raise ValueError(f"No markdown chunks under {docs_dir} (expected {pattern})")
        return cls(parts)

    def retrieve(self, query: str, *, top_k: int = 4) -> list[tuple[str, str, float]]:
        q_terms = _tokenize(query)
        if not q_terms:
            return []
        scored: list[tuple[float, _Chunk]] = []
        for ch in self._chunks:
            inter = len(q_terms & ch.terms)
            if inter == 0:
                continue
            # Light path boost: filename overlap with query terms
            path_terms = _tokenize(ch.rel_path)
            path_bonus = 0.3 * len(q_terms & path_terms)
            score = float(inter) + path_bonus
            scored.append((score, ch))
        scored.sort(key=lambda x: -x[0])
        out: list[tuple[str, str, float]] = []
        for score, ch in scored[:top_k]:
            out.append((ch.rel_path, ch.text, score))
        return out
