#!/usr/bin/env python3
"""Build the readable HTML archive from the canonical sentence-analysis JSON."""

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "句子解析数据.json"
STYLE_PATH = ROOT / "templates" / "句子解析档案.css"
OUTPUT_PATH = ROOT / "句子解析档案.html"
RUBY_PATTERN = re.compile(r"｜([^《》]+)《([^《》]+)》")


def escape(value):
    return html.escape(value, quote=True)


def render_furigana(source):
    """Convert explicit Aozora-style ruby marks into semantic HTML ruby."""
    pieces = []
    position = 0
    for match in RUBY_PATTERN.finditer(source):
        pieces.append(escape(source[position:match.start()]))
        base, reading = match.groups()
        pieces.append(f"<ruby>{escape(base)}<rt>{escape(reading)}</rt></ruby>")
        position = match.end()
    pieces.append(escape(source[position:]))
    rendered = "".join(pieces)
    if "｜" in rendered or "《" in rendered or "》" in rendered:
        raise ValueError(f"Unparsed furigana markup: {source}")
    return rendered


def render_list(items, renderer):
    return "\n".join(f"      <li>{renderer(item)}</li>" for item in items)


def split_level(value):
    level, separator, detail = value.partition("：")
    return level, detail if separator else ""


def render_entry(entry, index):
    vocabulary = render_list(
        entry["vocabulary"],
        lambda item: f"<code>{escape(item['term'])}｜{escape(item['reading'])}</code>：{escape(item['meaning'])}",
    )
    grammar = render_list(
        entry["grammar"],
        lambda item: f"<code>{escape(item['form'])}</code>：{escape(item['meaning'])} {escape(item['note'])}",
    )
    structure = render_list(
        entry["structure"],
        lambda item: f"<code>{escape(item['label'])}</code>：{escape(item['text'])}",
    )
    difficulty = render_list(
        [
            {"label": "词汇", "value": entry["difficulty"]["vocabulary"]},
            {"label": "语法", "value": entry["difficulty"]["grammar"]},
            {"label": "阅读", "value": entry["difficulty"]["reading"]},
        ],
        lambda item: f"<code>{escape(item['label'])}｜{escape(split_level(item['value'])[0])}</code>：{escape(split_level(item['value'])[1])}",
    )
    return f'''  <article id="{escape(entry['id'])}">
    <div class="entry-heading"><span class="entry-number">{index:02d}</span><h2>{escape(entry['title'])}</h2></div>
    <p class="sentence">{render_furigana(entry['furigana'])}</p>
    <p class="translation"><strong>自然翻译：</strong>{escape(entry['translation'])}</p>

    <h3>句子骨架</h3>
    <ul class="compact">{structure}
    </ul>

    <h3>词汇</h3>
    <ul class="compact">{vocabulary}
    </ul>

    <h3>语法与语气</h3>
    <ul class="compact">{grammar}
    </ul>
    <p class="nuance"><code>语气</code>：{escape(entry['nuance'])}</p>

    <h3>难度</h3>
    <ul class="compact">{difficulty}
    </ul>
  </article>'''


def build():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    entries = data["entries"]
    nav = "".join(
        f'<a href="#{escape(entry["id"])}">{index:02d} {escape(entry["title"])}</a>'
        for index, entry in enumerate(entries, start=1)
    )
    articles = "\n\n".join(render_entry(entry, index) for index, entry in enumerate(entries, start=1))
    page = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(data['title'])}</title>
  <style>
{STYLE_PATH.read_text(encoding="utf-8").rstrip()}
  </style>
</head>
<body>
  <header>
    <h1>{escape(data['title'])}</h1>
    <p>详细解析。笔记 <code>日语学习笔记.md</code> 保留精简知识点。</p>
    <nav>{nav}</nav>
  </header>

{articles}
</body>
</html>
'''
    OUTPUT_PATH.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    build()
