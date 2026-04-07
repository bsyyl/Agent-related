from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.workflow_config import workflow_configs
from src.tools.knowledge import KnowledgeClient


@dataclass(frozen=True)
class PortInfo:
    name: str
    country: str = ""
    unlocode: str = ""
    timezone: str = ""
    notes: str = ""
    sources: List[Dict[str, str]] = None


def _load_local_dataset(path_str: str) -> List[Dict[str, Any]]:
    if not path_str:
        return []
    p = Path(path_str)
    if not p.exists() or not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "ports" in data and isinstance(data["ports"], list):
            return data["ports"]
    except Exception:
        return []
    return []


def get_port_info(
    port_name: str,
    country: str = "",
    realtime: bool = False,
    top_n_sources: int = 5,
) -> Dict[str, Any]:
    """
    Retrieve port information for reporting.

    Strategy:
    1) Try local dataset (if configured).
    2) Query local KB (and web as fallback) for port-related evidence/snippets.
    3) If realtime=True, broaden query to include "congestion / waiting time / strike / weather".
    """
    port_name = (port_name or "").strip()
    country = (country or "").strip()
    if not port_name:
        return {"port": None, "evidence": []}

    cfg = workflow_configs.get("port_info", {}) or {}
    dataset_path = str(cfg.get("local_dataset", ""))
    dataset = _load_local_dataset(dataset_path)

    matched: Optional[Dict[str, Any]] = None
    for item in dataset:
        try:
            name = str(item.get("name", "")).strip()
        except Exception:
            continue
        if not name:
            continue
        if name.lower() == port_name.lower():
            if country and str(item.get("country", "")).strip().lower() != country.lower():
                continue
            matched = item
            break

    evidence: List[Dict[str, str]] = []
    kc = KnowledgeClient()
    base_q = f"{port_name} port"
    if country:
        base_q += f" {country}"

    queries = [base_q]
    if realtime:
        queries.append(f"{base_q} congestion waiting time")
        queries.append(f"{base_q} latest notice weather")

    for q in queries:
        for r in kc.search(q, top_n_sources):
            evidence.append(
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": (r.summary or r.content or "")[:400],
                }
            )

    # De-dup evidence by url
    seen = set()
    deduped = []
    for e in evidence:
        u = e.get("url", "")
        if not u or u in seen:
            continue
        seen.add(u)
        deduped.append(e)

    return {
        "port": matched or {"name": port_name, "country": country},
        "evidence": deduped[: max(0, int(top_n_sources))],
    }

