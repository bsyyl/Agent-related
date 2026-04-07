from __future__ import annotations

from typing import List

from src.config.workflow_config import workflow_configs
from src.tools._search import SearchResult
from src.tools.local_kb import LocalKbSearchClient
from src.tools.search import SearchClient


class KnowledgeClient:
    """
    Knowledge retrieval client: prefer local KB, fallback to web search.

    Returns a merged list of SearchResult objects.
    """

    def __init__(self) -> None:
        local_cfg = workflow_configs.get("local_kb", {}) or {}
        self._local_enabled = bool(local_cfg.get("enabled", True))
        self._local_top_n = int(local_cfg.get("topN", 8))
        self._local = LocalKbSearchClient(
            kb_path=str(local_cfg.get("path", "./local_kb")),
            include_globs=list(local_cfg.get("include_globs", ["**/*.md", "**/*.txt", "**/*.json"])),
            max_chars_per_file=int(local_cfg.get("max_chars_per_file", 200000)),
        )
        # Web search is optional (depends on configured engine and installed deps).
        try:
            self._web = SearchClient()
        except Exception:
            self._web = None

    def search(self, query: str, top_n: int) -> List[SearchResult]:
        top_n = int(top_n or 0)
        if top_n <= 0:
            return []

        results: List[SearchResult] = []
        seen_urls: set[str] = set()

        if self._local_enabled:
            local_results = self._local.search(query, min(self._local_top_n, top_n))
            for r in local_results:
                if r.url and r.url not in seen_urls:
                    seen_urls.add(r.url)
                    results.append(r)
                if len(results) >= top_n:
                    return results

        # Fill remaining slots using web search
        remain = top_n - len(results)
        if remain > 0 and self._web is not None:
            web_results = self._web.search(query, remain)
            for r in web_results:
                if r.url and r.url not in seen_urls:
                    seen_urls.add(r.url)
                    results.append(r)
                if len(results) >= top_n:
                    break

        return results

