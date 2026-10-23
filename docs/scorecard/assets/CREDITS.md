# Scorecard backdrop credits

The scorecard background is **procedurally generated** — there are no photographic, video or
third-party media assets in this directory or hotlinked from the page.

| Layer | How it is made | Where |
| --- | --- | --- |
| Aurora gradient mesh | Four blurred `radial-gradient` blobs drifting on `transform` keyframes (38–52 s, alternate) | `index.html` → `.sky .aurora` |
| Radar motif | Inline SVG of concentric pentagons + spokes (the same five-axis geometry as the score-profile radar chart), rotating once every 300 s | `index.html` → `.sky .motif` |
| Film grain | Inline SVG `feTurbulence` tile (data URI, ~600 bytes) at 6–10 % opacity | `index.html` → `.grain` |

All three layers are static under `prefers-reduced-motion: reduce`. Added weight: ~0 KB of media.

Fonts are loaded from Google Fonts under the SIL Open Font License 1.1:

- [Instrument Serif](https://fonts.google.com/specimen/Instrument+Serif) — Rodrigo Fuenzalida & Jordan Egstad
- [Inter](https://fonts.google.com/specimen/Inter) — Rasmus Andersson
