#!/usr/bin/env python3
"""Generate a sourced Chinese inference-systems report and static blog pages."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo


ROOT = pathlib.Path(__file__).resolve().parents[1]
POSTS = ROOT / "blog" / "posts"
DATA = ROOT / "blog" / "data"
TZ = ZoneInfo("Asia/Shanghai")

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["date", "title", "deck", "top_items", "engineering", "backend", "resources", "industry", "actions"],
    "properties": {
        "date": {"type": "string"},
        "title": {"type": "string"},
        "deck": {"type": "string"},
        "top_items": {"type": "array", "minItems": 3, "maxItems": 5, "items": {"$ref": "#/$defs/item"}},
        "engineering": {"$ref": "#/$defs/section"},
        "backend": {"$ref": "#/$defs/section"},
        "resources": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"$ref": "#/$defs/item"}},
        "industry": {"$ref": "#/$defs/section"},
        "actions": {"type": "array", "minItems": 3, "maxItems": 6, "items": {"type": "string"}},
    },
    "$defs": {
        "source": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "url"],
            "properties": {"name": {"type": "string"}, "url": {"type": "string"}},
        },
        "item": {
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "summary", "judgment", "sources"],
            "properties": {
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "judgment": {"type": "string"},
                "sources": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"$ref": "#/$defs/source"}},
            },
        },
        "section": {
            "type": "object",
            "additionalProperties": False,
            "required": ["content", "judgment", "sources"],
            "properties": {
                "content": {"type": "string"},
                "judgment": {"type": "string"},
                "sources": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"$ref": "#/$defs/source"}},
            },
        },
    },
}


def api_report(day: str) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required")
    model = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")
    prompt = f"""生成 {day} 的中文《推理系统技术日报》。
聚焦 AI/大模型/推理系统，以及后端、Golang、Rust、Kubernetes。只筛选最近24–48小时真正重要的变化；没有重要变化时明确写出，不得凑数。优先官方公告、项目仓库、论文原文和公司公告。每个事实必须附可直接打开的一手来源 URL。内容要有技术深度、工程判断、可落地工具/项目/论文、产业与投资信号。不要重复前一天已报道的旧闻，除非出现实质进展。输出严格符合给定 JSON schema。"""
    payload = {
        "model": model,
        "instructions": "你是严谨的推理系统技术编辑。使用网页搜索核验所有时效性事实；不要编造版本、日期、性能数字或链接。用简洁中文写作。",
        "input": prompt,
        "tools": [{"type": "web_search"}],
        "reasoning": {"effort": "low"},
        "text": {"verbosity": "medium", "format": {"type": "json_schema", "name": "daily_report", "strict": True, "schema": SCHEMA}},
        "store": False,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise SystemExit(f"OpenAI API failed: HTTP {exc.code}: {detail}") from exc
    chunks = []
    for output in raw.get("output", []):
        for content in output.get("content", []):
            if content.get("type") == "output_text":
                chunks.append(content.get("text", ""))
    if not chunks:
        raise SystemExit("OpenAI API returned no output_text")
    return json.loads("".join(chunks))


def safe_url(value: str) -> str:
    return value if re.match(r"^https://", value or "") else "#"


def sources_html(sources: list[dict]) -> str:
    links = []
    seen = set()
    for source in sources:
        url = safe_url(source.get("url", ""))
        if url == "#" or url in seen:
            continue
        seen.add(url)
        links.append(f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{html.escape(source.get("name") or "来源")}</a>')
    return '<div class="source-list">' + "".join(links) + "</div>"


def item_list(items: list[dict]) -> str:
    rows = []
    for item in items:
        rows.append(
            "<li><strong>" + html.escape(item["title"]) + "</strong> — " + html.escape(item["summary"])
            + '<span class="judgment">判断：' + html.escape(item["judgment"]) + "</span>"
            + sources_html(item["sources"]) + "</li>"
        )
    return "<ol>" + "".join(rows) + "</ol>"


def section(number: str, title: str, body: str) -> str:
    return f'<section class="report-section"><div class="section-number">{number}</div><h2>{html.escape(title)}</h2>{body}</section>'


def page_shell(title: str, body: str, prefix: str = "../../") -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="description" content="AI 推理系统、Golang、Rust 与 Kubernetes 技术日报"><title>{html.escape(title)} — Moersity</title>
<link rel="stylesheet" href="{prefix}css/common.css"><link rel="stylesheet" href="{prefix}css/blog.css"></head>
<body><nav><a class="nav-logo" href="{prefix}">Moersity</a><div class="nav-links"><a href="{prefix}blog/">技术日报</a><a href="{prefix}about.html">About Me</a></div></nav>{body}</body></html>"""


def render_post(report: dict) -> str:
    day = report["date"]
    blocks = [
        section("01", "今日最重要", item_list(report["top_items"])),
        section("02", "AI 推理 / 系统工程动态", f'<p>{html.escape(report["engineering"]["content"])}</p><p class="judgment">判断：{html.escape(report["engineering"]["judgment"])}</p>' + sources_html(report["engineering"]["sources"])),
        section("03", "后端与云原生 / Rust / Golang 动态", f'<p>{html.escape(report["backend"]["content"])}</p><p class="judgment">判断：{html.escape(report["backend"]["judgment"])}</p>' + sources_html(report["backend"]["sources"])),
        section("04", "值得看的项目 / 论文 / 工具", item_list(report["resources"])),
        section("05", "产业趋势与投资信号", f'<p>{html.escape(report["industry"]["content"])}</p><p class="judgment">判断：{html.escape(report["industry"]["judgment"])}</p>' + sources_html(report["industry"]["sources"])),
        section("06", "行动建议", "<ol>" + "".join(f"<li>{html.escape(x)}</li>" for x in report["actions"]) + "</ol>"),
    ]
    body = f'<main class="blog-shell"><header class="post-header"><div class="blog-kicker">推理系统技术日报 · {html.escape(day)}</div><h1>{html.escape(report["title"])}</h1><p class="post-deck">{html.escape(report["deck"])}</p></header><div class="report-grid">{"".join(blocks)}</div><a class="back-link" href="../">← 返回全部日报</a></main>'
    return page_shell(report["title"], body)


def render_index(reports: list[dict]) -> str:
    cards = []
    for report in sorted(reports, key=lambda x: x["date"], reverse=True):
        cards.append(f'<a class="post-card" href="posts/{html.escape(report["date"])}.html"><div class="post-meta">{html.escape(report["date"])}</div><h2>{html.escape(report["title"])}</h2><p>{html.escape(report["deck"])}</p></a>')
    body = f'<main class="blog-shell"><div class="blog-kicker">Inference Systems Briefing</div><h1 class="blog-title">推理系统<br>技术日报</h1><p class="blog-intro">每天筛选 AI 推理系统、Golang、Rust 与 Kubernetes 的关键变化。重工程判断、可落地实践和一手来源，不堆新闻。</p><div class="post-list">{"".join(cards)}</div></main>'
    return page_shell("推理系统技术日报", body, prefix="../")


def render_feed(reports: list[dict]) -> str:
    items = []
    for report in sorted(reports, key=lambda x: x["date"], reverse=True)[:20]:
        url = f"https://moersity.github.io/blog/posts/{report['date']}.html"
        items.append(f"<item><title>{html.escape(report['title'])}</title><link>{url}</link><guid>{url}</guid><pubDate>{dt.datetime.fromisoformat(report['date']).strftime('%a, %d %b %Y 00:00:00 +0800')}</pubDate><description>{html.escape(report['deck'])}</description></item>")
    return '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Moersity 推理系统技术日报</title><link>https://moersity.github.io/blog/</link><description>AI 推理系统与云原生技术日报</description>' + "".join(items) + "</channel></rss>"


def validate(report: dict, day: str) -> None:
    if report.get("date") != day:
        raise SystemExit(f"report date mismatch: expected {day}, got {report.get('date')}")
    urls = re.findall(r"https://[^\s<]+", json.dumps(report, ensure_ascii=False))
    if len(urls) < 4:
        raise SystemExit("report must contain at least four HTTPS sources")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now(TZ).date().isoformat())
    parser.add_argument("--input", type=pathlib.Path, help="Use an existing report JSON instead of the API")
    args = parser.parse_args()
    report = json.loads(args.input.read_text()) if args.input else api_report(args.date)
    validate(report, args.date)
    POSTS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / f"{args.date}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (POSTS / f"{args.date}.html").write_text(render_post(report))
    reports = [json.loads(path.read_text()) for path in DATA.glob("*.json")]
    (ROOT / "blog" / "index.html").write_text(render_index(reports))
    (ROOT / "blog" / "feed.xml").write_text(render_feed(reports))
    print(f"Generated {args.date}: {report['title']}")


if __name__ == "__main__":
    main()
