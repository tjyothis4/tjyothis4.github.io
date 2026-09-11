# tanmayjyothis — personal site

Static site. No frameworks, no dependencies, no web fonts. One stylesheet.
Dark mode follows the system preference automatically.

## Structure

```
index.html          home page (edit by hand)
style.css           the entire design system
posts/*.md          blog posts — this is where you write
templates/          HTML shells for posts and the blog index
build.py            generates blog.html + one page per post
blog.html           GENERATED — don't edit by hand
some-books.html     GENERATED — don't edit by hand
```

## Adding a blog post

1. Create `posts/my-new-post.md`:

```markdown

Write normal markdown here. Headings (`##`), **bold**, *italic*,
[links](https://example.com), lists, `code`, blockquotes and fenced
code blocks are all supported.
```

2. Run the build:

```
python3 build.py
```

3. Commit and push. That's it — `blog.html` and the post page are
   regenerated automatically, newest first.

### Linking to a post published elsewhere (e.g. Medium)

Use an `external` field instead of a body — it appears in the blog
index with an ↗ and links straight out:

```markdown
---
title: Post Title
date: 2026-01-01
external: https://medium.com/@you/the-post
---
```

The filename (minus `.md`) becomes the URL, e.g. `posts/some-books.md`
→ `some-books.html`. Override with a `slug:` field if needed.
