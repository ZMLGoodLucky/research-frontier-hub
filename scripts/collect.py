#!/usr/bin/env python3
"""Daily traffic forecasting literature collector.

No LLM inference and no invented journal ranking. Requires only Python stdlib.
OpenAlex/arXiv/RSS are discovery sources; expert judgments go in data/curated.json.
Usage: python scripts/collect.py [--offline]
"""
from __future__ import annotations
import argparse
import datetime as dt
import email.utils
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = dt.datetime.now(dt.timezone.utc).date()
USER_AGENT = "FrontierLabResearchWatch/1.0 (+https://github.com/ZMLGoodLucky/research-frontier-hub; research-metadata-reader)"
ATOM = "{http://www.w3.org/2005/Atom}"


def read_json(file: Path, fallback):
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return fallback


def request(url: str, *, timeout: int = 18) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/atom+xml, application/rss+xml, application/xml;q=.9, */*;q=.5"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise ValueError(f"HTTP {resp.status}")
        return resp.read(2_500_000)


def safe_url(text: str | None) -> str:
    if not text: return ""
    url = text.strip()
    return url if urllib.parse.urlparse(url).scheme in {"http", "https"} else ""


def flatten_abstract(inverted) -> str:
    if not isinstance(inverted, dict): return ""
    words = {}
    for word, indices in inverted.items():
        if isinstance(indices, list):
            for pos in indices:
                if isinstance(pos, int) and 0 <= pos < 5000: words[pos] = str(word)
    return " ".join(words[i] for i in sorted(words))[:1800]


def relevant(title: str, abstract: str = "") -> bool:
    """Strict traffic *road* forecast filter to avoid network/air/maritime traffic."""
    t = (title or "").lower(); context = (t + " " + (abstract or "")[:800]).lower()
    if re.search(r"network traffic|packet traffic|air traffic|maritime traffic|cellular traffic|pedestrian trajectory|vehicle trajectory", t):
        return False
    road = bool(re.search(r"traffic flow|road traffic|traffic speed|traffic forecasting|traffic prediction|traffic state|traffic congestion|transportation network|urban mobility", t))
    forecasting = bool(re.search(r"forecast|predict|prediction|prognosis", t))
    if road and forecasting: return True
    return bool("traffic" in t and forecasting and re.search(r"road|urban|traffic flow|transportation",context))


def infer_topic(title: str, abstract: str = "") -> tuple[str, list[str]]:
    t = (title + " " + abstract[:400]).lower()
    tags = ["交通预测"]
    if any(w in t for w in ("incident", "accident", "event", "anomaly", "aperiodic")): tags.append("事件")
    if any(w in t for w in ("self-supervised", "contrastive learning", "masked reconstruction")): tags.append("自监督学习")
    if any(w in t for w in ("dynamic graph", "adaptive graph", "graph learning", "graph neural")): tags.append("动态图")
    if any(w in t for w in ("multi-view", "multiview", "multimodal", "weather", "external factors", "large language model")): tags.append("多模态")
    if any(w in t for w in ("transfer", "zero-shot", "generalization", "cross-domain", "domain adaptation")): tags.append("泛化")
    primary = ("事件与异常扰动" if "事件" in tags else "自监督学习" if "自监督学习" in tags else "动态图与依赖" if "动态图" in tags else "多模态与外部因素" if "多模态" in tags else "跨域与零样本" if "泛化" in tags else "时空预测")
    return primary, tags


def digest_id(source: str, key: str) -> str:
    return source + "-" + hashlib.sha1(key.strip().lower().encode("utf-8")).hexdigest()[:14]


def candidate(source: str, title: str, date: str, link: str, abstract: str, venue: str, status: str, *, doi: str = "") -> dict:
    category, topics = infer_topic(title, abstract)
    abstract = re.sub(r"\s+", " ", abstract or "").strip()
    return {
        "id": digest_id(source.lower().replace(' ', '-'), doi or link), "type": "insight" if source.startswith("MIT") else "paper",
        "category": category if not source.startswith("MIT") else "权威资讯", "topics": topics,
        "title": title.strip(), "title_zh": "", "date": date, "source": source, "venue": venue,
        "status": status, "level": "等级尚未核验；不能依据元数据推定分区 / CCF 等级", "verified": False,
        "problem": "自动发现候选：尚未核对全文的研究问题与创新贡献，请点击原文阅读。",
        "method": ("原始英文摘要摘录（未经人工核验）：" + abstract[:800]) if abstract else "来源未提供摘要，请查看原文。",
        "contribution": "自动采集不进行创新性、领先性或方法有效性的判断。",
        "relevance": "待人工审核与多视角、自监督、动态图或事件引导交通预测研究的直接关联。",
        "questions": ["论文是否公开实验数据与源码？", "是否使用与既有工作一致的评价协议？"],
        "url": link, "doi": doi, "code": "", "featured": False, "editorial": False,
    }


def openalex(cfg: dict, start: dt.date) -> list[dict]:
    all_items: list[dict] = []
    for query in cfg["openalex_queries"]:
        params = {"search": query, "filter": f"from_publication_date:{start.isoformat()}", "per_page": "20", "sort": "publication_date:desc"}
        if os.environ.get("OPENALEX_API_KEY"): params["api_key"] = os.environ["OPENALEX_API_KEY"]
        endpoint = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
        response = json.loads(request(endpoint).decode("utf-8"))
        for obj in response.get("results", []):
            title = (obj.get("title") or "").strip(); abstract = flatten_abstract(obj.get("abstract_inverted_index"))
            if not relevant(title, abstract): continue
            date = obj.get("publication_date") or ""
            if not valid_date(date,start): continue
            doi = (obj.get("doi") or "").replace("https://doi.org/", "")
            location = obj.get("primary_location") or {}; journal = (location.get("source") or {}).get("display_name") or "OpenAlex 数据源"
            link = safe_url(obj.get("doi")) or safe_url(obj.get("id"))
            if not link: continue
            kind = obj.get("type") or "未知类型"
            all_items.append(candidate("OpenAlex",title,date,link,abstract,journal,f"数据库记录：{kind} · 尚待核验",doi=doi))
    return all_items


def valid_date(text: str, start: dt.date) -> bool:
    try: return start <= dt.date.fromisoformat(text) <= TODAY
    except (TypeError, ValueError): return False


def arxiv(cfg: dict, start: dt.date) -> list[dict]:
    items=[]
    for i, q in enumerate(cfg["arxiv_queries"]):
        if i: time.sleep(3.2)  # respect arXiv API rate guidance
        params={"search_query":q,"start":0,"max_results":35,"sortBy":"submittedDate","sortOrder":"descending"}
        root=ET.fromstring(request("https://export.arxiv.org/api/query?"+urllib.parse.urlencode(params)))
        for entry in root.findall(ATOM+"entry"):
            title=" ".join((entry.findtext(ATOM+"title") or "").split())
            abstract=" ".join((entry.findtext(ATOM+"summary") or "").split())
            if not relevant(title,abstract):continue
            published=(entry.findtext(ATOM+"published") or "")[:10]
            if not valid_date(published,start):continue
            link=entry.findtext(ATOM+"id") or ""
            link=safe_url(link)
            if not link:continue
            items.append(candidate("arXiv", title, published, link, abstract, "arXiv 预印本", "预印本 · 非录用证明"))
    return items


def mit_rss(cfg: dict, start: dt.date) -> list[dict]:
    items=[]
    for feed in read_json(ROOT/"data/feeds.json",[]):
        if not feed.get("enabled"):continue
        root=ET.fromstring(request(feed["url"]))
        for e in root.findall(".//item"):
            title=" ".join((e.findtext("title") or "").split())
            summary=re.sub("<[^>]*>", " ", e.findtext("description") or "")
            if not re.search(r"traffic|transportation|mobility|congestion|spatiotemporal", (title+" "+summary).lower()):continue
            date_raw=e.findtext("pubDate") or ""
            try:published=email.utils.parsedate_to_datetime(date_raw).date().isoformat()
            except (TypeError,ValueError):continue
            if not valid_date(published,start):continue
            link=safe_url(e.findtext("link"))
            if not link:continue
            items.append(candidate("MIT News",title,published,link,summary,"MIT News · 官方报道","机构资讯 · 非学术论文"))
    return items


def deduplicate(items: list[dict], limit: int) -> list[dict]:
    seen=set(); result=[]
    for obj in sorted(items,key=lambda a:(int(bool(a.get("editorial"))), a.get("date", "")),reverse=True):
        # DOI, arXiv link and normalized title as multi-source duplicate guards
        title=re.sub(r"[^a-z0-9]+","",(obj.get("title") or "").lower())[:110]
        doi=(obj.get("doi") or "").lower()
        url=(obj.get("url") or "").split("?")[0].rstrip("/").lower()
        keys={"title:"+title,"url:"+url}
        if doi:keys.add("doi:"+doi)
        if keys & seen:continue
        seen.update(keys);result.append(obj)
        if len(result)>=limit:break
    return sorted(result, key=lambda a: (a.get("date", ""), int(bool(a.get("editorial")))), reverse=True)


def main():
    args=argparse.ArgumentParser();args.add_argument("--offline",action="store_true",help="Write curated seed without network; use for first deployment and tests")
    options=args.parse_args()
    cfg=read_json(ROOT/"config/interests.json",{})
    curated=read_json(ROOT/"data/curated.json",[])
    output=ROOT/"site/data.json"
    existing=read_json(output,{})
    historic=[a for a in existing.get("items",[]) if not a.get("editorial")]
    status=[];new=[]
    if not options.offline:
        start=TODAY-dt.timedelta(days=int(cfg.get("days_to_collect",14)))
        for name, fn in (("OpenAlex",openalex),("arXiv",arxiv),("MIT News RSS",mit_rss)):
            try:
                entries=fn(cfg,start);new.extend(entries)
                status.append({"source":name,"ok":True,"collected":len(entries)})
                print(f"[OK] {name}: {len(entries)} records",flush=True)
            except Exception as exc:
                status.append({"source":name,"ok":False,"error":str(exc)[:160]})
                print(f"[WARNING] {name}: {exc}",file=sys.stderr,flush=True)
    else:
        status=[{"source":"离线初始化","ok":True,"collected":len(curated),"note":"首次版本包含人工精选样例，尚未进行在线自动采集"}]
    historic=[a for a in historic if a.get("date") and a.get("url")]
    combined=deduplicate(curated+new+historic,limit=max(90,int(cfg.get("max_auto_items",70))+len(curated)))
    successful=any(s["ok"] for s in status)
    now=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    out={"schema_version":"1.0","generated_at": now if successful else existing.get("generated_at",now),
         "last_checked_at":now,"timezone":"Asia/Shanghai","sources_note":"自动发现未进行同行评审；期刊与会议分区须人工核实。",
         "fetch_status":status,"items":combined}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # File:// fallback preview. Deliberately includes same vetted metadata as JSON.
    (ROOT/"site/seed.js").write_text("window.FRONTIER_INITIAL_DATA = "+json.dumps(out,ensure_ascii=False,separators=(',',':'))+";\n",encoding="utf-8")
    print(f"Saved {len(combined)} entries to {output}")
    return 0

if __name__=="__main__":sys.exit(main())
