"""Verified venue metadata for FrontierLab.

CCF: 2026 seventh list. CAS zone: 2025 historical edition only;
no CAS 2026 edition exists, and we never infer zones from JCR.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "data" / "venue_registry.json"

def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text or "").lower())

def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

def annotate(item: dict, registry: dict | None = None) -> dict:
    """Add publication kind and venue ratings, without inventing a CCF/CAS level."""
    registry = registry or load_registry()
    item = dict(item)
    venue = str(item.get("venue") or "").strip()
    src = str(item.get("source") or "")
    reported = str(item.get("publication_type") or "").lower()
    if item.get("type") == "insight":
        kind = "news"
    elif "arxiv" in norm(venue) or src.lower().startswith("arxiv"):
        kind = "preprint"
    elif reported in ("journal", "conference", "preprint"):
        kind = reported
    else:
        kind = "unknown"
    hit = None
    if kind not in ("preprint", "news"):
        vkey = norm(venue)
        for v in registry.get("venues", []):
            if vkey and vkey in {norm(v.get("name")), norm(v.get("abbr")), *(norm(x) for x in v.get("aliases", []))}:
                hit = v
                break
        if hit:
            kind = hit.get("kind", kind)
    if kind == "news":
        item.update(publication_type="news",venue_abbr="机构资讯",venue_full=venue or src,ccf_grade="不适用",ccf_listed=None,ccf_edition=None,ccf_source="",cas_zone="不适用",cas_edition=None,cas_source="")
        return item
    if kind == "preprint":
        item.update(publication_type="preprint",venue_abbr="arXiv",venue_full="arXiv 预印本平台",ccf_grade="不适用",ccf_listed=None,ccf_edition=None,ccf_source="",cas_zone="不适用",cas_edition=None,cas_source="")
        return item
    item["publication_type"] = kind
    item["venue_abbr"] = hit.get("abbr") if hit else (venue if len(venue) <= 16 else "待核验")
    item["venue_full"] = hit.get("name") if hit else venue or "发表刊会待核验"
    grade = hit.get("ccf") if hit else None
    item["ccf_grade"] = grade or "待核验"
    item["ccf_listed"] = True if grade else None
    item["ccf_edition"] = registry["edition"]["ccf"]
    item["ccf_source"] = hit.get("ccf_source",registry["edition"]["ccf_source"]) if hit else registry["edition"]["ccf_source"]
    if kind == "journal":
        zone = hit.get("cas_zone") if hit else None
        item["cas_zone"] = f"{zone}区" if zone in (1,2,3,4) else "2025版待核验"
        item["cas_edition"] = "2025历史版"
        item["cas_source"] = hit.get("cas_source") if hit and zone in (1,2,3,4) else registry["edition"]["cas_notice"]
        item["cas_top"] = bool(hit.get("cas_top")) if hit and zone in (1,2,3,4) else None
        item["cas_verification"] = hit.get("cas_verification","") if hit else ""
        item["impact_factor"] = hit.get("impact_factor") if hit else None
        item["impact_factor_year"] = hit.get("impact_factor_year") if hit else None
        item["impact_factor_source"] = hit.get("impact_factor_source","") if hit else ""
        item["letpub_url"] = hit.get("letpub_url","") if hit else ""
    elif kind == "conference":
        item["cas_zone"] = "不适用"
        item["cas_edition"] = None
        item["cas_source"] = ""
    else:
        item["cas_zone"] = "类型待核验"
        item["cas_edition"] = None
        item["cas_source"] = ""
    return item
