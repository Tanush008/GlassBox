"""
The context engine.

Superbrain's pitch is a "proprietary context engine that compresses and
prioritizes code intelligence on the fly" and claims 60-80% token savings
while keeping full repo awareness. This module is Glassbox's (much smaller,
fully transparent) take on the same idea, applied to the sample repo:

1. Walk every file in the repo.
2. Score each file's relevance to the user's request.
3. Greedily pack the highest-scoring files into a fixed token budget.
4. Report exactly what was included, what was left out, and how many
   tokens were saved versus dumping the whole repo into the prompt.

The scoring function is intentionally simple (token-overlap + a few
hand-rolled signals) rather than an embedding model, so the whole thing
runs with zero external calls and its behavior is easy to reason about
and explain in an interview. The README spells out what a production
version would add.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    "is", "are", "be", "it", "this", "that", "should", "when", "add",
    "make", "so", "as", "at", "by", "we", "our", "i", "want", "need",
    "please", "can", "you",
}

_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


def count_tokens(text: str) -> int:
    """Cheap, dependency-free token estimate.

    ~4 characters per token is the standard rule of thumb for GPT/Claude-
    style BPE tokenizers on English text and code. This is intentionally
    an approximation, not a real tokenizer call - good enough for a
    relative "how much of the repo did we include" budget, and it means
    the context engine has zero external dependencies or network calls.
    """
    return max(1, len(text) // 4)


def _tokenize(text: str) -> set[str]:
    words = {w.lower() for w in _WORD_RE.findall(text)}
    # also split snake_case / camelCase identifiers into sub-parts so
    # "user_email" matches a request that mentions "email"
    parts: set[str] = set()
    for w in words:
        parts.update(p for p in re.split(r"_", w) if len(p) > 2)
        parts.update(
            p.lower()
            for p in re.findall(r"[A-Z]?[a-z0-9]+", w)
            if len(p) > 2
        )
    return (words | parts) - _STOPWORDS


@dataclass
class FileScore:
    path: str
    content: str
    score: float
    tokens: int
    matched_terms: List[str] = field(default_factory=list)


@dataclass
class ContextResult:
    included: List[FileScore]
    excluded: List[FileScore]
    included_tokens: int
    full_repo_tokens: int
    budget: int

    @property
    def compression_pct(self) -> float:
        if self.full_repo_tokens == 0:
            return 0.0
        saved = self.full_repo_tokens - self.included_tokens
        return round(100 * saved / self.full_repo_tokens, 1)


def _iter_repo_files(repo_path: Path) -> List[Path]:
    exts = {".py", ".md", ".txt", ".json", ".cfg", ".ini"}
    return sorted(
        p for p in repo_path.rglob("*")
        if p.is_file() and p.suffix in exts and "__pycache__" not in p.parts
    )


def _score_file(request_terms: set[str], path: Path, content: str) -> FileScore:
    file_terms = _tokenize(content) | _tokenize(path.stem)
    matched = sorted(request_terms & file_terms)

    overlap = len(matched)
    # Normalize a little so a giant file doesn't win purely on size, and
    # give a small boost to files whose *name* matches the request (a
    # cheap proxy for "this is probably the entry point for the change").
    name_boost = 2.0 if any(t in path.stem.lower() for t in request_terms) else 0.0
    density = overlap / max(len(file_terms), 1) * 10
    score = overlap + density + name_boost

    return FileScore(
        path=str(path),
        content=content,
        score=round(score, 3),
        tokens=count_tokens(content),
        matched_terms=matched,
    )


def select_context(request: str, repo_path: Path, budget: int) -> ContextResult:
    request_terms = _tokenize(request)
    files = _iter_repo_files(repo_path)

    scored: List[FileScore] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = str(f.relative_to(repo_path))
        fs = _score_file(request_terms, f, content)
        fs.path = rel
        scored.append(fs)

    scored.sort(key=lambda fs: fs.score, reverse=True)

    full_repo_tokens = sum(fs.tokens for fs in scored)

    included: List[FileScore] = []
    excluded: List[FileScore] = []
    spent = 0
    for fs in scored:
        if fs.score > 0 and spent + fs.tokens <= budget:
            included.append(fs)
            spent += fs.tokens
        else:
            excluded.append(fs)

    # Always guarantee at least one file gets in, even on a near-empty
    # request, so the agents have *something* to work with.
    if not included and scored:
        included.append(scored[0])
        spent = scored[0].tokens
        excluded = scored[1:]

    return ContextResult(
        included=included,
        excluded=excluded,
        included_tokens=spent,
        full_repo_tokens=full_repo_tokens,
        budget=budget,
    )
