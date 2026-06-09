# OptimityFX Blog Content Pipeline

Every blog post is a Markdown file in `content/blog/*.md`. Running `python3 build.py`
turns each one into its own SEO page (`blog-<slug>.html`) and rebuilds `sitemap.xml`.

## How to add a post

1. Create `content/blog/YYYY-MM-DD-<slug>.md` (copy an existing one).
2. Fill the frontmatter (between the `---` fences) and write the body in Markdown.
3. Set `status: draft` while it's being reviewed; change to `status: published` to go live.
4. Run `python3 build.py`, commit, push → Vercel deploys automatically.

## Frontmatter fields

| field | required | notes |
|-------|----------|-------|
| `title` | yes | H1 + `<title>` |
| `slug` | yes | URL becomes `blog-<slug>.html` — keep it keyword-rich, lowercase, hyphenated |
| `category` | yes | e.g. Color Grading, AI Tools, Editing, Business, UGC, Workflow |
| `filter` | yes | one of: `color`, `edit`, `ai`, `business` (drives the blog filter buttons) |
| `crumb` | no | breadcrumb label (defaults to category) |
| `excerpt` | yes | card teaser |
| `meta_desc` | yes | Google search-result description (~150 chars) |
| `keywords` | yes | comma-separated SEO keywords |
| `date` | yes | human display, e.g. `Jun 9, 2026` |
| `iso` | yes | `YYYY-MM-DD` — used for sorting + sitemap `lastmod` + JSON-LD |
| `read` | no | e.g. `5 min` |
| `hero_kw` | no | placeholder image keywords (used only if `image` is empty) |
| `image` | no | path to a real hero image, e.g. `assets/blog/<slug>.jpg` (Higgsfield output) |
| `status` | no | `published` (default) or `draft` |
| `cta_h` / `cta_p` | no | override the bottom call-to-action text |

## Markdown supported

`## H2`, `### H3`, `> blockquote`, `- bullet lists`, `**bold**`, `*italic*`, `[link](url.html)`, paragraphs.

## Draft → publish (the approval gate)

- A file with `status: draft` is **excluded** from the build — it won't appear anywhere.
- To approve: flip `status: draft` → `status: published`, rebuild, push.
- The daily automation drops new posts as `status: draft` so nothing goes public without a human flip.
