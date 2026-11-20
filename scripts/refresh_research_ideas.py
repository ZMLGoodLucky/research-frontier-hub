#!/usr/bin/env python3
"""Weekly evidence refresh for curated research questions.

Only matches *public metadata* from the daily research feed.
Does NOT fabricate a new research problem, novelty claim, or prior work conclusion.
Runs independently of daily collection; writes site/idea-evidence.json only.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TIMEZONE = ZoneInfo("Asia/Shanghai")


def read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def normalize(url: str) -> str:
    return str(url or "").split("?")[0].rstrip("/").lower()


def topic_score(paper: dict, idea: dict) -> int:
    title = str(paper.get("title") or "").lower()
    meta = " ".join(str(v) for v in (
        paper.get("method") or "", paper.get("category") or "",
        " ".join(paper.get("topics") or []), paper.get("problem") or ""
    )).lower()
    terms = [str(t).lower() for t in idea.get("match_terms", [])]
    if not terms:
        return 0
    title_hits = sum(1 for t in terms if t in title)
    meta_hits = sum(1 for t in terms if t in meta and t not in title)
    # Metadata can contain generic user-oriented boilerplate:
    # require at least one meaningful hit in the actual paper title.
    if title_hits < 1 or (title_hits + meta_hits) < 2:
        return 0
    return title_hits * 3 + min(meta_hits, 5)


def scan(ideas: dict, feed: dict, prior: dict, now: dt.datetime):
    today = now.astimezone(TIMEZONE).date()
    past_seen = prior.get("seen", {})
    output = {
        "schema_version": "1.0",
        "checked_at": now.astimezone(TIMEZONE).isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "lookback_days": 14,
        "source_data_generated_at": feed.get("generated_at"),
        "review_method": "基于公开元数据标题/主题自动匹配，非论文全文核验",
        "status": "自动证据更新不修改核心科学问题及三个创新假设",
        "topics": {},
        "seen": {}
    }
    items = feed.get("items", []) if isinstance(feed.get("items"), list) else []
    for idea in ideas.get("ideas", []):
        topic_id = idea.get("id")
        if not topic_id:
            continue
        existing = set(past_seen.get(topic_id, [])) if isinstance(past_seen, dict) else set()
        known = {normalize(x.get("url")) for x in idea.get("prior", [])}
        ranked = []
        for item in items:
            if item.get("type") != "paper" or not item.get("url"):
                continue
            link = normalize(item["url"])
            if link in known or link in existing:
                continue
            try:
                published = dt.date.fromisoformat(item["date"])
            except (TypeError, ValueError, KeyError):
                continue
            days = (today - published).days
            if days < 0 or days > 14:
                continue
            relevance = topic_score(item, idea)
            if not relevance:
                continue
            ranked.append((relevance, published, item))
        ranked.sort(key=lambda v: (v[0], v[1]), reverse=True)
        new = []
        for _, _, paper in ranked[:3]:
            link = normalize(paper["url"])
            existing.add(link)
            new.append({
                "title": paper.get("title") or "",
                "date": paper.get("date") or "",
                "venue": paper.get("venue_full") or paper.get("venue") or paper.get("source") or "",
                "url": paper.get("url"),
                "doi": paper.get("doi") or "",
                "discovered_via": paper.get("discovered_via") or [paper.get("source")],
                "candidate_only": True
            })
        output["topics"][topic_id] = {
            "papers": new,
            "new_count": len(new),
            "summary": f"新增匹配 {len(new)} 篇；论文贡献及重叠性待全文核验"
        }
        output["seen"][topic_id] = sorted(existing)[-200:]
    return output


def main():
    now = dt.datetime.now(TIMEZONE)
    ideas = read(ROOT / "site/research-ideas.json", {})
    papers = read(ROOT / "site/data.json", {})
    before = read(ROOT / "site/idea-evidence.json", {})
    if not ideas.get("ideas"):
        raise SystemExit("No curated research ideas; leaving prior evidence unchanged.")
    if not isinstance(papers.get("items"), list):
        raise SystemExit("No valid paper metadata; leaving prior evidence unchanged.")
    result = scan(ideas, papers, before, now)
    dest = ROOT / "site/idea-evidence.json"
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Weekly scan {result['checked_at']}: " + ", ".join(
        f"{key}={topic['new_count']}" for key, topic in result["topics"].items()))
    print("Core research questions and innovation hypotheses remain unchanged.")


if __name__ == "__main__":
    main()
