# Gotchas hit in real runs (and fixes)

## Rendering
- **File URLs with spaces got double-encoded.** `pathToFileURL(new URL(import.meta.url).pathname)` produced `%2520` and `ERR_FILE_NOT_FOUND`. Use `fileURLToPath(import.meta.url)`; `render.mjs` resolves paths correctly.
- **No Playwright browser installed.** `render.mjs` falls back to the system Chrome/Chromium (or set `CHROME_PATH`). It resolves Playwright from the project folder, so `npm i playwright-core` there.
- **Fonts used only in hidden scenes don't load until displayed.** The first frames of a later scene can render in a fallback font. Preload every face and weight with `document.fonts.load(...)` in `window.ready`. Use `display=block` for web fonts.
- **Measuring elements inside `display:none` scenes returns zeros.** Show the scene temporarily, measure once at init, then hide it again.
- **CSS transitions or animations break frame capture.** Everything must be set from `t`.
- **Playwright's CommonJS export:** a dynamic `import()` exposes `chromium` under `.default` (handled in `render.mjs`).

## Layout bugs the contact sheet caught
- Big display text ran under a neighbouring element ("Connected." under the app window) and stat numbers collided across columns. Measure widths, and leave room for the widest string the counters reach.
- A 3D-tilted card pushed past the frame edge. With `rotateY`, a negative angle brings the right edge toward the viewer and makes it bigger. Check the sign in a still.
- `<q>` adds its own quotation marks, so curly quotes in the text doubled up. Set `q { quotes: none }` or use a span.
- Overlaying live text on a screenshot (e.g., typing into its input box) needs coordinates mapped through the image's display scale. Compute them from the natural size, then verify in a still.

## Assets and research
- A bot wall (Cloudflare) blocked `curl` on the company homepage, but direct asset URLs worked. Read pages with a real browser and fetch uploads by URL with a normal User-Agent.
- Domain redirects (e.g. an old domain redirecting to the current one) need a second fetch of the final URL.
- Proprietary web fonts (Adobe Fonts / Typekit) can't be loaded locally. Use the site's declared fallback and disclose it.
- A company's own published graphic can contain third-party logos (e.g. AI-assistant logos in an integrations diagram). Leave those out of ads unless approved.
- Public screenshots can contain people's names. Flag them before reuse in ads.

## Tooling
- Contact-sheet globbing sorts lexicographically ("10.6" before "3.1"). `render.mjs sheet` labels frames in order; if you assemble frames yourself, zero-pad the names.
- ffmpeg `pad` errors when the input is bigger than the pad box. Use `scale=W:H:force_original_aspect_ratio=decrease,pad=W:H:(ow-iw)/2:(oh-ih)/2`.
- zsh errors on `rm -f x_*.png` when nothing matches ("no matches found"). Use `find . -name 'x_*.png' -delete`, or `setopt nullglob`.
- Pure-Python audio synthesis takes a few seconds for 35 s of audio. That's fine. Don't prematurely add numpy as a dependency.
