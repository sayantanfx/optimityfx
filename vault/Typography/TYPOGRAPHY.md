# OptimityFX — Typography

## Typeface
**Inter** — used for both headings and body.
- Google Fonts: https://fonts.google.com/specimen/Inter
- Weights loaded on site: **300, 400, 500, 600, 700, 800, 900**
- Fallback stack: `'Inter', system-ui, sans-serif`
- Local `.ttf` files provided in the `../Fonts/` folder (plus `InterVariable.ttf`).

CSS tokens:
```
--head: 'Inter', system-ui, sans-serif;
--body: 'Inter', system-ui, sans-serif;
```

## Type scale (from live site CSS)
Sizes use responsive `clamp(min, preferred, max)`.

| Element | Size | Weight | Notes |
|---------|------|--------|-------|
| H1 | `clamp(2.8rem, 7vw, 6rem)` | 800 | line-height 1.02, letter-spacing -0.5px |
| H2 (`.h-sec`) | `clamp(2.1rem, 4.5vw, 3.5rem)` | 800 | UPPERCASE, letter-spacing -1px |
| H3 | `1.5rem` | 800 | letter-spacing -0.3px |
| Hero display | `clamp(2.2rem, 3.8vw, 4rem)` | 800 | |
| Stat number | `clamp(2.4rem, 5vw, 3.4rem)` | 800 | |
| Lead paragraph | `clamp(1.02rem, 1.6vw, 1.22rem)` | 400 | color: Muted `#9AA3B2` |
| Body (`p`) | `1rem` (16px base) | 400 | color: Muted |
| Eyebrow / label | `0.72rem` | 600 | UPPERCASE, letter-spacing 3.5px, cyan |
| Nav links | `0.9rem` | 500 | |
| Button | `0.92rem` | 600 | letter-spacing 0.2px |
| Button large | `1rem` | — | padding 17px 34px |
| Button small | `0.82rem` | — | |

## Rules of thumb
- Headings: weight **800**, tight negative letter-spacing, tight line-height (~1.02).
- H2 section titles are **UPPERCASE**.
- Body copy sits in Muted grey `#9AA3B2`; reserve pure white `#FFFFFF` for headings/emphasis.
- Eyebrows/labels: small, uppercase, wide tracking, cyan accent.
- Base font size = 16px (1rem).
