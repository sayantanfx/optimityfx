#!/usr/bin/env python3
"""
Autonomous OptimityFX journal writer — runs in GitHub Actions every 6 hours.
Pipeline: research (Claude + web search) -> write -> generate hero image ->
build static site -> (caller commits/pushes -> Vercel deploys) -> WhatsApp ping.

Required env: ANTHROPIC_API_KEY
Optional env: WHATSAPP_WEBHOOK_URL  (POSTed a JSON payload with the new post)
"""
import os, re, glob, json, sys, datetime, urllib.parse, pathlib
import anthropic, requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOG_DIR = ROOT / "content" / "blog"
IMG_DIR = ROOT / "assets" / "blog"
MODEL = "claude-opus-4-8"

BRAND = """OptimityFX (optimityfx.com) is a premium Indian creative studio: video editing,
color grading, graphic design, AI content production (AI music videos, UGC, product
commercials, AI influencers, VFX), the NextGen Academy (courses), and a store (LUTs,
presets, templates). Audience: brands, creators, music labels, production houses.
Voice: confident, premium, slightly contrarian, practical and genuinely useful. ₹ for pricing."""

def existing_slugs():
    out = []
    for p in glob.glob(str(BLOG_DIR / "*.md")):
        txt = pathlib.Path(p).read_text(encoding="utf-8")
        m = re.search(r"^slug:\s*(.+)$", txt, re.M)
        t = re.search(r"^title:\s*(.+)$", txt, re.M)
        if m:
            out.append((m.group(1).strip(), t.group(1).strip() if t else ""))
    return out

def research_and_write(taken):
    today = datetime.date.today()
    taken_list = "\n".join(f"- {s} :: {t}" for s, t in taken) or "(none yet)"
    system = f"""You are the autonomous OptimityFX blog journal writer.
{BRAND}

Your job each run: research ONE trending, on-brand topic and write ONE complete blog post.

WORKFLOW (follow exactly):
1. RESEARCH: Use web_search to find the TOP trending news/topic RIGHT NOW that overlaps
   OptimityFX's niche (AI video/tools, color grading, filmmaking, short-form & retention
   editing, UGC / ad creative, the creator business, DaVinci Resolve, new model/tool releases,
   platform news). Pick something timely and genuinely useful, not evergreen filler.
2. MATCH: tie it to a specific OptimityFX service so the post naturally adds value and shows
   how OptimityFX can help — without being a hard sell.
3. REWRITE in OptimityFX's voice with a catchy, SEO-friendly headline and SEO keywords.

HARD RULES:
- NEVER write about or mention T-Series in any way. Skip any T-Series angle entirely.
- Do NOT reuse any of these already-published topics or slugs:
{taken_list}
- No fabricated statistics, fake clients, or invented quotes.
- Body is Markdown: use ## H2, optional ### H3, at least one > blockquote, at least one
  - bullet list, **bold**, [text](page.html) links to services.html/portfolio.html/
  academy.html/store.html/contact.html. Do NOT put an H1 in the body (the title is separate).
- 700-1100 words. Open with a hook, end with a natural CTA link.

OUTPUT: After researching, respond with ONE fenced ```json block and nothing else, with keys:
title, slug (lowercase-hyphenated, keyword-rich, unique), category, crumb, filter
(one of: color, edit, ai, business), excerpt, meta_desc (~150 chars), keywords
(comma-separated), read (e.g. "6 min"), image_prompt (a vivid cinematic prompt for a
1200x630 hero image, no text/words in the image), body (the full Markdown),
instagram_caption (hook + 3-5 hashtags), linkedin_post (2-3 short professional paragraphs).
The iso date is {today.isoformat()} and the display date is {today.strftime('%b %-d, %Y')}."""

    messages = [{"role": "user", "content": "Research today's best topic and write the post now."}]
    tools = [{"type": "web_search_20260209", "name": "web_search"}]
    client = anthropic.Anthropic()
    for _ in range(6):  # allow server-tool pause_turn continuations
        resp = client.messages.create(
            model=MODEL, max_tokens=16000, system=system,
            thinking={"type": "adaptive"}, output_config={"effort": "high"},
            tools=tools, messages=messages,
        )
        if resp.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": resp.content})
            continue
        break
    text = "".join(b.text for b in resp.content if b.type == "text")
    m = re.search(r"```json\s*(\{.*\})\s*```", text, re.S) or re.search(r"(\{.*\})", text, re.S)
    if not m:
        sys.exit("No JSON found in model output:\n" + text[:2000])
    data = json.loads(m.group(1))
    data["iso"] = today.isoformat()
    data["date"] = today.strftime("%b %-d, %Y")
    return data

def make_image(prompt, slug):
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    out = IMG_DIR / f"{slug}.jpg"
    q = urllib.parse.quote(f"cinematic, {prompt}, high detail, no text, no watermark")
    url = f"https://image.pollinations.ai/prompt/{q}?width=1200&height=630&nologo=true&model=flux"
    try:
        r = requests.get(url, timeout=120)
        if r.ok and len(r.content) > 5000:
            out.write_bytes(r.content)
            return f"assets/blog/{slug}.jpg"
    except Exception as e:
        print("image generation failed:", e)
    return None  # caller falls back to hero_kw placeholder

def write_post(data):
    slug = data["slug"]
    image = make_image(data.get("image_prompt", data["title"]), slug)
    fm = {
        "title": data["title"], "slug": slug, "category": data.get("category", "AI Tools"),
        "crumb": data.get("crumb", data.get("category", "Article")),
        "filter": data.get("filter", "ai"), "excerpt": data.get("excerpt", ""),
        "meta_desc": data.get("meta_desc", data.get("excerpt", "")),
        "keywords": data.get("keywords", ""), "date": data["date"], "iso": data["iso"],
        "read": data.get("read", "6 min"), "status": "published",
    }
    if image:
        fm["image"] = image
    else:
        fm["hero_kw"] = "cinema,film,studio"
    front = "\n".join(f"{k}: {v}" for k, v in fm.items())
    md = f"---\n{front}\n---\n{data['body'].strip()}\n"
    (BLOG_DIR / f"{data['iso']}-{slug}.md").write_text(md, encoding="utf-8")
    return slug

def notify_whatsapp(data, slug):
    hook = os.environ.get("WHATSAPP_WEBHOOK_URL", "").strip()
    if not hook:
        print("WHATSAPP_WEBHOOK_URL not set — skipping WhatsApp.")
        return
    payload = {
        "title": data["title"],
        "url": f"https://www.optimityfx.com/blog-{slug}.html",
        "excerpt": data.get("excerpt", ""),
        "image": f"https://www.optimityfx.com/assets/blog/{slug}.jpg",
        "instagram_caption": data.get("instagram_caption", ""),
        "linkedin_post": data.get("linkedin_post", ""),
    }
    try:
        requests.post(hook, json=payload, timeout=30)
        print("WhatsApp webhook sent.")
    except Exception as e:
        print("WhatsApp webhook failed:", e)

def main():
    data = research_and_write(existing_slugs())
    slug = write_post(data)
    os.system(f"cd '{ROOT}' && python3 build.py")
    notify_whatsapp(data, slug)
    print(f"PUBLISHED: {data['title']}\nhttps://www.optimityfx.com/blog-{slug}.html")

if __name__ == "__main__":
    main()
