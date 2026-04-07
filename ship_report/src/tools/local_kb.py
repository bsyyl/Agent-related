from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from src.tools._search import SearchClient as BaseSearchClient, SearchResult


@dataclass(frozen=True)
class LocalKbDoc:
    path: str
    title: str
    content: str


def _iter_files(root: Path, patterns: List[str]) -> Iterable[Path]:
    # Very small, dependency-free globbing.
    # We rely on Path.rglob per pattern to keep behavior predictable.
    for pat in patterns:
        yield from root.rglob(pat.replace("**/", ""))


def _safe_read_text(path: Path, max_chars: int) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text[:max_chars] if max_chars and len(text) > max_chars else text
    except Exception:
        return ""


def _extract_text_from_json(raw: str) -> str:
    try:
        obj = json.loads(raw)
    except Exception:
        return raw

    chunks: List[str] = []

    def walk(x):
        if x is None:
            return
        if isinstance(x, str):
            if x.strip():
                chunks.append(x.strip())
            return
        if isinstance(x, (int, float, bool)):
            chunks.append(str(x))
            return
        if isinstance(x, list):
            for it in x:
                walk(it)
            return
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(k, str) and k.strip():
                    chunks.append(k.strip())
                walk(v)

    walk(obj)
    return "\n".join(chunks)


def _tokenize(q: str) -> List[str]:
    # Simple tokenizer that works for English acronyms and basic CJK mixed queries.
    q = (q or "").strip().lower()
    if not q:
        return []
    tokens = []
    buf = []
    for ch in q:
        if ch.isalnum():
            buf.append(ch)
        else:
            if buf:
                tokens.append("".join(buf))
                buf = []
    if buf:
        tokens.append("".join(buf))
    # de-dup while preserving order
    seen = set()
    out = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _score(content: str, tokens: List[str]) -> int:
    if not content or not tokens:
        return 0
    c = content.lower()
    s = 0
    for t in tokens:
        if not t:
            continue
        # Very cheap scoring: occurrences capped to avoid bias by huge docs.
        cnt = c.count(t)
        if cnt:
            s += min(cnt, 20)
    return s


class LocalKbSearchClient(BaseSearchClient):
    """
    Local knowledge base search.

    - Indexes markdown/txt/json files under a directory.
    - Returns SearchResult where url is `local://<relative_path>`.
    """

    def __init__(
        self,
        kb_path: str,
        include_globs: Optional[List[str]] = None,
        max_chars_per_file: int = 200000,
    ) -> None:
        self._root = Path(kb_path).resolve()
        self._include_globs = include_globs or ["**/*.md", "**/*.txt", "**/*.json"]
        self._max_chars_per_file = max_chars_per_file
        self._docs: List[LocalKbDoc] = []
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        if not self._root.exists() or not self._root.is_dir():
            return

        seen: set[str] = set()
        for p in _iter_files(self._root, self._include_globs):
            try:
                p = p.resolve()
            except Exception:
                continue
            if not p.is_file():
                continue
            if str(p) in seen:
                continue
            seen.add(str(p))

            raw = _safe_read_text(p, self._max_chars_per_file)
            if not raw.strip():
                continue

            text = raw
            if p.suffix.lower() == ".json":
                text = _extract_text_from_json(raw)

            rel = os.path.relpath(str(p), str(self._root))
            title = p.stem
            self._docs.append(LocalKbDoc(path=rel.replace("\\", "/"), title=title, content=text))

    def search(self, query: str, top_n: int) -> List[SearchResult]:
        self._load()
        tokens = _tokenize(query)
        if not tokens or not self._docs:
            return []

        scored: List[Tuple[int, LocalKbDoc]] = []
        for d in self._docs:
            s = _score(d.content, tokens)
            if s > 0:
                scored.append((s, d))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: List[SearchResult] = []
        for s, d in scored[: max(0, int(top_n or 0))]:
            excerpt = d.content[:800].strip().replace("\r\n", "\n")
            results.append(
                SearchResult(
                    url=f"local://{d.path}",
                    title=d.title,
                    summary=excerpt[:300],
                    content=excerpt,
                    date="",
                )
            )
        return results

