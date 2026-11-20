"""Crossref, Semantic Scholar and official RSS discovery adapters.

Metadata only: no bypassing paywalls, no fabricated peer-review claims.
Each adapter is independently caught by the main collector.
"""
import datetime as dt
import email.utils
import json
import os
import re
import urllib.parse
import xml.etree.ElementTree as ET

ATOM = "{http://www.w3.org/2005/Atom}"


def crossref(cfg, start, request, relevant, valid_date, candidate, today):
    out = []
    for q in cfg.get("crossref_queries", []):
        params = {"query.bibliographic": q, "filter": f"from-pub-date:{start.isoformat()},until-pub-date:{today.isoformat()}", "rows": 12, "sort": "published", "order": "desc"}
        if os.environ.get("CROSSREF_MAILTO"):params["mailto"] = os.environ["CROSSREF_MAILTO"]
        response = json.loads(request("https://api.crossref.org/works?" + urllib.parse.urlencode(params)).decode("utf-8"))
        for o in response.get("message", {}).get("items", []):
            kind = o.get("type", "")
            if kind not in ("journal-article", "proceedings-article"):continue
            title = (o.get("title") or [""])[0].strip()
            abstract = re.sub(r"<[^>]*>", " ", o.get("abstract") or "")
            if not relevant(title, abstract):continue
            parts = (o.get("published") or o.get("published-online") or o.get("issued") or {}).get("date-parts", [])
            parts = parts[0] if parts else []
            if len(parts) < 3:continue
            try:published = dt.date(*parts[:3]).isoformat()
            except (TypeError, ValueError):continue
            if not valid_date(published, start):continue
            doi = (o.get("DOI") or "").strip()
            link = o.get("URL") or ("https://doi.org/" + doi if doi else "")
            if not link:continue
            venue = (o.get("container-title") or [""])[0]
            out.append(candidate("Crossref", title, published, link, abstract, venue, "DOI元数据 · 待人工核验",
                doi=doi, publication_type="journal" if kind == "journal-article" else "conference"))
    return out


def semantic_scholar(cfg, start, request, relevant, valid_date, candidate, today):
    out = []
    extra = {"x-api-key": os.environ["S2_API_KEY"]} if os.environ.get("S2_API_KEY") else {}
    for q in cfg.get("semantic_scholar_queries", []):
        params = {"query": q, "limit": 12, "fields": "title,abstract,url,externalIds,publicationDate,venue,publicationTypes,year"}
        response = json.loads(request("https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params), extra_headers=extra).decode("utf-8"))
        for o in response.get("data", []):
            title = (o.get("title") or "").strip()
            abstract = o.get("abstract") or ""
            if not relevant(title, abstract):continue
            published = o.get("publicationDate") or ""
            if not valid_date(published, start):continue
            doi = (o.get("externalIds") or {}).get("DOI") or ""
            link = ("https://doi.org/" + doi if doi else "") or o.get("url") or ""
            if not link:continue
            types = o.get("publicationTypes") or []
            kind = "journal" if "JournalArticle" in types else "conference" if "Conference" in types else "preprint" if "Preprint" in types else "unknown"
            venue = o.get("venue") or ("arXiv" if kind == "preprint" else "发表刊会待核验")
            out.append(candidate("Semantic Scholar", title, published, link, abstract, venue, "学术图谱记录 · 待人工核验", doi=doi, publication_type=kind))
    return out


def field(node, key):
    for el in node:
        if el.tag.rsplit("}", 1)[-1] == key:
            return " ".join("".join(el.itertext()).split())
    return ""


def parse_date(value):
    if not value:return ""
    try:return dt.date.fromisoformat(value[:10]).isoformat()
    except ValueError:pass
    try:return email.utils.parsedate_to_datetime(value).date().isoformat()
    except (ValueError, TypeError, IndexError):return ""


def official_feed(feed, start, request, relevant, valid_date, candidate):
    root = ET.fromstring(request(feed["url"]))
    entries = root.findall(".//item")
    if not entries:entries = root.findall(".//" + ATOM + "entry")
    result = []
    for entry in entries[:100]:
        title = field(entry, "title")
        abstract = re.sub(r"<[^>]*>", " ", field(entry, "description") or field(entry, "summary") or field(entry, "content"))
        text = (title + " " + abstract).lower()
        context = bool(re.search(r"traffic|transportation|mobility|congestion|spatiotemporal|incident propagation", text))
        if not relevant(title, abstract) and not context:continue
        published = parse_date(field(entry, "pubDate") or field(entry, "date") or field(entry, "published") or field(entry, "updated"))
        if not valid_date(published, start):continue
        link = field(entry, "link")
        if not link:
            for child in entry:
                if child.tag.rsplit("}", 1)[-1] == "link":
                    link = child.get("href") or ""
                    if link:break
        if not link.startswith(("https://", "http://")):continue
        paper = feed.get("kind") == "paper"
        result.append(candidate(feed.get("name", "官方RSS"), title, published, link, abstract,
            feed.get("venue") or feed.get("name", "官方资讯"),
            "官方期刊RSS · 文章元数据待核验" if paper else "机构资讯 · 非论文",
            kind="paper" if paper else "insight",
            publication_type="journal" if paper else "news"))
    return result


def choose_daily(items, today, history, limit=5):
    previous = set()
    for day, ids in history.items():
        try:days = (today - dt.date.fromisoformat(day)).days
        except (TypeError, ValueError):continue
        if 0 < days <= 14 and isinstance(ids, list):previous.update(ids)
    eligible = []
    for x in items:
        try:age = (today - dt.date.fromisoformat(x.get("date", ""))).days
        except (TypeError, ValueError):continue
        if x.get("type") != "paper" or age < 0 or age > 14 or x.get("id") in previous:continue
        tags = x.get("topics") or []
        priority = (5 if x.get("editorial") else 0) + (14 - age) * 2 + min(len(tags), 4)
        if "事件" in tags or "动态图" in tags:priority += 3
        eligible.append((priority, x.get("date"), x.get("id")))
    eligible.sort(reverse=True)
    return [x[2] for x in eligible[:min(5, max(1, limit))]]
