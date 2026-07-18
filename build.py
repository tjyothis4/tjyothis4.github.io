#!/usr/bin/env python3
"""
build.py — turns posts/*.md into HTML pages and regenerates blog.html.

Usage:            python3 build.py
Add a post:       create posts/my-post.md with front matter (see README.md),
                  run python3 build.py, commit, push. Done.

Zero dependencies. Python 3.8+.
"""

import html
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
POSTS = ROOT / "posts"
TEMPLATES = ROOT / "templates"


# ---------- front matter ----------

def parse_front_matter(text):
    """Parse a leading '---' block of key: value lines. Returns (meta, body)."""
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        raise ValueError("missing front matter (--- block) at top of file")
    meta = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        meta[key.strip().lower()] = value.strip().strip('"').strip("'")
    return meta, text[m.end():]


# ---------- markdown (small, covers what a blog needs) ----------

def md_inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\w_])_([^_]+)_(?![\w_])", r"<em>\1</em>", s)
    return s


def md_to_html(md):
    out = []
    lines = md.split("\n")
    i = 0
    para, in_ul, in_ol = [], False, False

    def flush_para():
        if para:
            out.append("<p>" + md_inline(" ".join(para)) + "</p>")
            para.clear()

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # fenced code block
        if stripped.startswith("```"):
            flush_para(); close_lists()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
            i += 1
            continue

        # blank line
        if not stripped:
            flush_para(); close_lists()
            i += 1
            continue

        # heading
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush_para(); close_lists()
            level = len(m.group(1)) + 1  # md '#' -> h2 (h1 is the post title)
            out.append(f"<h{level}>{md_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # horizontal rule
        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            flush_para(); close_lists()
            out.append("<hr />")
            i += 1
            continue

        # blockquote
        if stripped.startswith(">"):
            flush_para(); close_lists()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>" + md_inline(" ".join(quote)) + "</p></blockquote>")
            continue

        # unordered list
        if re.match(r"^[-*]\s+", stripped):
            flush_para()
            if in_ol:
                out.append("</ol>"); in_ol = False
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append("<li>" + md_inline(re.sub(r"^[-*]\s+", "", stripped)) + "</li>")
            i += 1
            continue

        # ordered list
        if re.match(r"^\d+\.\s+", stripped):
            flush_para()
            if in_ul:
                out.append("</ul>"); in_ul = False
            if not in_ol:
                out.append("<ol>"); in_ol = True
            out.append("<li>" + md_inline(re.sub(r"^\d+\.\s+", "", stripped)) + "</li>")
            i += 1
            continue

        # plain paragraph line
        para.append(stripped)
        i += 1

    flush_para(); close_lists()
    return "\n".join(out)


# ---------- build ----------

def display_date(iso):
    d = date.fromisoformat(iso)
    return d.strftime("%B %-d, %Y") if hasattr(d, "strftime") else iso


def display_updated(value):
    """Accepts YYYY-MM ('July 2026') or YYYY-MM-DD ('July 18, 2026')."""
    if re.match(r"^\d{4}-\d{2}$", value):
        return date.fromisoformat(value + "-01").strftime("%B %Y")
    return display_date(value)


def date_line(p):
    line = display_date(p["date"])
    if p.get("updated"):
        line += f" · Updated {display_updated(p['updated'])}"
    return line


def main():
    post_template = (TEMPLATES / "post.html").read_text()
    blog_template = (TEMPLATES / "blog.html").read_text()
    year = str(date.today().year)

    posts = []
    for md_file in sorted(POSTS.glob("*.md")):
        meta, body = parse_front_matter(md_file.read_text())
        if "title" not in meta or "date" not in meta:
            raise ValueError(f"{md_file.name}: front matter needs at least title and date")
        meta["slug"] = meta.get("slug", md_file.stem)
        meta["description"] = meta.get("description", "")
        meta["body"] = body
        posts.append(meta)

    posts.sort(key=lambda p: p["date"], reverse=True)

    # individual post pages (external posts have no page of their own)
    for p in posts:
        if p.get("external"):
            continue
        page = (
            post_template
            .replace("{{title}}", html.escape(p["title"], quote=False))
            .replace("{{description}}", html.escape(p["description"]))
            .replace("{{date_iso}}", p["date"])
            .replace("{{date_display}}", date_line(p))
            .replace("{{content}}", md_to_html(p["body"]))
            .replace("{{year}}", year)
        )
        out = ROOT / f"{p['slug']}.html"
        out.write_text(page)
        print(f"  wrote {out.name}")

    # blog index
    items = []
    for p in posts:
        href = p.get("external") or f"{p['slug']}.html"
        target = ' target="_blank" rel="noopener"' if p.get("external") else ""
        mark = '<span class="external-mark">↗</span>' if p.get("external") else ""
        items.append(
            f'                <li><a href="{href}"{target}>'
            f'<span class="post-title">{html.escape(p["title"], quote=False)}{mark}</span>'
            f'<span class="post-meta">{display_date(p["date"])}</span></a></li>'
        )
    blog = (
        blog_template
        .replace("{{posts}}", "\n".join(items))
        .replace("{{year}}", year)
    )
    (ROOT / "blog.html").write_text(blog)
    print(f"  wrote blog.html ({len(posts)} posts)")


if __name__ == "__main__":
    main()
