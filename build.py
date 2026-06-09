#!/usr/bin/env python3
"""OptimityFX static site generator — wraps page bodies in a shared shell.
Produces plain static HTML. Run: python3 build.py"""
import os, re, glob

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{keywords}">
<meta name="author" content="OptimityFX">
<link rel="canonical" href="https://optimityfx.com/{slug}">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#07090C">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://optimityfx.com/{slug}">
<meta property="og:image" content="{og_image}">
<meta property="og:site_name" content="OptimityFX">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_image}">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="assets/favicon.svg">
<link rel="manifest" href="manifest.json">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="css/style.css?v=20260607">
{jsonld}
</head>
<body>
<div class="progress"></div>
"""

# --- Single source of truth for services (id, title, short-desc, svg inner) ---
SVC_ICON = {
 "editing":'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9 5 3-5 3z"/>',
 "grading":'<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18z"/>',
 "design":'<path d="M12 3v18M3 12h18"/><circle cx="12" cy="12" r="9"/>',
 "ai-music":'<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
 "ugc":'<rect x="2" y="7" width="15" height="10" rx="2"/><path d="m17 9 5-2v10l-5-2"/>',
 "commercial":'<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><path d="M3 6h18M16 10a4 4 0 0 1-8 0"/>',
 "ai-tvc":'<rect x="2" y="7" width="20" height="13" rx="2"/><path d="m8 3 4 4 4-4"/>',
 "ai-influencer":'<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
 "ai-vfx":'<path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M5 19l1 2 1-2 2-1-2-1-1-2-1 2-2 1z"/>',
}
# (id, title, short-desc, is_ai)
SERVICES = [
 ("editing","Video Editing","Reels, films, ads, long-form",False),
 ("grading","Color Grading","Cinematic looks & LUTs",False),
 ("design","Graphic Design","Brand, thumbnails, key art",False),
 ("ai-music","AI Music Video","Concept to final cut",True),
 ("ugc","AI UGC","Creator-style content at scale",True),
 ("commercial","AI Product Commercial","Scroll-stopping product ads",True),
 ("ai-tvc","AI TV Advertisement","Broadcast-ready AI ad films",True),
 ("ai-influencer","AI Influencer","AI creators & spokespeople",True),
 ("ai-vfx","AI VFX","AI effects & compositing",True),
]
def _svc_icon(sid):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">{SVC_ICON[sid]}</svg>'
def _drop_item(sid,t,d,ai):
    tag = ' <span class="ai-tag">AI POWERED</span>' if ai else ''
    return (f'          <a href="service-{sid}.html"><span class="di">{_svc_icon(sid)}</span>'
            f'<span><span class="dt">{t}{tag}</span><span class="dd">{d}</span></span></a>')
SERVICES_DROP = '<div class="drop">\n' + "\n".join(_drop_item(*s) for s in SERVICES) + '\n        </div>'

def nav(active):
    items = [("services.html","Services"),("portfolio.html","Work"),("academy.html","Academy"),
             ("store.html","Store"),("b2b.html","B2B"),("blog.html","Blog"),("about.html","About")]
    def li(h,t):
        cls = ' class="active"' if h==active else ''
        if h == "services.html":
            caret = '<svg class="caret" viewBox="0 0 12 8" fill="none"><path d="M1 1.5 6 6.5 11 1.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
            return f'<li class="has-drop"><a href="{h}"{cls}>{t} {caret}</a>{SERVICES_DROP}</li>'
        return f'<li><a href="{h}"{cls}>{t}</a></li>'
    links = "".join(li(h,t) for h,t in items)
    drawer = "".join(f'<a href="{h}">{t}</a>' for h,t in items)
    return f"""<header class="nav">
  <div class="wrap nav-inner">
    <a href="index.html" class="brand"><img src="assets/logo.png" alt="OptimityFX — Your Vision, Graded" class="brand-img" width="878" height="296"></a>
    <nav class="nav-links" aria-label="Primary">{links}</nav>
    <div class="nav-cta">
      <a href="contact.html" class="btn btn-accent btn-sm">Start a Project</a>
      <button class="burger" aria-label="Toggle menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<div class="m-drawer">{drawer}<a href="contact.html" class="btn btn-accent">Start a Project</a></div>
"""

FOOTER = """<footer class="footer">
  <div class="wrap">
    <div class="footer-top">
      <div class="footer-brand">
        <a href="index.html" class="brand brand-foot"><img src="assets/logo.png" alt="OptimityFX — Your Vision, Graded" class="brand-img" width="878" height="296"></a>
        <p>Your Vision — Graded. A premium creative studio for video, color & AI-powered content.</p>
        <div class="foot-social">
          <a href="https://www.youtube.com/@OptimityFX" target="_blank" rel="noopener" aria-label="OptimityFX on YouTube"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M23 12s0-3.3-.4-4.9a2.5 2.5 0 0 0-1.8-1.8C19.2 5 12 5 12 5s-7.2 0-8.8.4A2.5 2.5 0 0 0 1.4 7.2C1 8.7 1 12 1 12s0 3.3.4 4.9a2.5 2.5 0 0 0 1.8 1.8C4.8 19 12 19 12 19s7.2 0 8.8-.4a2.5 2.5 0 0 0 1.8-1.8C23 15.3 23 12 23 12zM9.8 15.3V8.7l6 3.3z"/></svg></a>
          <a href="https://www.instagram.com/optimityfx/" target="_blank" rel="noopener" aria-label="OptimityFX on Instagram"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg></a>
          <a href="https://www.linkedin.com/company/optimityfx/" target="_blank" rel="noopener" aria-label="OptimityFX on LinkedIn"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5A2.5 2.5 0 1 1 0 3.5a2.5 2.5 0 0 1 4.98 0zM.5 8h4V24h-4zM8 8h3.8v2.2h.06c.53-1 1.83-2.2 3.77-2.2 4.03 0 4.77 2.65 4.77 6.1V24h-4v-7.1c0-1.7-.03-3.9-2.37-3.9-2.38 0-2.74 1.85-2.74 3.77V24H8z"/></svg></a>
          <a href="https://vimeo.com/optimityfx" target="_blank" rel="noopener" aria-label="OptimityFX on Vimeo"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M22 7.4c-.1 2.1-1.6 5-4.4 8.6-2.9 3.8-5.4 5.7-7.4 5.7-1.2 0-2.3-1.2-3.1-3.5C6 16.5 5.4 11 4.3 9.6c-.4-.5-.9-.5-1.6-.1l-1-1.3c1.7-1.5 3.4-3.2 4.4-3.3 1.2-.1 2 .7 2.3 2.5.4 2.4.7 3.9.9 4.5.5 2.3 1 2.3 1.6 1.3.4-.8.7-2 .7-3.6 0-1.3-.5-1.9-1.5-1.9-.4 0-1 .1-1.4.3.8-2.7 2.4-4 4.7-3.9 1.7.1 2.5 1.2 2.4 3.3z"/></svg></a>
        </div>
      </div>
      <div><h5>Services</h5><ul><li><a href="service-editing.html">Video Editing</a></li><li><a href="service-grading.html">Color Grading</a></li><li><a href="service-design.html">Graphic Design</a></li><li><a href="service-ai-music.html">AI Music Video</a></li><li><a href="service-ugc.html">AI UGC</a></li><li><a href="service-commercial.html">AI Product Commercial</a></li><li><a href="service-ai-tvc.html">AI TV Advertisement</a></li><li><a href="service-ai-influencer.html">AI Influencer</a></li><li><a href="service-ai-vfx.html">AI VFX</a></li></ul></div>
      <div><h5>Explore</h5><ul><li><a href="portfolio.html">Portfolio</a></li><li><a href="academy.html">NextGen Academy</a></li><li><a href="store.html">Digital Store</a></li><li><a href="b2b.html">B2B Solutions</a></li><li><a href="blog.html">Blog</a></li></ul></div>
      <div><h5>Company</h5><ul><li><a href="about.html">About Us</a></li><li><a href="about.html#team">Our Team</a></li><li><a href="contact.html">Contact</a></li><li><a href="privacy.html">Privacy Policy</a></li><li><a href="terms.html">Terms & Conditions</a></li></ul></div>
      <div class="footer-brand">
        <h5>Get In Touch</h5>
        <ul class="foot-contact">
          <li><a href="mailto:optimityfx.studio@gmail.com">optimityfx.studio@gmail.com</a></li>
          <li><a href="tel:+917001202156">+91 70012 02156</a></li>
        </ul>
        <a href="contact.html" class="btn btn-accent btn-sm" style="margin-top:16px">Start a Project</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; <span data-year>2026</span> OptimityFX. All rights reserved. Crafted with vision.</p>
      <div class="legal-links"><a href="privacy.html">Privacy</a><a href="terms.html">Terms</a><a href="contact.html">Contact</a></div>
    </div>
  </div>
</footer>
<script src="js/main.js?v=20260607"></script>
</body>
</html>
"""

# arrow icon shorthand
ARR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
CHK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>'

# Topic-relevant image helper (LoremFlickr serves keyword-matched photos; lock pins a stable image)
_lock = [0]
def IMG(keywords, w=800, h=600, lock=None):
    if lock is None:
        _lock[0] += 1; lock = _lock[0]
    kw = ",".join(k.strip() for k in keywords.split(","))
    return f"https://loremflickr.com/{w}/{h}/{kw}?lock={lock}"

# Young, smart male avatar (DiceBear avataaars — neat hair, light/no beard, smart glasses, corporate bg)
def AVATAR(seed):
    s = seed.replace(" ", "+")
    return ("https://api.dicebear.com/7.x/avataaars/svg?seed=" + s +
            "&radius=50&backgroundColor=14304a,1b2a44,12303f&backgroundType=gradientLinear"
            "&clothing=blazerAndShirt,blazerAndSweater,collarAndSweater,shirtCrewNeck"
            "&clothesColor=262e33,3c4f5c,25557c,5199e4"
            "&top=shortFlat,shortRound,shortWaved,theCaesarAndSidePart,sides,shortCurly"
            "&hairColor=2c1b18,4a312c,724133,090806"
            "&facialHairProbability=22&facialHair=beardLight,moustacheFancy&facialHairColor=2c1b18,4a312c,090806"
            "&accessories=prescription01,prescription02,round&accessoriesProbability=45&accessoriesColor=262e33,3c4f5c"
            "&eyes=default,happy&eyebrows=default,defaultNatural,raisedExcited&mouth=smile,default")

OG_DEFAULT = "https://optimityfx.com/assets/og-image.jpg"

def page(slug, title, desc, keywords, active, body, jsonld="", og_image=None):
    img = og_image if og_image else OG_DEFAULT
    html = HEAD.format(title=title, desc=desc, keywords=keywords, slug=slug, jsonld=jsonld, og_image=img)
    html += nav(active) + "<main>\n" + body + "\n</main>\n" + FOOTER
    with open(slug, "w") as f:
        f.write(html)
    print("wrote", slug)

# ===================== PAGES =====================
PAGES = {}

# Placeholder embed used for video tiles until real per-project URLs are added.
DEMO_VIDEO = "https://www.youtube.com/embed/ScMzIvxBSi4"

# ---------- PORTFOLIO ----------
def tile(kw, cat, name, cls="", play=False, lock=0, video=None, img_path=None):
    src = img_path if img_path else IMG(kw, 800, 600, lock=lock)
    if play:
        overlay = '<div class="play"><span><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span></div>'
        data = f' data-video="{video or DEMO_VIDEO}"'
    else:
        overlay = ''
        data = f' data-full="{img_path if img_path else IMG(kw, 1400, 1000, lock=lock)}"'
    img = f'<img src="{src}" alt="{name}" loading="lazy">'
    return (f'<div class="tile {cls}" data-cat="{cat.lower()}"{data}>'
            f'{img}<div class="tile-grad"></div>{overlay}'
            f'<div class="tile-meta"><span class="cat">{cat}</span><h4>{name}</h4></div></div>')

work = [
 ("concert,stage","Music Video","Neon Nights — T-Series","wide",True,101,None,None),
 ("coastline,cinematic","Color Grade","Coastline Doc","",False,102,None,"assets/portfolio/coastline-doc.webp"),
 ("car,product","AI Commercial","Tata Product Film","",True,103,None,None),
 ("skincare,cosmetics","UGC","D2C Skincare","",False,104,None,"assets/portfolio/d2c-skincare.webp"),
 ("festival,poster","Graphic Design","Festival Key Art","",False,105,None,"assets/portfolio/festival-key-art.webp"),
 ("rain,concert","Music Video","Monsoon — Zee Music","",True,106,None,None),
 ("wedding,cinematic","Color Grade","Wedding Film","wide",False,107,None,"assets/portfolio/wedding-film.webp"),
 ("neon,abstract","AI Music Video","Synthwave Dreams","",True,108,None,"assets/portfolio/synthwave-dreams.webp"),
 ("album,vinyl","Graphic Design","Album Cover Series","",False,109,None,"assets/portfolio/album-cover-series.webp"),
 ("fitness,gym","UGC","Fitness App Ads","",False,110,None,"assets/portfolio/fitness-app-ads.webp"),
 ("sneakers,shoes","AI Commercial","Sneaker Drop","",True,111,None,"assets/portfolio/sneaker-drop.webp"),
 ("travel,landscape","Color Grade","Travel Series","",False,112,None,"assets/portfolio/travel-series.webp"),
]
tiles = "\n".join(tile(*w) for w in work)
PAGES["portfolio.html"] = dict(
 title="Portfolio — Our Work | OptimityFX Creative Studio",
 desc="Browse 2,000+ projects: music videos, color grading, AI commercials, UGC and design for T-Series, Zee Music, Tata and brands across 10+ countries.",
 keywords="video editing portfolio, color grading showreel, creative studio work, music video editing, AI commercial",
 active="portfolio.html",
 og_image="https://optimityfx.com/assets/portfolio/synthwave-dreams.webp",
 jsonld='<script type="application/ld+json">{"@context":"https://schema.org","@type":"CollectionPage","name":"OptimityFX Portfolio","url":"https://optimityfx.com/portfolio.html"}</script>',
 body=f"""
<section class="page-hero">
  <div class="wrap">
    <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span>Work</div>
    <h1 class="reveal d1">Our <span class="spectrum-text">Work</span></h1>
    <p class="lead reveal d2">2,000+ projects delivered across 10+ countries. Filter by craft and explore the stories we've brought to life.</p>
  </div>
</section>

<section class="section section--tight" id="grading">
  <div class="wrap">
    <div class="sec-head reveal"><span class="eyebrow">Color Grading</span><h2 class="h-sec">Before / <span class="grad-text">After</span></h2><p class="lead">Drag the slider to see the transformation.</p></div>
    <div class="grid g-2">
      <div class="ba reveal">
        <img class="before" src="{IMG('portrait,cinematic',1200,700,lock=201)}" style="filter:saturate(.3) contrast(.85) brightness(.95)" alt="Before grade">
        <img class="after" src="{IMG('portrait,cinematic',1200,700,lock=201)}" style="filter:saturate(1.4) contrast(1.15) brightness(1.05)" alt="After grade">
        <span class="ba-label lbl-before">Before</span><span class="ba-label lbl-after">After</span>
        <div class="handle"><span class="knob"><svg viewBox="0 0 24 24"><path d="M8 7 3 12l5 5M16 7l5 5-5 5"/></svg></span></div>
        <input type="range" min="0" max="100" value="50" aria-label="Compare before and after">
      </div>
      <div class="ba reveal d1">
        <img class="before" src="{IMG('landscape,mountains',1200,700,lock=202)}" style="filter:saturate(.35) contrast(.9) sepia(.1)" alt="Before grade">
        <img class="after" src="{IMG('landscape,mountains',1200,700,lock=202)}" style="filter:saturate(1.3) contrast(1.12) hue-rotate(-8deg) brightness(1.05)" alt="After grade">
        <span class="ba-label lbl-before">Before</span><span class="ba-label lbl-after">After</span>
        <div class="handle"><span class="knob"><svg viewBox="0 0 24 24"><path d="M8 7 3 12l5 5M16 7l5 5-5 5"/></svg></span></div>
        <input type="range" min="0" max="100" value="50" aria-label="Compare before and after">
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="sec-head reveal"><span class="eyebrow">Gallery</span><h2 class="h-sec">Selected <span class="grad-text">Projects</span></h2></div>
    <div class="filters reveal">
      <button class="filter-btn active" data-filter="all">All Work</button>
      <button class="filter-btn" data-filter="music video">Music Videos</button>
      <button class="filter-btn" data-filter="color grade">Color Grading</button>
      <button class="filter-btn" data-filter="ai">AI &amp; Commercials</button>
      <button class="filter-btn" data-filter="ugc">UGC</button>
      <button class="filter-btn" data-filter="graphic design">Design</button>
    </div>
    <p class="note" style="margin-bottom:22px">Tip: click any image to open the gallery viewer · play icons mark video projects.</p>
    <div class="gallery reveal d1">
{tiles}
    </div>
  </div>
</section>

<!-- lightbox gallery viewer (images + video) -->
<div class="lightbox" aria-hidden="true">
  <button class="lb-close" aria-label="Close">&times;</button>
  <button class="lb-nav lb-prev" aria-label="Previous">&#8249;</button>
  <div class="lb-frame"></div>
  <button class="lb-nav lb-next" aria-label="Next">&#8250;</button>
</div>

<section class="section section--tight"><div class="wrap"><div class="cta-band center reveal"><h2>Like What You See?</h2><p style="margin-inline:auto">Let's create your next standout project together.</p><a href="contact.html" class="btn btn-accent btn-lg">Start a Project {ARR}</a></div></div></section>
""")

# ---------- ABOUT + TEAM ----------
_LI = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5A2.5 2.5 0 1 1 0 3.5a2.5 2.5 0 0 1 4.98 0zM.5 8h4V24h-4zM8 8h3.8v2.2h.06c.53-1 1.83-2.2 3.77-2.2 4.03 0 4.77 2.65 4.77 6.1V24h-4v-7.1c0-1.7-.03-3.9-2.37-3.9-2.38 0-2.74 1.85-2.74 3.77V24H8z"/></svg>'
_IG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>'
def member(name, role, bio, cert=None, li=None):
    cert_html = ''
    if cert:
        cert_html = (f'<div class="cert"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                     f'<path d="M12 2 4 6v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6z"/><path d="m9 12 2 2 4-4"/></svg> {cert}</div>')
    slug = name.split()[0].lower()
    # try the real photo first; if the file isn't there yet, fall back to the avatar
    photo = (f'<img src="assets/team/{slug}.jpg" alt="{name} — {role}" loading="lazy" '
             f'onerror="this.onerror=null;this.src=\'{AVATAR(name)}\'">')
    # always show the LinkedIn icon; if no URL yet, leave it as a placeholder (#)
    href = li if li else "#"
    tgt = ' target="_blank" rel="noopener"' if li else ''
    socials = f'<div class="socials"><a href="{href}"{tgt} aria-label="{name} on LinkedIn">{_LI}</a></div>'
    return f"""<div class="member reveal">
      <div class="photo">{photo}</div>
      <h4>{name}</h4><div class="role">{role}</div><p class="bio">{bio}</p>
      {cert_html}
      {socials}
    </div>"""
def open_role(role):
    return f"""<div class="member open reveal">
      <div class="photo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg></div>
      <h4>Onboarding&hellip;</h4><div class="role">{role}</div><p class="bio">This seat is opening up &mdash; talented people welcome.</p>
      <a href="contact.html" class="hiring"><span class="dot"></span> We're hiring</a>
    </div>"""
team = [
 member("Sayantan Adhikary","Founder","Sets the creative vision and signs off on every final grade.","Blackmagic Design Certified Colorist", li="https://www.linkedin.com/in/searchmydetails/"),
 member("Sagnik Adhikary","Co-Founder &middot; Investor","Backs the studio's growth and long-term vision.", li="https://www.linkedin.com/in/sagnik-adhikary-232258246/"),
 member("Ashish Kumar Jain","Co-Founder &middot; Social Media & Business Expansion","Drives social media, brand reach and business partnerships.", li="https://www.linkedin.com/in/c2ashish/"),
 member("Praloy Maity","Marketing, Data & Business Mgmt","Turns data into smart marketing and growth decisions.", li="https://www.linkedin.com/in/praloy-corporate/"),
 member("Bikram Saha","Marketing, Data & Business Mgmt","Drives campaigns, analytics and day-to-day operations.", li="https://www.linkedin.com/in/bikccu/"),
 member("Biswajit Sena","Sr. Creative Media Designer","Crafts the visuals, key art and brand-defining design."),
 open_role("AI Integrator, Automation Expert"),
 open_role("Open Role"),
 open_role("Open Role"),
]
team_html = "\n".join(team)
PAGES["about.html"] = dict(
 title="About OptimityFX — Our Story & Team | Creative Studio",
 desc="Meet OptimityFX — a global creative studio of editors, colorists and AI artists. 2,000+ projects, 10+ countries, clients including T-Series, Zee Music & Tata.",
 keywords="about OptimityFX, creative studio team, colorist, video editor, our story",
 active="about.html",
 og_image="https://optimityfx.com/assets/story.jpg",
 jsonld='<script type="application/ld+json">{"@context":"https://schema.org","@type":"AboutPage","name":"About OptimityFX","url":"https://optimityfx.com/about.html"}</script>',
 body=f"""
<section class="page-hero">
  <div class="wrap">
    <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span>About</div>
    <h1 class="reveal d1">We Turn Vision<br>Into <span class="spectrum-text">Visuals</span></h1>
    <p class="lead reveal d2">OptimityFX began with a simple belief: world-class creative shouldn't be reserved for the few. Today we're a global studio helping brands and creators look extraordinary.</p>
  </div>
</section>

<section class="section--tight"><div class="wrap"><div class="stats reveal">
  <div class="stat"><b class="spectrum-text" data-count="2000" data-suffix="+">0</b><span>PROJECTS DELIVERED</span></div>
  <div class="stat"><b class="spectrum-text" data-count="10" data-suffix="+">0</b><span>COUNTRIES</span></div>
  <div class="stat"><b class="spectrum-text" data-count="150" data-suffix="+">0</b><span>BRANDS & CREATORS</span></div>
  <div class="stat"><b class="spectrum-text" data-count="8" data-suffix=" yrs">0</b><span>OF CRAFT</span></div>
</div></div></section>

<section class="section"><div class="wrap split">
  <div class="reveal"><img src="assets/story.jpg" alt="OptimityFX studio setup" loading="lazy" onerror="this.onerror=null;this.src='{IMG('filmmaker,camera,cinema',800,640,lock=312)}'" style="width:100%;aspect-ratio:3/2;object-fit:cover;object-position:center;border-radius:18px;border:1px solid var(--line)"></div>
  <div class="reveal d1">
    <span class="eyebrow">Our Story</span>
    <h2 class="h-sec" style="margin:14px 0">Craft Meets <span class="grad-text">Technology</span></h2>
    <p class="lead">From a one-person edit suite to a full-stack creative studio, we've always chased one thing — work that makes people stop, feel and remember. We pair traditional craftsmanship with cutting-edge AI to deliver premium results at startup speed.</p>
    <ul class="check-list">
      <li>{CHK} Senior specialists for every discipline</li>
      <li>{CHK} Transparent process & on-time delivery</li>
      <li>{CHK} Trusted by labels, enterprises & creators alike</li>
    </ul>
  </div>
</div></section>

<section class="section" style="background:var(--bg-2)"><div class="wrap">
  <div class="sec-head center reveal"><span class="eyebrow center-eb">Values</span><h2 class="h-sec">What Drives <span class="grad-text">Us</span></h2></div>
  <div class="grid g-3">
    <div class="card reveal"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m12 2 2.4 7.4H22l-6 4.6 2.3 7.4L12 17l-6.3 4.4L8 14 2 9.4h7.6z"/></svg></div><h3>Craft First</h3><p>Every frame, cut and color is intentional. We sweat the details others skip.</p></div>
    <div class="card reveal d1"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg></div><h3>Speed & Reliability</h3><p>Premium quality, delivered on time — with an avg. 48-hour turnaround.</p></div>
    <div class="card reveal d2"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/></svg></div><h3>True Partnership</h3><p>We think like an extension of your team, invested in your growth.</p></div>
  </div>
</div></section>

<section class="section" id="team"><div class="wrap">
  <div class="sec-head center reveal"><span class="eyebrow center-eb">The People</span><h2 class="h-sec">Meet The <span class="grad-text">Team</span></h2><p class="lead" style="margin-inline:auto">The founders and specialists behind OptimityFX — and a few seats we're still filling.</p></div>
  <div class="grid g-3 team-grid">
{team_html}
  </div>
</div></section>

<section class="section section--tight"><div class="wrap"><div class="cta-band center reveal"><h2>Want To Work With Us?</h2><p style="margin-inline:auto">We're always excited to meet ambitious brands and creators.</p><a href="contact.html" class="btn btn-accent btn-lg">Get In Touch {ARR}</a></div></div></section>
""")

# ---------- ACADEMY ----------
def course(kw, level, title, meta, price, lock, img=None):
    src = img if img else IMG(kw, 640, 360, lock=lock)
    return f"""<article class="course reveal">
      <div class="ctop"><img src="{src}" alt="{title}" loading="lazy"><span class="clevel">{level}</span></div>
      <div class="cbody"><h4>{title}</h4>
        <div class="cmeta">{meta}</div>
        <div class="cfoot"><span class="cprice">{price}</span><a href="contact.html" class="btn btn-accent btn-sm">Enroll</a></div>
      </div></article>"""
courses = [
 ("video,editing","Beginner","NextGen Video Editing",'<span>⏱ 24 lessons</span><span>● Live + Recorded</span>',"₹4,999",401,"assets/academy/video-editing.webp"),
 ("color,cinema","Advanced","NextGen Color Grading",'<span>⏱ 18 lessons</span><span>● DaVinci Resolve</span>',"₹6,999",402,"assets/academy/color-grading.webp"),
 ("audio,studio","Intermediate","NextGen Mix &amp; Master",'<span>⏱ 20 lessons</span><span>● Hands-on</span>',"₹5,499",403,"assets/academy/mix-master.webp"),
 ("microphone,singing","Beginner","NextGen Singing",'<span>⏱ 16 lessons</span><span>● Live coaching</span>',"₹3,999",404,"assets/academy/singing.webp"),
 ("drums,music","Beginner","NextGen Drums",'<span>⏱ 22 lessons</span><span>● Live + Recorded</span>',"₹4,499",405,"assets/academy/drums.webp"),
 ("technology,computer","Advanced","NextGen AI Tools",'<span>⏱ 14 lessons</span><span>● Latest workflows</span>',"₹5,999",406,"assets/academy/ai-tools.webp"),
 ("office,computer,desk","Intermediate","NextGen Pro Workflow",'<span>⏱ 12 lessons</span><span>● Pro pipeline</span>',"₹4,999",410,"assets/academy/pro-workflow.webp"),
 ("speaker,podium,audience","Beginner","NextGen Attitude &amp; Confidence",'<span>⏱ 12 sessions</span><span>● Live coaching</span>',"₹4,499",408,"assets/academy/confidence.webp"),
 ("piano,studio","Advanced","NextGen Music Production",'<span>⏱ 26 lessons</span><span>● Live + Recorded</span>',"₹7,499",409,"assets/academy/music-production.webp"),
]
courses_html = "\n".join(course(*c) for c in courses)
PAGES["academy.html"] = dict(
 title="NextGen Academy — Live & Recorded Creative Courses | OptimityFX",
 desc="Upskill with NextGen Academy: online live & recorded courses in video editing, color grading, mixing & mastering, singing, drums, AI tools and pro workflows.",
 keywords="color grading course, video editing course, music mixing course, AI tools course, online creative classes, NextGen Academy",
 active="academy.html",
 og_image="https://optimityfx.com/assets/academy/video-editing.webp",
 jsonld='<script type="application/ld+json">{"@context":"https://schema.org","@type":"EducationalOrganization","name":"OptimityFX NextGen Academy","url":"https://optimityfx.com/academy.html","description":"Live and recorded creative courses."}</script>',
 body=f"""
<section class="page-hero">
  <div class="wrap">
    <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span>Academy</div>
    <span class="tag-pill reveal">NextGen Academy</span>
    <h1 class="reveal d1" style="margin-top:14px">Skill Up. <span class="spectrum-text">Level Up.</span></h1>
    <p class="lead reveal d2">Learn directly from working professionals. Live and recorded courses across editing, color, music, AI and the workflows the industry actually uses.</p>
    <div class="hero-actions reveal d3" style="margin-top:28px"><a href="#courses" class="btn btn-accent btn-lg">Browse Courses {ARR}</a><a href="contact.html" class="btn btn-ghost btn-lg">Request a Syllabus</a></div>
  </div>
</section>

<section class="section--tight"><div class="wrap"><div class="trust-row reveal">
  <span class="trust-badge">{CHK} Live + Recorded Access</span>
  <span class="trust-badge">{CHK} Certificate on Completion</span>
  <span class="trust-badge">{CHK} Real Project Assignments</span>
  <span class="trust-badge">{CHK} Lifetime Community Access</span>
</div></div></section>

<section class="section" id="courses"><div class="wrap">
  <div class="sec-head reveal"><span class="eyebrow">Curriculum</span><h2 class="h-sec">Explore Our <span class="grad-text">Courses</span></h2><p class="lead">From your first edit to a pro pipeline — there's a track for every goal.</p></div>
  <div class="grid g-3">
{courses_html}
  </div>
</div></section>

<section class="section" style="background:var(--bg-2)"><div class="wrap">
  <div class="sec-head center reveal"><span class="eyebrow center-eb">Why Learn With Us</span><h2 class="h-sec">Built For <span class="grad-text">Real Results</span></h2></div>
  <div class="grid g-4">
    <div class="card reveal"><div class="ic">🎬</div><h3>Learn By Doing</h3><p>Every module ends with a hands-on, portfolio-ready project.</p></div>
    <div class="card reveal d1"><div class="ic">🧑‍🏫</div><h3>Industry Mentors</h3><p>Taught by pros who work on real client projects daily.</p></div>
    <div class="card reveal d2"><div class="ic">💬</div><h3>Live Doubt-Solving</h3><p>Weekly live sessions to get unstuck and go deeper.</p></div>
    <div class="card reveal d3"><div class="ic">🏆</div><h3>Career Support</h3><p>Portfolio reviews & guidance to land work or clients.</p></div>
  </div>
</div></section>

<section class="section"><div class="wrap"><div class="cta-band center reveal"><h2>Not Sure Where To Start?</h2><p style="margin-inline:auto">Book a free counseling call and we'll map the right learning path for you.</p><a href="contact.html" class="btn btn-accent btn-lg">Talk to an Advisor {ARR}</a></div></div></section>
""")

# ---------- STORE ----------
def product(kw, tag, name, meta, price, old=None, lock=0, rating="★★★★★", img=None):
    old_html = f'<del>{old}</del>' if old else ''
    src = img if img else IMG(kw, 600, 450, lock=lock)
    return f"""<article class="product reveal" data-cat="{tag.lower()}">
      <div class="thumb"><img src="{src}" alt="{name}" loading="lazy"><span class="ptag">{tag}</span></div>
      <div class="pbody"><h4>{name}</h4><div class="pmeta">{meta}</div>
        <div class="pfoot"><span class="pprice">{price} {old_html}</span><span class="prating">{rating}</span></div>
        <a href="contact.html" class="btn btn-accent btn-sm" style="width:100%;justify-content:center;margin-top:14px">Buy Now</a>
      </div></article>"""
products = [
 ("cinematic,landscape","LUTs","Cinematic LUT Pack Vol.1","30 LUTs · .cube","₹1,499","₹2,999",501,"★★★★★","assets/store/lut-cinematic.webp"),
 ("moody,portrait","Presets","Moody Film Presets","20 presets · Lightroom","₹999","₹1,799",502,"★★★★★","assets/store/presets-moody.webp"),
 ("video,smartphone","Templates","Reels Transition Pack","50 transitions · Premiere","₹1,299",None,503,"★★★★★","assets/store/reels-transitions.webp"),
 ("color,monitor","Course","Color Grading Bootcamp","8 hrs · Lifetime","₹3,999","₹5,999",504,"★★★★★","assets/store/color-bootcamp.webp"),
 ("sunset,city","LUTs","Teal & Orange Master LUTs","15 LUTs · .cube","₹1,199",None,505,"★★★★★","assets/store/lut-teal-orange.webp"),
 ("screen,desk","Templates","YouTube Thumbnail Kit","100 PSD templates","₹899","₹1,499",506,"★★★★★","assets/store/thumbnail-kit.webp"),
 ("portrait,face","Presets","Skin Tone Pro Presets","12 presets · Resolve","₹1,099",None,507,"★★★★★","assets/store/skin-tone-presets.webp"),
 ("neon,concert","Course","AI Music Video Blueprint","6 hrs · Lifetime","₹2,999","₹4,499",508,"★★★★★","assets/store/ai-music-blueprint.webp"),
]
products_html = "\n".join(product(*p) for p in products)
PAGES["store.html"] = dict(
 title="Digital Store — LUTs, Presets, Templates & Courses | OptimityFX",
 desc="Download pro-grade LUTs, color presets, editing templates and self-paced courses — the exact tools used by OptimityFX. Instant download, lifetime access.",
 keywords="buy LUTs, color grading presets, premiere templates, lightroom presets, editing course download",
 active="store.html",
 og_image="https://optimityfx.com/assets/store/lut-cinematic.webp",
 jsonld='<script type="application/ld+json">{"@context":"https://schema.org","@type":"Store","name":"OptimityFX Digital Store","url":"https://optimityfx.com/store.html"}</script>',
 body=f"""
<section class="page-hero">
  <div class="wrap">
    <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span>Store</div>
    <h1 class="reveal d1">Digital <span class="spectrum-text">Store</span></h1>
    <p class="lead reveal d2">The exact LUTs, presets, templates and courses we use on client work — ready to download and drop into your projects.</p>
  </div>
</section>

<section class="section--tight"><div class="wrap"><div class="trust-row reveal">
  <span class="trust-badge">{CHK} Instant Download</span>
  <span class="trust-badge">{CHK} Lifetime Updates</span>
  <span class="trust-badge">{CHK} Secure Checkout</span>
  <span class="trust-badge">{CHK} Works in Premiere, Resolve & Lightroom</span>
</div></div></section>

<section class="section"><div class="wrap">
  <div class="filters reveal">
    <button class="filter-btn active" data-filter="all">All Products</button>
    <button class="filter-btn" data-filter="luts">LUTs</button>
    <button class="filter-btn" data-filter="presets">Presets</button>
    <button class="filter-btn" data-filter="templates">Templates</button>
    <button class="filter-btn" data-filter="course">Courses</button>
  </div>
  <div class="grid g-4">
{products_html}
  </div>
  <p class="note center" style="margin-top:30px">Note: filter tags map to product categories. Connect your payment gateway (Razorpay, Stripe, Gumroad) to enable live checkout.</p>
</div></section>

<section class="section section--tight"><div class="wrap"><div class="cta-band center reveal"><h2>Want A Custom LUT Pack?</h2><p style="margin-inline:auto">We build bespoke color tools tailored to your camera & brand.</p><a href="contact.html" class="btn btn-accent btn-lg">Request Custom Tools {ARR}</a></div></div></section>
""")

# ---------- COACHING ----------
PAGES["b2b.html"] = dict(
 title="B2B Solutions for Brands & Businesses | OptimityFX",
 desc="Strategic B2B partnerships for brands and businesses — growth strategy, positioning, content systems and scale planning from a team that's built a studio from zero.",
 keywords="B2B solutions, brand strategy, business growth partnerships, content systems for brands",
 active="b2b.html",
 og_image="https://optimityfx.com/assets/services/commercial.webp",
 jsonld='<script type="application/ld+json">{"@context":"https://schema.org","@type":"Service","serviceType":"B2B Solutions","provider":{"@type":"Organization","name":"OptimityFX"}}</script>',
 body=f"""
<section class="page-hero">
  <div class="wrap">
    <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span>B2B</div>
    <span class="tag-pill reveal">B2B Solutions</span>
    <h1 class="reveal d1" style="margin-top:14px">Grow Your Business,<br><span class="spectrum-text">On Purpose.</span></h1>
    <p class="lead reveal d2">We've built a creative studio from zero. Now we partner with businesses and brands to craft the strategy to grow — and the systems to scale.</p>
    <div class="hero-actions reveal d3" style="margin-top:28px"><a href="contact.html" class="btn btn-accent btn-lg">Book a Strategy Call {ARR}</a></div>
  </div>
</section>

<section class="section"><div class="wrap">
  <div class="sec-head center reveal"><span class="eyebrow center-eb">What You Get</span><h2 class="h-sec">B2B Solutions That <span class="grad-text">Move The Needle</span></h2></div>
  <div class="grid g-3">
    <div class="card reveal"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 3v18h18"/><path d="m7 14 3-3 3 3 5-5"/></svg></div><h3>Growth Strategy</h3><p>A clear roadmap to grow revenue, audience and impact — built around your strengths.</p></div>
    <div class="card reveal d1"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="m9 12 2 2 4-4"/></svg></div><h3>Brand Positioning</h3><p>Stand out in a crowded market with messaging and a niche that's unmistakably you.</p></div>
    <div class="card reveal d2"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div><h3>Pricing & Offers</h3><p>Package and price your work so you earn what you're worth — without guesswork.</p></div>
    <div class="card reveal"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M8 4v16"/></svg></div><h3>Content Systems</h3><p>Repeatable workflows & calendars so output stays consistent as you scale.</p></div>
    <div class="card reveal d1"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg></div><h3>Client Acquisition</h3><p>Find, pitch and close better clients with a sales process that fits creatives.</p></div>
    <div class="card reveal d2"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m12 2 2.4 7.4H22l-6 4.6 2.3 7.4L12 17l-6.3 4.4L8 14 2 9.4h7.6z"/></svg></div><h3>Accountability</h3><p>Regular check-ins to keep you focused, unblocked and shipping.</p></div>
  </div>
</div></section>

<section class="section" style="background:var(--bg-2)"><div class="wrap">
  <div class="sec-head center reveal"><span class="eyebrow center-eb">How It Works</span><h2 class="h-sec">Your Path To <span class="grad-text">Growth</span></h2></div>
  <div class="grid g-4">
    <div class="card reveal"><div class="ic">01</div><h3>Audit</h3><p>We assess where you are and where the biggest opportunities sit.</p></div>
    <div class="card reveal d1"><div class="ic">02</div><h3>Plan</h3><p>A custom 90-day strategy with clear priorities and milestones.</p></div>
    <div class="card reveal d2"><div class="ic">03</div><h3>Execute</h3><p>Bi-weekly strategy sessions to implement, adjust and stay on track.</p></div>
    <div class="card reveal d3"><div class="ic">04</div><h3>Scale</h3><p>Systemize what works so growth compounds without burnout.</p></div>
  </div>
</div></section>

<section class="section"><div class="wrap">
  <div class="sec-head center reveal"><span class="eyebrow center-eb">Plans</span><h2 class="h-sec">Choose Your <span class="grad-text">Engagement</span></h2></div>
  <div class="grid g-3">
    <div class="price-card reveal"><h3>Power Hour</h3><p class="note">One focused session</p><div class="price">₹4,999<small>/ session</small></div>
      <ul><li>{CHK} 60-min 1:1 strategy call</li><li>{CHK} Recording + action notes</li><li>{CHK} 7-day follow-up support</li></ul>
      <a href="contact.html" class="btn btn-ghost">Book Now</a></div>
    <div class="price-card featured reveal d1"><span class="tag">Best Value</span><h3>Growth Program</h3><p class="note">90-day transformation</p><div class="price">₹24,999<small>/ quarter</small></div>
      <ul><li>{CHK} 6 bi-weekly sessions</li><li>{CHK} Custom growth roadmap</li><li>{CHK} WhatsApp/email support</li><li>{CHK} Templates & frameworks</li></ul>
      <a href="contact.html" class="btn btn-accent">Apply Now</a></div>
    <div class="price-card reveal d2"><h3>Brand Partner</h3><p class="note">Hands-on, done-with-you</p><div class="price">Custom<small>/ retainer</small></div>
      <ul><li>{CHK} Weekly sessions</li><li>{CHK} Strategy + execution support</li><li>{CHK} Team workshops</li></ul>
      <a href="contact.html" class="btn btn-ghost">Enquire</a></div>
  </div>
</div></section>

<section class="section section--tight"><div class="wrap"><div class="cta-band center reveal"><h2>Ready To Grow?</h2><p style="margin-inline:auto">Book a free 20-minute discovery call — no pitch, just clarity.</p><a href="contact.html" class="btn btn-accent btn-lg">Book Free Call {ARR}</a></div></div></section>
""")

# ---------- BLOG ----------
# Posts are authored as Markdown files in content/blog/*.md (frontmatter + body).
# Set `status: draft` to keep a post out of the build until approved (1-click publish).
BLOG_DIR = "content/blog"

def _md_inline(t):
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" style="color:var(--accent)">\1</a>', t)
    return t

def md_to_html(md):
    out = []
    for block in re.split(r'\n\s*\n', md.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith('### '):
            out.append(f"<h3>{_md_inline(block[4:].strip())}</h3>")
        elif block.startswith('## '):
            out.append(f"<h2>{_md_inline(block[3:].strip())}</h2>")
        elif block.startswith('> '):
            quote = " ".join(l[2:].strip() for l in block.splitlines())
            out.append(f"<blockquote>{_md_inline(quote)}</blockquote>")
        elif all(l.strip().startswith('- ') for l in block.splitlines()):
            lis = "".join(f"<li>{_md_inline(l.strip()[2:])}</li>" for l in block.splitlines())
            out.append(f'<ul class="dot">{lis}</ul>')
        else:
            out.append(f"<p>{_md_inline(block)}</p>")
    return "\n  ".join(out)

def parse_post(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', raw, re.S)
    fm, body = (m.group(1), m.group(2)) if m else ("", raw)
    meta = {}
    for line in fm.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    meta['body'] = body
    return meta

def load_posts():
    items = []
    for p in sorted(glob.glob(f"{BLOG_DIR}/*.md")):
        if os.path.basename(p).upper().startswith("README"):
            continue
        meta = parse_post(p)
        if meta.get("status", "published").lower() != "published":
            continue
        items.append(meta)
    items.sort(key=lambda m: m.get("iso", ""), reverse=True)
    return items

def _post_hero(meta, w, h):
    img = meta.get("image", "").strip()
    if img:
        return img
    # use slug-derived lock so card + post page always resolve to the same image
    lock = abs(hash(meta.get("slug", "default"))) % 9999
    return IMG(meta.get("hero_kw", "cinema,film"), w, h, lock=lock)

def post_card(meta):
    url = f"blog-{meta['slug']}.html"
    return f"""<article class="post-card reveal" data-cat="{meta.get('filter','all')}">
      <a href="{url}" class="pimg"><img src="{_post_hero(meta,640,400)}" alt="{meta['title']}" loading="lazy"></a>
      <div class="pc-body"><span class="pc-cat">{meta.get('category','')}</span>
        <h3><a href="{url}">{meta['title']}</a></h3>
        <p class="pc-ex">{meta.get('excerpt','')}</p>
        <div class="pc-meta"><span>{meta.get('date','')}</span><span>·</span><span>{meta.get('read','5 min')} read</span></div>
      </div></article>"""

POSTS = load_posts()
posts_html = "\n".join(post_card(m) for m in POSTS)
PAGES["blog.html"] = dict(
 title="Blog — Color Grading, Editing & Creator Business Tips | OptimityFX",
 desc="Tutorials, breakdowns and strategy from the OptimityFX studio: color grading, video editing, AI tools, UGC and growing your creative business.",
 keywords="color grading tutorial, video editing tips, AI video, UGC tips, creative business blog",
 active="blog.html",
 og_image="https://optimityfx.com/assets/blog/veo3-ai-audio-video-music-production.webp",
 jsonld='<script type="application/ld+json">{"@context":"https://schema.org","@type":"Blog","name":"OptimityFX Blog","url":"https://optimityfx.com/blog.html"}</script>',
 body=f"""
<section class="page-hero">
  <div class="wrap">
    <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span>Blog</div>
    <h1 class="reveal d1">The <span class="spectrum-text">Journal</span></h1>
    <p class="lead reveal d2">Tutorials, behind-the-scenes breakdowns and hard-won lessons on craft and the creative business.</p>
  </div>
</section>
<section class="section"><div class="wrap">
  <div class="filters reveal">
    <button class="filter-btn active" data-filter="all">All</button>
    <button class="filter-btn" data-filter="color">Color</button>
    <button class="filter-btn" data-filter="edit">Editing</button>
    <button class="filter-btn" data-filter="ai">AI</button>
    <button class="filter-btn" data-filter="business">Business</button>
  </div>
  <div class="grid g-3">
{posts_html}
  </div>
</div></section>
<section class="section section--tight"><div class="wrap"><div class="cta-band center reveal"><h2>Get Our Best Tips In Your Inbox</h2><p style="margin-inline:auto">Join 12,000+ creators. One useful email a week. No spam.</p>
  <form data-fake class="hero-actions" style="justify-content:center;max-width:460px;margin-inline:auto">
    <input type="email" required placeholder="you@email.com" aria-label="Email" style="flex:1;padding:14px 18px;background:var(--bg-2);border:1px solid var(--line);border-radius:100px;color:var(--text)">
    <button type="submit" class="btn btn-accent">Subscribe</button>
  </form></div></div></section>
""")

# ---------- BLOG POSTS (one unique URL per post, generated from content/blog/*.md) ----------
def post_page(meta):
    cat = meta.get("category", "")
    crumb = meta.get("crumb", cat or "Article")
    hero = _post_hero(meta, 1200, 620)
    iso = meta.get("iso", "")
    cta_h = meta.get("cta_h", "Want Us To Elevate Your Next Project?")
    cta_p = meta.get("cta_p", "Send us your footage and get a free grading or editing test.")
    jsonld = (
        '<script type="application/ld+json">{"@context":"https://schema.org",'
        '"@type":"BlogPosting","headline":"' + meta["title"].replace('"', "'") + '",'
        '"author":{"@type":"Organization","name":"OptimityFX"},'
        '"datePublished":"' + iso + '","dateModified":"' + iso + '",'
        '"image":"' + (hero if hero.startswith("http") else "https://optimityfx.com/" + hero) + '",'
        '"description":"' + meta.get("meta_desc", meta.get("excerpt", "")).replace('"', "'") + '",'
        '"mainEntityOfPage":"https://optimityfx.com/blog-' + meta["slug"] + '.html",'
        '"publisher":{"@type":"Organization","name":"OptimityFX","logo":{"@type":"ImageObject","url":"https://optimityfx.com/assets/logo-mark.svg"}}}</script>'
    )
    body = f"""
<section class="page-hero" style="padding-bottom:30px">
  <div class="wrap" style="max-width:780px">
    <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span><a href="blog.html">Blog</a><span>/</span>{crumb}</div>
    <span class="pc-cat reveal" style="color:var(--accent);font-weight:600;letter-spacing:2px;text-transform:uppercase;font-size:.72rem">{cat}</span>
    <h1 class="reveal d1" style="font-size:clamp(2.2rem,5vw,3.4rem);margin:14px 0">{meta['title']}</h1>
    <div class="pc-meta reveal d2" style="display:flex;gap:14px;color:var(--dim);font-size:.85rem"><span>By OptimityFX</span><span>·</span><span>{meta.get('date','')}</span><span>·</span><span>{meta.get('read','5 min')} read</span></div>
  </div>
</section>
<section class="section" style="padding-top:30px"><div class="wrap"><div class="article reveal">
  <img src="{hero}" alt="{meta['title']}">
  {md_to_html(meta['body'])}
</div></div></section>
<section class="section section--tight"><div class="wrap"><div class="cta-band center reveal"><h2>{cta_h}</h2><p style="margin-inline:auto">{cta_p}</p><a href="contact.html" class="btn btn-accent btn-lg">Start a Project {ARR}</a></div></div></section>
"""
    og_img = hero if hero.startswith("http") else "https://optimityfx.com/" + hero
    return dict(
        title=f"{meta['title']} | OptimityFX Blog",
        desc=meta.get("meta_desc", meta.get("excerpt", "")),
        keywords=meta.get("keywords", ""),
        active="blog.html",
        jsonld=jsonld,
        body=body,
        og_image=og_img,
    )

for _m in POSTS:
    PAGES[f"blog-{_m['slug']}.html"] = post_page(_m)

# Backward-compat: old single blog-post.html now redirects to the blog index.
PAGES["blog-post.html"] = dict(
    title="OptimityFX Blog", desc="OptimityFX Journal", keywords="", active="blog.html",
    jsonld='<meta http-equiv="refresh" content="0; url=blog.html"><link rel="canonical" href="https://optimityfx.com/blog.html">',
    body='<section class="section"><div class="wrap"><p>Redirecting to the <a href="blog.html" style="color:var(--accent)">OptimityFX Journal</a>…</p></div></section>')

# ---------- CONTACT ----------
PAGES["contact.html"] = dict(
 title="Contact OptimityFX — Start Your Project | Free Consultation",
 desc="Get in touch with OptimityFX for video editing, color grading, AI production or B2B solutions. Free consultation and a tailored quote within 24 hours.",
 keywords="contact OptimityFX, hire creative studio, video editing quote, color grading enquiry",
 active="contact.html",
 og_image="https://optimityfx.com/assets/services/grading.webp",
 jsonld='<script type="application/ld+json">{"@context":"https://schema.org","@type":"ContactPage","name":"Contact OptimityFX","url":"https://optimityfx.com/contact.html"}</script>',
 body=f"""
<section class="page-hero">
  <div class="wrap">
    <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span>Contact</div>
    <h1 class="reveal d1">Let's Create <span class="spectrum-text">Together</span></h1>
    <p class="lead reveal d2">Tell us about your project. We reply within 24 hours with ideas and a tailored quote.</p>
  </div>
</section>
<section class="section" style="padding-top:20px"><div class="wrap split" style="align-items:start">
  <div class="reveal">
    <div class="card">
      <h3 style="margin-bottom:20px">Start a Project</h3>
      <form data-fake>
        <div class="form-row">
          <div class="field"><label>Name</label><input type="text" required placeholder="Your name"></div>
          <div class="field"><label>Email</label><input type="email" required placeholder="you@email.com"></div>
        </div>
        <div class="form-row">
          <div class="field"><label>Service</label><select><option>Video Editing</option><option>Color Grading</option><option>Graphic Design</option><option>AI Music Video</option><option>UGC / AI UGC</option><option>AI Product Commercial</option><option>Academy</option><option>B2B Solutions</option></select></div>
          <div class="field"><label>Budget</label><select><option>Under ₹25k</option><option>₹25k – ₹1L</option><option>₹1L – ₹5L</option><option>₹5L+</option></select></div>
        </div>
        <div class="field"><label>Project Details</label><textarea required placeholder="Tell us about your vision, timeline and references…"></textarea></div>
        <button type="submit" class="btn btn-accent btn-lg" style="width:100%;justify-content:center">Send Message {ARR}</button>
        <p class="note" style="margin-top:12px;text-align:center">By submitting you agree to our <a href="privacy.html" style="color:var(--muted)">Privacy Policy</a>.</p>
      </form>
    </div>
  </div>
  <div class="reveal d1">
    <div class="card" style="margin-bottom:22px"><h3 style="margin-bottom:8px">Reach Us Directly</h3>
      <p style="margin-bottom:18px">Prefer email or a quick call? We're here.</p>
      <ul class="check-list" style="margin-top:0">
        <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6 10-6"/></svg> <a href="mailto:optimityfx.studio@gmail.com" style="color:inherit">optimityfx.studio@gmail.com</a></li>
        <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.6A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.5 2.8.6a2 2 0 0 1 1.7 2z"/></svg> <a href="tel:+917001202156" style="color:inherit">+91 70012 02156</a></li>
        <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg> Remote-first · Serving 10+ countries</li>
      </ul>
    </div>
    <div class="card"><h3 style="margin-bottom:14px">Frequent Questions</h3>
      <div class="acc-item"><button class="acc-q">How fast can you deliver? <span class="pm"></span></button><div class="acc-a"><p>Most projects ship within 48–96 hours depending on scope. Rush options are available.</p></div></div>
      <div class="acc-item"><button class="acc-q">Do you work with international clients? <span class="pm"></span></button><div class="acc-a"><p>Absolutely — we're remote-first and already serve clients across 10+ countries.</p></div></div>
      <div class="acc-item"><button class="acc-q">How does pricing work? <span class="pm"></span></button><div class="acc-a"><p>We quote per project or via monthly retainers. Share your brief and we'll tailor a quote within 24 hours.</p></div></div>
    </div>
  </div>
</div></section>
""")

# ---------- APP ----------
PAGES["app.html"] = dict(
 title="OptimityFX Mobile App — Edit, Grade & Learn On The Go (iOS & Android)",
 desc="The OptimityFX app brings color grading presets, course access, project tracking and our store to your pocket. Coming soon to the App Store and Google Play.",
 keywords="OptimityFX app, color grading app, creative learning app, iOS, Android",
 active="",
 og_image="https://optimityfx.com/assets/services/ai-influencer.webp",
 jsonld='<script type="application/ld+json">{"@context":"https://schema.org","@type":"SoftwareApplication","name":"OptimityFX","operatingSystem":"iOS, Android","applicationCategory":"MultimediaApplication","offers":{"@type":"Offer","price":"0","priceCurrency":"INR"},"aggregateRating":{"@type":"AggregateRating","ratingValue":"4.9","ratingCount":"1280"}}</script>',
 body=f"""
<section class="page-hero">
  <div class="wrap split" style="align-items:center">
    <div>
      <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span>App</div>
      <span class="tag-pill reveal">Coming Soon · iOS &amp; Android</span>
      <h1 class="reveal d1" style="margin-top:14px">Your Studio,<br><span class="spectrum-text">In Your Pocket.</span></h1>
      <p class="lead reveal d2">Apply our signature presets, watch Academy lessons, track your projects and shop the store — all from one beautifully crafted app.</p>
      <div class="app-badges reveal d3" style="flex-direction:row;flex-wrap:wrap;margin-top:26px">
        <a href="#notify" class="app-badge"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M16.5 1.6c0 1.2-.5 2.3-1.3 3.1-.8.9-2.1 1.6-3.2 1.5-.1-1.2.5-2.4 1.2-3.1.8-.9 2.2-1.6 3.3-1.5zM20.8 17c-.6 1.4-.9 2-1.7 3.2-1.1 1.7-2.6 3.8-4.5 3.8-1.7 0-2.1-1.1-4.4-1.1s-2.8 1.1-4.4 1.1c-1.9 0-3.4-1.9-4.5-3.6C-1 16.1-1.4 9.7 2.3 7.4c1.3-.8 2.7-1 3.9-1 1.3 0 2.5 1 4.4 1 1.8 0 2.6-1 4.4-1 1.1 0 2.6.3 3.9 1.5-3.4 1.9-2.9 6.7.9 8.1z"/></svg><span><span class="ab-s">Download on the</span><span class="ab-b">App Store</span></span></a>
        <a href="#notify" class="app-badge"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M3.6 1.8 13.3 12 3.6 22.2c-.3-.2-.6-.6-.6-1.2V3c0-.6.3-1 .6-1.2zM14.7 13.4l2.6 2.7-9.4 5.4zM18.6 9.2c.9.5 1.4 1.2 1.4 2s-.5 1.5-1.4 2l-2.5 1.4-2.9-3 2.9-3zM8 2.3l9.3 5.3-2.6 2.7z"/></svg><span><span class="ab-s">Get it on</span><span class="ab-b">Google Play</span></span></a>
      </div>
      <p class="note reveal d4" style="margin-top:14px">★★★★★ 4.9 — from 1,280+ early testers</p>
    </div>
    <div class="reveal d1" style="display:grid;place-items:center">
      <img src="{IMG('smartphone,app,mobile',520,760,lock=630)}" alt="OptimityFX app preview" style="max-width:300px;border-radius:32px;border:8px solid #111;box-shadow:var(--shadow)">
    </div>
  </div>
</section>

<section class="section"><div class="wrap">
  <div class="sec-head center reveal"><span class="eyebrow center-eb">Features</span><h2 class="h-sec">Everything, <span class="grad-text">Everywhere</span></h2></div>
  <div class="grid g-4">
    <div class="card reveal"><div class="ic">🎨</div><h3>1-Tap Presets</h3><p>Apply our pro LUTs & presets to your clips instantly.</p></div>
    <div class="card reveal d1"><div class="ic">🎓</div><h3>Academy On-Demand</h3><p>Stream live & recorded lessons anywhere.</p></div>
    <div class="card reveal d2"><div class="ic">📦</div><h3>Project Tracking</h3><p>Approve previews & track delivery in real time.</p></div>
    <div class="card reveal d3"><div class="ic">🛍️</div><h3>Store Access</h3><p>Buy & download tools straight to your device.</p></div>
  </div>
</div></section>

<section class="section" id="notify" style="background:var(--bg-2)"><div class="wrap">
  <div class="cta-band center reveal">
    <h2>Be First To Know At Launch</h2>
    <p style="margin-inline:auto">Join the waitlist and get early access plus a launch-day discount.</p>
    <form data-fake class="hero-actions" style="justify-content:center;max-width:460px;margin-inline:auto">
      <input type="email" required placeholder="you@email.com" aria-label="Email" style="flex:1;padding:14px 18px;background:var(--black);border:1px solid var(--line);border-radius:100px;color:var(--text)">
      <button type="submit" class="btn btn-accent">Notify Me</button>
    </form>
    <p class="note" style="margin-top:14px">App Store & Google Play listings are in review. Badges link here until live.</p>
  </div>
</div></section>
""")

# ---------- TERMS ----------
def legal(slug, title, desc, h1, intro, sections):
    secs = "\n".join(f"<h2>{i+1}. {h}</h2>\n{b}" for i,(h,b) in enumerate(sections))
    return dict(title=title, desc=desc, keywords="terms, privacy, legal, OptimityFX", active="",
      jsonld='', body=f"""
<section class="page-hero" style="padding-bottom:20px"><div class="wrap" style="max-width:820px">
  <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span>{h1}</div>
  <h1 class="reveal d1" style="font-size:clamp(2.2rem,5vw,3.4rem)">{h1}</h1>
  <p class="note reveal d2" style="margin-top:8px">Last updated: June 1, 2026</p>
</div></section>
<section class="section" style="padding-top:30px"><div class="wrap"><div class="article reveal">
  <p>{intro}</p>
  {secs}
  <h2>Contact</h2>
  <p>Questions about this document? Email us at <a href="mailto:optimityfx.studio@gmail.com" style="color:var(--accent)">optimityfx.studio@gmail.com</a>.</p>
</div></div></section>
""")

PAGES["terms.html"] = legal("terms.html",
 "Terms & Conditions | OptimityFX",
 "OptimityFX terms and conditions covering services, payments, intellectual property, revisions, refunds and acceptable use.",
 "Terms &amp; Conditions",
 "Welcome to OptimityFX. By accessing our website, purchasing products or engaging our services, you agree to these Terms &amp; Conditions. Please read them carefully.",
 [
  ("Services","<p>OptimityFX provides creative services including video editing, color grading, graphic design, AI-generated content, education (NextGen Academy) and B2B solutions. Project scope, deliverables and timelines are defined in your individual agreement or order.</p>"),
  ("Payments &amp; Invoicing","<p>Project work typically requires an advance to commence, with the balance due before final delivery. Digital products and courses are charged in full at checkout. All prices are exclusive of applicable taxes unless stated.</p>"),
  ("Revisions","<p>Each engagement includes a defined number of revision rounds. Additional revisions or scope changes may incur extra charges, communicated before work proceeds.</p>"),
  ("Refunds","<p>Service deposits are non-refundable once work has begun. Digital products (LUTs, presets, templates, courses) are non-refundable after download due to their nature. See specific offer terms at checkout.</p>"),
  ("Intellectual Property","<p>Upon full payment, final deliverables are licensed or assigned to you as specified in your agreement. OptimityFX retains the right to showcase completed work in its portfolio and marketing unless a written NDA states otherwise. Digital products are licensed for your use and may not be resold or redistributed.</p>"),
  ("Client Responsibilities","<p>You are responsible for providing source files, timely feedback and any rights/clearances for materials you supply (footage, music, logos). You warrant that supplied content does not infringe third-party rights.</p>"),
  ("AI-Generated Content","<p>AI-assisted deliverables are produced using third-party tools. While we strive for originality and quality, you are responsible for final review and compliance with platform and advertising policies in your jurisdiction.</p>"),
  ("Acceptable Use","<p>You agree not to misuse our website, attempt unauthorized access, or use our services for unlawful, infringing or harmful purposes.</p>"),
  ("Limitation of Liability","<p>To the maximum extent permitted by law, OptimityFX's total liability for any claim is limited to the amount paid for the specific service or product giving rise to the claim. We are not liable for indirect or consequential damages.</p>"),
  ("Changes to These Terms","<p>We may update these Terms from time to time. Continued use of our services after changes constitutes acceptance of the revised Terms.</p>"),
  ("Governing Law","<p>These Terms are governed by the laws of India, and disputes are subject to the exclusive jurisdiction of the courts located in our registered place of business.</p>"),
 ])

PAGES["privacy.html"] = legal("privacy.html",
 "Privacy Policy | OptimityFX",
 "How OptimityFX collects, uses, stores and protects your personal data, including cookies, third-party services and your privacy rights.",
 "Privacy Policy",
 "Your privacy matters to us. This Privacy Policy explains what information OptimityFX collects, how we use it, and the choices you have. By using our website and services, you consent to this policy.",
 [
  ("Information We Collect","<p>We collect information you provide directly — such as your name, email, phone number and project details when you contact us, place an order or enroll in a course. We also collect limited technical data (IP address, browser type, pages visited) automatically.</p>"),
  ("How We Use Your Information","<ul class='dot'><li>To respond to enquiries and deliver services</li><li>To process payments and fulfil orders</li><li>To provide course access and customer support</li><li>To send updates and marketing (with your consent)</li><li>To improve our website and offerings</li></ul>"),
  ("Cookies &amp; Analytics","<p>We use cookies and analytics tools (e.g. Google Analytics) to understand usage and improve experience. You can control cookies through your browser settings. Disabling cookies may affect some functionality.</p>"),
  ("Third-Party Services","<p>We use trusted third parties for payments, email, hosting and analytics. These providers process data only as needed to deliver their services and under their own privacy commitments. We do not sell your personal data.</p>"),
  ("Data Retention","<p>We retain personal data only as long as necessary to provide services, comply with legal obligations and resolve disputes.</p>"),
  ("Data Security","<p>We implement reasonable technical and organizational measures to protect your data. However, no method of transmission over the internet is 100% secure.</p>"),
  ("Your Rights","<p>Depending on your location, you may have the right to access, correct, delete or restrict processing of your personal data, and to withdraw consent. To exercise these rights, contact us at optimityfx.studio@gmail.com.</p>"),
  ("Children's Privacy","<p>Our services are not directed to children under 13 (or the minimum age in your jurisdiction). We do not knowingly collect data from children.</p>"),
  ("International Users","<p>As we serve clients across 10+ countries, your data may be processed outside your country of residence. We take steps to ensure appropriate safeguards are in place.</p>"),
  ("Changes to This Policy","<p>We may update this Privacy Policy periodically. The 'Last updated' date reflects the latest revision.</p>"),
 ])

# ===== SERVICE DETAIL PAGES =====
# Hero image: use dedicated hero if present, otherwise fall back to existing service image.
def _svc_hero(sid):
    hero = f"assets/services/service-{sid}-hero.webp"
    if os.path.exists(hero):
        return hero
    return f"assets/services/{sid}.webp"

# Rich per-service data: (title, tagline, h1_main, h1_accent, lead, includes, process, for_whom, faqs, related, cta_label, cta_url, meta_desc, keywords, is_ai)
SVC_DETAIL = {
 "editing": (
  "Video Editing", "01 — Video Editing",
  "Edits That Hold", "Attention",
  "We cut for story, pacing and retention. Every reel, ad film, documentary or long-form piece gets sound design, motion graphics, captions and an obsessive eye for the frame that makes viewers stay.",
  [
   ("Short-form & long-form", "Reels, Shorts, TikTok, YouTube, ad films, documentaries and podcasts."),
   ("Motion graphics & titles", "Animated lower-thirds, openers, kinetic type and branded end cards."),
   ("Sound design & audio cleanup", "Dialogue levelling, music sync, SFX layering and noise removal."),
   ("Subtitles & captions", "Burned-in or SRT/VTT, multi-language on request."),
   ("Multi-format delivery", "16:9, 9:16, 1:1 — one project, every platform."),
   ("Revision rounds included", "2 structured revision rounds with direct feedback — unlimited on retainer."),
  ],
  [("Brief & References","You share the footage, goals and inspiration."),
   ("Rough Cut","We assemble the story, pacing and arc."),
   ("Revisions","Your feedback, applied until it's perfect."),
   ("Final Delivery","All formats delivered via WeTransfer or Drive."),],
  ["Brands & D2C companies","Music artists & labels","YouTube creators","Ad agencies & media houses"],
  [("How long does a typical edit take?","Most short-form pieces (under 3 min) are delivered within 48–72 hours. Long-form and series work is scoped per project, usually 4–7 days."),
   ("What footage formats do you accept?","We work with any codec — Sony, Canon, Blackmagic RAW, ProRes, h.264/h.265, DJI D-Log and more."),
   ("Do you provide music?","We source royalty-free tracks or work with tracks you supply. For client work requiring sync licensing, we can advise."),
   ("Can you repurpose one video into multiple formats?","Absolutely — repurposing a hero film into Reels, Stories and a YouTube cut is a common request and is quoted as a bundle."),],
  [("grading","Color Grading","Make every frame look cinematic."),("design","Graphic Design","Thumbnails & key art that get clicked."),("ugc","AI UGC","Scale your content with AI-powered UGC.")],
  "Get a Quote","contact.html",
  "Professional video editing service — reels, ad films, documentaries & long-form. Motion graphics, sound design and multi-format delivery by OptimityFX.",
  "professional video editing service, hire video editor, cinematic video editing, reel editing, ad film editing, YouTube video editing",
  False,
 ),
 "grading": (
  "Color Grading", "02 — Color Grading",
  "A Million-Dollar", "Look",
  "Primary & secondary correction, shot matching, film emulation and custom cinematic looks in DaVinci Resolve. We make every frame intentional — your footage deserves colour that actually means something.",
  [
   ("LOG / RAW primary grading", "S-Log, C-Log, BRAW, ARRI LogC — we work in your native colour science."),
   ("Shot matching & continuity", "Consistent look across every angle, lighting condition and camera."),
   ("Custom LUT creation", "Bespoke .cube LUTs built around your camera, story and brand."),
   ("Film emulation & grain", "Kodak, Fuji and ARRI-inspired looks applied with restraint."),
   ("Skin-tone & beauty work", "Precision secondary masks to protect and enhance talent."),
   ("DPX / ProRes master delivery", "Graded masters in any format required, plus a final LUT export."),
  ],
  [("Footage Handoff","Deliver your RAW/LOG files, LUT preferences and references."),
   ("Primary Grade","We establish exposure, white balance and base contrast."),
   ("Secondary & Look","Selective colour, window masks, creative grade applied."),
   ("Export & Delivery","Graded DPX / ProRes masters + a custom LUT for the edit."),],
  ["Film & documentary directors","Music video producers","Wedding & event videographers","Brand & commercial teams"],
  [("What NLE / grading software do you use?","DaVinci Resolve is our primary tool, using Fusion and Color pages. We can also deliver XML or CDL round-trips for Premiere Pro timelines."),
   ("Do you work with flat / LOG footage?","Yes — we require LOG or RAW files for the best results. We can work with h.264 if LOG is unavailable, but final quality depends on source."),
   ("Can I get a custom LUT as a deliverable?","Yes. Custom LUT creation is included in most grading packages or available as a standalone add-on."),
   ("How do revisions work?","We include 2 rounds of revisions as standard. Unlimited revisions are available on retainer."),],
  [("editing","Video Editing","Full pipeline from cut to grade."),("ai-vfx","AI VFX","Add impossible shots to your grade."),("design","Graphic Design","Key art to match your cinematic look.")],
  "Get a Grade","contact.html",
  "Professional color grading service in DaVinci Resolve — LOG/RAW grading, shot matching, custom LUTs and film emulation by OptimityFX.",
  "professional color grading service, DaVinci Resolve colorist, hire colorist, LOG grading, custom LUT creation, cinematic color grade",
  False,
 ),
 "design": (
  "Graphic Design", "03 — Graphic Design",
  "Designed To Be", "Clicked",
  "Click-magnet thumbnails, key art, posters, brand identities and social media kits engineered for attention — and built around your brand system so every asset feels like it belongs.",
  [
   ("YouTube thumbnails & channel art", "High-contrast, data-informed designs that improve CTR."),
   ("Brand identity & logo systems", "Wordmarks, symbols, colour palettes and usage guidelines."),
   ("Posters & key art", "Film posters, event key art, album covers and OOH assets."),
   ("Social media kits", "Story, feed and Reel templates — on-brand, ready to edit."),
   ("Presentation & pitch decks", "Investor and brand decks that communicate clearly and look premium."),
   ("Source files on delivery", "Layered PSDs, AI files and export-ready assets in every format you need."),
  ],
  [("Brief & Moodboard","You share your vision, audience and references."),
   ("Concepts","2–3 initial directions for you to react to."),
   ("Refinement","We develop your chosen direction to pixel-perfect."),
   ("Asset Delivery","Layered PSDs, SVGs and export-ready files in all sizes."),],
  ["YouTubers & podcasters","Music artists & event organisers","Startups & D2C brands","Film & production companies"],
  [("What file formats do you deliver?","We deliver print-ready PDFs, layered PSDs or AI files, and web-optimised PNGs/SVGs. Any format you need, just ask."),
   ("Do you work with existing brand guidelines?","Yes — we always work within your existing brand system first. If you don't have one yet, we'll create it."),
   ("How many concepts do I get?","Standard packages include 2–3 initial concepts. We develop the chosen direction through as many rounds as needed."),
   ("Can you design for print and digital?","Absolutely. All designs are set up for both screen and print at full resolution from the start."),],
  [("editing","Video Editing","Put your brand assets in motion."),("grading","Color Grading","Colour-match your design to your film."),("ai-tvc","AI TV Advertisement","Bring your brand into a full AI ad film.")],
  "Start a Brief","contact.html",
  "Professional graphic design studio — YouTube thumbnails, brand identity, key art, posters and social media kits by OptimityFX.",
  "graphic design studio, YouTube thumbnail design, brand identity design, key art design, social media kit, poster design service",
  False,
 ),
 "ai-music": (
  "AI Music Video", "04 — AI Music Video",
  "Imagination,", "Rendered",
  "From concept and storyboard to generative visuals and final edit — striking AI music videos that match your sound, build a world around it and stand out on every platform.",
  [
   ("Concept & storyboard", "We translate your track's mood into a visual treatment and scene-by-scene storyboard."),
   ("Generative visuals", "AI-produced imagery and sequences with a consistent, locked-in visual style."),
   ("Beat-synced editing", "Every cut, transition and effect is timed to the music."),
   ("Colour grade & finishing", "Cinematic grade and final delivery in broadcast resolution."),
   ("Multi-platform cuts", "Lyric video, short-form teaser and full video from one production."),
   ("Rights-cleared music & VO", "Licensed or original score plus voiceover sourcing if your track needs it."),
  ],
  [("Track & Brief","Share your audio, mood references and visual ideas."),
   ("Storyboard & Style","We map the scenes and lock the visual language."),
   ("AI Generation & Edit","Visuals are generated, cut and graded."),
   ("Delivery","Final video + platform cuts delivered in 5–10 days."),],
  ["Independent artists","Record labels","Music producers","Podcasters & audiobook publishers"],
  [("Do I need to supply any footage?","No — we generate everything from scratch using AI. You supply the audio and your creative vision."),
   ("How long does production take?","Most AI music videos are delivered within 5–10 business days, depending on length and complexity."),
   ("What length of track works best?","We work with tracks from 1 minute to 5+ minutes. Longer tracks are scoped individually."),
   ("Can I use the video on YouTube & streaming platforms?","Yes. We deliver broadcast-ready files cleared for YouTube, Spotify Canvas, Apple Music and social."),],
  [("editing","Video Editing","Human-crafted editing to complement your AI visuals."),("grading","Color Grading","A signature cinematic grade for your video."),("ai-vfx","AI VFX","Add next-level effects to your music video.")],
  "Discuss Your Track","contact.html",
  "AI music video production — concept, storyboard, generative visuals and beat-synced editing by OptimityFX. Delivered in days, not weeks.",
  "AI music video production, generative music video, AI video for artists, AI visual music video, music video without film crew",
  True,
 ),
 "ugc": (
  "AI UGC", "05 — AI UGC",
  "Content That", "Converts",
  "Authentic creator-style UGC and AI-generated avatars at scale — hook-first scripts, multiple variations and every aspect ratio, ready to run as performance ads across every platform.",
  [
   ("Real-creator & AI-avatar UGC", "Choose human creators, AI avatars or a blend — same quality, different cost profiles."),
   ("Hook-first scripting", "Every video leads with a scroll-stopping hook, tested across your audience."),
   ("Multiple creative variations", "3–6 hooks per product, so you can split-test and scale winners."),
   ("Multi-platform aspect ratios", "9:16, 1:1 and 16:9 delivered from every production."),
   ("Post-production finishing", "Captions, music, SFX, colour and brand overlays included."),
   ("Performance insights", "We flag which hooks test strongest and recommend the next iteration."),
  ],
  [("Brief & Product","You share the product, audience and key messaging."),
   ("Scripts & Hooks","We write hook-first scripts and submit for approval."),
   ("Production","AI or real-creator shoots, edited and polished."),
   ("Delivery & Scale","Variations delivered, ready to test and scale winners."),],
  ["D2C & e-commerce brands","Performance marketing teams","Apps & SaaS products","Health, beauty & lifestyle brands"],
  [("What's the difference between real-creator and AI UGC?","Real-creator UGC uses actual human talent filmed on-location. AI UGC uses generative avatars and voice synthesis to produce creator-style content without a film crew."),
   ("How many variations do I get?","Standard packages deliver 3–6 hook variations per product. Volume bundles are available for scaling."),
   ("Can you match a specific creator persona or style?","Yes — we build consistent AI personas or match real-creator styles for brand alignment across all variations."),
   ("Do you handle ad platform uploads?","We deliver files ready for Meta, TikTok and Google Ads. Platform upload can be added as a managed service."),],
  [("commercial","AI Product Commercial","Full cinematic product ads without a crew."),("ai-influencer","AI Influencer","A persistent AI brand spokesperson."),("ai-tvc","AI TV Advertisement","Scale up to broadcast-grade AI ad films.")],
  "Scale Your UGC","contact.html",
  "AI UGC production at scale — hook-first scripts, AI avatars and real-creator content for D2C brands and performance marketers by OptimityFX.",
  "AI UGC production, user generated content ads, AI avatar UGC, performance ad content, D2C UGC service, creator style ads",
  True,
 ),
 "commercial": (
  "AI Product Commercial", "06 — AI Product Commercial",
  "Ads Without A", "Film Crew",
  "Premium, photorealistic product commercials generated with AI — hero shots, lifestyle scenes and dynamic motion. Delivered in days, at a fraction of the cost of a traditional production.",
  [
   ("Photoreal product hero shots", "Studio-grade hero imagery and 360° renders without a physical shoot."),
   ("Lifestyle & environment scenes", "AI-generated lifestyle contexts that place your product in the perfect setting."),
   ("Motion, VFX & sound design", "Dynamic product reveal animations, particle effects and a full audio mix."),
   ("Voiceover & music", "Professional VO and licensed or original score included."),
   ("Ready for ads, web & retail", "Delivered in 16:9, 9:16 and 1:1 — ready for every channel."),
   ("Brand guideline compliance", "Every frame respects your colours, fonts and visual identity standards."),
  ],
  [("Product Brief","You share product images, brand guidelines and campaign goals."),
   ("Storyboard & Concept","We design the visual world for your commercial."),
   ("AI Production","Scenes generated, assembled, graded and mixed."),
   ("Final Delivery","Campaign-ready cuts in all formats within 5–7 days."),],
  ["E-commerce & D2C brands","Consumer electronics companies","Luxury & beauty brands","Startups launching new products"],
  [("Do you need the physical product?","No physical product is required. High-resolution product photos or a 3D model (if available) give us the best results."),
   ("Can the commercial run on Meta and Google Ads?","Yes. All deliverables are formatted and compressed for Meta, Google, YouTube and programmatic display."),
   ("How is this different from a regular product photoshoot?","We generate motion video, not static images — and deliver it in days, not weeks, at a significantly lower cost than a traditional studio or film production."),
   ("Do you offer product photography as well?","Yes — our sister skill 'AI Product Photoshoot' covers static imagery. Ask us about bundling both."),],
  [("ugc","AI UGC","Add creator-style UGC to your product launch."),("ai-tvc","AI TV Advertisement","Scale your commercial to broadcast TV."),("grading","Color Grading","A premium cinematic grade for every frame.")],
  "Get a Commercial","contact.html",
  "AI product commercial production — photorealistic hero shots, lifestyle scenes, motion and sound design, delivered in days by OptimityFX.",
  "AI product commercial, AI advertising production, product video without film crew, AI product ad, photorealistic product video",
  True,
 ),
 "ai-tvc": (
  "AI TV Advertisement", "07 — AI TV Advertisement",
  "Broadcast-Ready,", "AI-Made",
  "Full TV commercials produced with AI — from script and storyboard to a polished, broadcast-grade ad film. Big-screen impact without the big-screen production budget.",
  [
   ("Script, storyboard & concept", "A full creative treatment developed from your brief and brand guidelines."),
   ("AI scene generation", "Cinematic, high-fidelity scenes generated at broadcast resolution."),
   ("Voiceover & music composition", "Professional VO casting or AI voice, plus original or licensed score."),
   ("Sound design & mix", "Full Dolby-compliant audio mix ready for broadcast playout."),
   ("Broadcast & OTT-ready delivery", "Delivered to AMPP, AS-11, ProRes or any spec required by your broadcaster."),
   ("15s, 30s & 60s cuts", "All standard campaign lengths produced from a single production."),
  ],
  [("Brief & Brand Guidelines","You share the campaign objective, brand standards and any existing assets."),
   ("Script & Storyboard","We write the script and map every scene for approval."),
   ("AI Production & Grade","Scenes generated, assembled, graded and fully mixed."),
   ("Broadcast Delivery","Playout-ready masters delivered in your broadcaster's required spec."),],
  ["Enterprise brands & CMOs","Media buyers & agencies","OTT & streaming advertisers","Political & public-awareness campaigns"],
  [("Can an AI TV commercial run on national broadcast?","Yes. We deliver to broadcast-compliant specs including AS-11, AMPP and ProRes masters that meet the technical requirements of major broadcasters."),
   ("What campaign lengths do you produce?","We produce 15s, 30s and 60s commercials as standard. Custom lengths available."),
   ("Do you handle media buying?","We focus on production excellence. For media planning and buying, we can refer trusted partners."),
   ("How does cost compare to a traditional TVC?","AI production typically costs 70–90% less than a traditional film production of equivalent visual quality."),],
  [("commercial","AI Product Commercial","Shorter, social-first product ads."),("ugc","AI UGC","Creator-style performance content at scale."),("ai-vfx","AI VFX","Add impossible VFX shots to your TVC.")],
  "Plan a TV Ad","contact.html",
  "AI TV commercial production — broadcast-ready ad films with script, storyboard, AI scenes, VO and full mix by OptimityFX. 70–90% less than traditional TVC costs.",
  "AI TV commercial production, broadcast AI advertisement, AI TVC service, AI ad film, television commercial without film crew",
  True,
 ),
 "ai-influencer": (
  "AI Influencer", "08 — AI Influencer",
  "A Face That", "Never Sleeps",
  "Build a custom AI influencer or brand spokesperson — a consistent, fully controllable digital persona that posts, presents and promotes around the clock, in any language, on every platform.",
  [
   ("Custom persona design", "Appearance, personality, voice and backstory crafted around your brand."),
   ("Talking-head & lifestyle content", "Scripted product reviews, tutorials, announcements and day-in-the-life content."),
   ("Multi-language & multi-platform", "The same persona speaks to audiences in their language, natively."),
   ("Consistent visual identity", "Every piece of content maintains the same face, style and brand voice."),
   ("Content calendar & batch delivery", "Weekly or monthly content packs delivered ready to post."),
   ("Full IP ownership transfer", "The persona, voice model and all content are yours on final payment."),
  ],
  [("Persona Brief","You define the role, tone, audience and platform goals."),
   ("Character Creation","We design the AI persona's look, voice and personality."),
   ("Content Production","Scripts written, content generated and finished."),
   ("Ongoing Delivery","Weekly or monthly packs, posting-ready."),],
  ["D2C & e-commerce brands","SaaS & app companies","Media & entertainment properties","Influencer marketing agencies"],
  [("Does the AI influencer look photorealistic?","Yes — our AI influencers are generated to be photorealistic and consistent across all content, indistinguishable from human creators to the casual viewer."),
   ("Can one AI influencer post in multiple languages?","Yes. The same persona can be adapted to English, Hindi, Spanish, Arabic and most major languages without any loss of visual consistency."),
   ("Who owns the AI influencer persona?","You do. We transfer full IP ownership of the character design, voice model and all generated content upon final payment."),
   ("Can the AI influencer promote different products?","Absolutely — one persona can be scripted to promote your full product range, seasonal campaigns or third-party partnerships."),],
  [("ugc","AI UGC","Scalable creator-style performance ads."),("commercial","AI Product Commercial","Hero product ads for your influencer to promote."),("ai-tvc","AI TV Advertisement","Put your AI persona in a broadcast commercial.")],
  "Create an AI Influencer","contact.html",
  "AI influencer creation service — custom digital personas, talking-head content and multilingual brand spokespeople at scale by OptimityFX.",
  "AI influencer creation, digital avatar influencer, AI brand spokesperson, virtual influencer service, AI content creator",
  True,
 ),
 "ai-vfx": (
  "AI VFX", "09 — AI VFX",
  "Impossible Shots,", "Made Possible",
  "AI-powered visual effects and compositing — set extensions, object removal, relighting and effects that used to need a full VFX house, delivered faster, leaner and at a fraction of the cost.",
  [
   ("Set extensions & environments", "Expand or replace backgrounds with photoreal AI-generated environments."),
   ("Object removal & cleanup", "Remove rigs, wires, crew and unwanted elements frame-by-frame."),
   ("Relighting & colour", "Re-light scenes in post — change time of day, add drama, match locations."),
   ("Rotoscoping & compositing", "Precise mattes and seamless layer compositing for any shot."),
   ("Generative effects & enhancements", "Particles, weather, fire, smoke and energy effects generated and composited."),
   ("Timeline integration", "Composited shots returned inside your existing Premiere, Resolve or Avid timeline."),
  ],
  [("Shot List & Brief","You share the footage, problem frames and the desired result."),
   ("VFX Breakdown","We scope each shot and confirm the approach."),
   ("AI Processing & Compositing","Effects generated, layered and integrated into the edit."),
   ("QC & Delivery","Frame-by-frame QC, then graded masters delivered."),],
  ["Film & commercial directors","Post-production houses","Music video producers","Documentary & branded content teams"],
  [("What types of VFX do you handle with AI?","Set extensions, clean-up, background replacement, atmospheric effects (rain, smoke, fire), relighting and compositing. Complex simulations (fluid dynamics, destruction) are scoped individually."),
   ("Do you need original RAW files for VFX work?","Ideally yes — higher-quality source files produce better compositing results. We can work with finished exports in some cases."),
   ("Can you integrate AI VFX into an existing edit?","Yes. We work directly inside your existing timeline (Premiere, Resolve, Avid) and return the composited sequence ready to render."),
   ("How is pricing structured for VFX?","VFX is quoted per shot. We provide a full breakdown after reviewing the footage, so there are no surprises."),],
  [("grading","Color Grading","Grade your composited shots to perfection."),("editing","Video Editing","Full post-production pipeline with VFX baked in."),("ai-tvc","AI TV Advertisement","VFX-heavy broadcast ad films.")],
  "Discuss VFX","contact.html",
  "AI VFX service — set extensions, object removal, relighting, rotoscoping and generative effects composited into your footage by OptimityFX.",
  "AI VFX service, AI visual effects, AI set extension, AI compositing, object removal video, generative VFX, AI post production",
  True,
 ),
}

def service_page(sid):
    (svc_title, tag_num, h1_main, h1_accent, lead, includes, process,
     for_whom, faqs, related, cta_label, cta_url, meta_desc, keywords, is_ai) = SVC_DETAIL[sid]
    ai_badge = ' <span class="ai-tag">AI POWERED</span>' if is_ai else ''
    hero_img = _svc_hero(sid)
    mid_img  = f"assets/services/service-{sid}-mid.webp"
    slug = f"service-{sid}.html"
    og_img = f"https://optimityfx.com/{hero_img}"
    svc_url = f"https://optimityfx.com/{slug}"

    # Split includes: first 3 cards before mid image, remaining after
    inc_before = "".join(
        f'<div class="card reveal"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">{SVC_ICON[sid]}</svg></div>'
        f'<h3>{t}</h3><p>{d}</p></div>'
        for t, d in includes[:3]
    )
    inc_after = "".join(
        f'<div class="card reveal"><div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">{SVC_ICON[sid]}</svg></div>'
        f'<h3>{t}</h3><p>{d}</p></div>'
        for t, d in includes[3:]
    )

    # process HTML
    proc_items = "".join(
        f'<div class="card reveal d{i}"><div class="ic">0{i+1}</div><h3>{t}</h3><p>{d}</p></div>'
        for i,(t,d) in enumerate(process)
    )

    # for-whom pills
    for_pills = "".join(
        f'<span class="trust-badge">{CHK} {w}</span>'
        for w in for_whom
    )

    # FAQ accordion
    faq_items = "".join(
        f'<div class="acc-item"><button class="acc-q">{q} <span class="pm"></span></button>'
        f'<div class="acc-a"><p>{a}</p></div></div>'
        for q,a in faqs
    )

    # Related services grid
    rel_cards = "".join(
        f'<div class="card reveal"><div class="ic">{_svc_icon(r)}</div>'
        f'<h3><a href="service-{r}.html" style="color:inherit;text-decoration:none">{rt}</a></h3>'
        f'<p>{rd}</p>'
        f'<a href="service-{r}.html" class="card-link">Learn more {ARR}</a></div>'
        for r,rt,rd in related
    )

    jsonld = (
        '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Service",'
        f'"name":"{svc_title}","serviceType":"{svc_title}",'
        '"provider":{"@type":"Organization","name":"OptimityFX","url":"https://optimityfx.com"},'
        f'"url":"{svc_url}","description":"{meta_desc}",'
        '"areaServed":"Worldwide",'
        f'"image":"{og_img}",'
        '"offers":{"@type":"Offer","price":"0","priceCurrency":"INR","description":"Custom quote on request"}}'
        '</script>'
        '\n<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
        '{"@type":"ListItem","position":1,"name":"Home","item":"https://optimityfx.com/"},'
        '{"@type":"ListItem","position":2,"name":"Services","item":"https://optimityfx.com/services.html"},'
        f'{{"@type":"ListItem","position":3,"name":"{svc_title}","item":"{svc_url}"}}'
        ']}</script>'
    )

    body = f"""
<section class="page-hero">
  <div class="wrap">
    <div class="crumbs reveal"><a href="index.html">Home</a><span>/</span><a href="services.html">Services</a><span>/</span>{svc_title}</div>
    <span class="tag-pill reveal">{tag_num}{ai_badge}</span>
    <h1 class="reveal d1" style="margin-top:14px">{h1_main}<br><span class="spectrum-text">{h1_accent}</span></h1>
    <p class="lead reveal d2">{lead}</p>
    <div class="hero-actions reveal d3" style="margin-top:28px">
      <a href="{cta_url}" class="btn btn-accent btn-lg">{cta_label} {ARR}</a>
      <a href="portfolio.html" class="btn btn-ghost btn-lg">See Our Work</a>
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap">
    <div class="reveal" style="border-radius:20px;overflow:hidden;border:1px solid var(--line);max-height:500px">
      <img src="{hero_img}" alt="{svc_title} — OptimityFX" style="width:100%;height:100%;object-fit:cover;display:block" loading="eager" width="1280" height="720">
    </div>
  </div>
</section>

<section class="section" style="background:var(--bg-2)">
  <div class="wrap">
    <div class="sec-head center reveal">
      <span class="eyebrow center-eb">What's Included</span>
      <h2 class="h-sec">Everything You <span class="grad-text">Need</span></h2>
    </div>
    <div class="grid g-3">
{inc_before}
    </div>
  </div>
</section>

<section class="section" style="background:var(--bg-2);padding-top:40px">
  <div class="wrap">
    <div class="grid g-3">
{inc_after}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="sec-head center reveal">
      <span class="eyebrow center-eb">How We Work</span>
      <h2 class="h-sec">A Simple, <span class="grad-text">Transparent</span> Process</h2>
    </div>
    <div class="grid g-4">
{proc_items}
    </div>
  </div>
</section>

<section class="section" style="background:var(--bg-2)">
  <div class="wrap">
    <div class="sec-head center reveal">
      <span class="eyebrow center-eb">Who It's For</span>
      <h2 class="h-sec">Built For <span class="grad-text">Ambitious Creators</span></h2>
    </div>
    <div class="trust-row reveal" style="justify-content:center;flex-wrap:wrap;gap:14px">
{for_pills}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap" style="max-width:820px">
    <div class="sec-head reveal">
      <span class="eyebrow">FAQ</span>
      <h2 class="h-sec">Common <span class="grad-text">Questions</span></h2>
    </div>
    <div class="reveal">
{faq_items}
    </div>
  </div>
</section>

<section class="section" style="background:var(--bg-2)">
  <div class="wrap">
    <div class="sec-head center reveal">
      <span class="eyebrow center-eb">Also Consider</span>
      <h2 class="h-sec">Related <span class="grad-text">Services</span></h2>
    </div>
    <div class="grid g-3">
{rel_cards}
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cta-band center reveal">
      <h2>Ready To Get Started?</h2>
      <p style="margin-inline:auto">Tell us about your project and we'll reply with a tailored quote within 24 hours.</p>
      <a href="{cta_url}" class="btn btn-accent btn-lg">{cta_label} {ARR}</a>
    </div>
  </div>
</section>
"""
    return dict(
        title=f"{svc_title} Service — {h1_main} {h1_accent} | OptimityFX",
        desc=meta_desc,
        keywords=keywords,
        active="services.html",
        og_image=og_img,
        jsonld=jsonld,
        body=body,
    )

for _sid in SVC_DETAIL:
    PAGES[f"service-{_sid}.html"] = service_page(_sid)

# ===== generate =====
for slug, cfg in PAGES.items():
    page(slug, cfg["title"], cfg["desc"], cfg.get("keywords",""), cfg["active"], cfg["body"], cfg.get("jsonld",""), cfg.get("og_image"))

# ===== sitemap.xml (static pages + every published blog post) =====
def write_sitemap():
    static = [
        ("", "weekly", "1.0"), ("services.html", "monthly", "0.9"),
        ("portfolio.html", "weekly", "0.9"), ("academy.html", "weekly", "0.8"),
        ("store.html", "weekly", "0.8"), ("b2b.html", "monthly", "0.7"),
        ("about.html", "monthly", "0.7"), ("blog.html", "weekly", "0.8"),
        ("app.html", "monthly", "0.6"), ("contact.html", "monthly", "0.8"),
        ("terms.html", "yearly", "0.3"), ("privacy.html", "yearly", "0.3"),
        ("service-editing.html", "monthly", "0.85"),
        ("service-grading.html", "monthly", "0.85"),
        ("service-design.html", "monthly", "0.85"),
        ("service-ai-music.html", "monthly", "0.85"),
        ("service-ugc.html", "monthly", "0.85"),
        ("service-commercial.html", "monthly", "0.85"),
        ("service-ai-tvc.html", "monthly", "0.85"),
        ("service-ai-influencer.html", "monthly", "0.85"),
        ("service-ai-vfx.html", "monthly", "0.85"),
    ]
    rows = []
    for loc, freq, pri in static:
        rows.append(f'  <url><loc>https://optimityfx.com/{loc}</loc><changefreq>{freq}</changefreq><priority>{pri}</priority></url>')
    for m in POSTS:
        lastmod = f"<lastmod>{m.get('iso','')}</lastmod>" if m.get("iso") else ""
        rows.append(f'  <url><loc>https://optimityfx.com/blog-{m["slug"]}.html</loc>{lastmod}<changefreq>monthly</changefreq><priority>0.6</priority></url>')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + '\n</urlset>\n'
    with open("sitemap.xml", "w") as f:
        f.write(xml)
    print(f"wrote sitemap.xml ({len(static)} pages + {len(POSTS)} posts)")

write_sitemap()
print("Done.")
