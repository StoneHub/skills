# Pipeline: how frames get made

## The core contract
The animation is a program that draws frame t. A headless browser asks for each frame, screenshots it, and ffmpeg encodes the sequence. Because each picture depends only on `t`, renders are deterministic and any frame can be inspected on its own.

The page exposes:
- `window.seek(t)`: set every element's state for time `t` (seconds). It can be async.
- `window.DURATION`: total length in seconds.
- `window.ready` (optional): a promise to await before frame 0, e.g. font preloading.

Rules that keep it deterministic:
- No CSS transitions or animations, `Date.now()`, `requestAnimationFrame` loops, timers, or unseeded `Math.random()`. Use a seeded PRNG (`mulberry32` in the template).
- Hide inactive scenes with `display:none`, both for speed and to avoid stray overlap.
- Any physics or simulation must be computable from `t` (closed-form, or re-simulated from 0 with a fixed step).

## Default toolkit (known-good)
| Job | Default | Notes |
|---|---|---|
| Animation | One HTML file + vanilla JS helpers (`assets/template.html`) | Fastest to write and debug; real CSS/SVG/Canvas available |
| Capture | `scripts/render.mjs` (Playwright + Chrome) | stills, labelled contact sheets, video; any viewport size |
| Encode | ffmpeg, libx264, CRF 16, yuv420p, +faststart | Universally playable |
| SFX/beat | `scripts/sfx.py` (stdlib synth) | Fast, no assets, license-free |
| Voice | `scripts/voiceover.py` (ElevenLabs; macOS `say` for drafts) | Gives word timings for sync and captions |
| Mix | `scripts/mix.py` | Ducking under VO, loudness normalization, mux |

Render cost seen in practice: 35 s at 1080p60 (2,100 frames) took about 2.5–3.5 minutes. Draft at 30 fps or with `--from/--to` for a single section.

## Alternatives: reach for these when the concept wants them
The default exists to be fast, not to cap ambition. Before building, check whether something newer or better suited exists (a quick search on current tools is cheap), and use it if it serves the idea.
- **Remotion** (React compositions, rendered frame by frame): good for reusable templates and data-driven variants.
- **GSAP / HyperFrames**: rich timelines. Drive the timeline by seeking it (`tl.seek(t)`, paused) inside `window.seek`.
- **Three.js / WebGL shaders**: 3D product shots, particles, abstract brand worlds. Render with `preserveDrawingBuffer` and set uniforms from `t`.
- **Canvas 2D / p5.js**: generative art, data art.
- **D3**: data stories. **Lottie**: existing After Effects animations (use `goToAndStop(frame, true)`).
- **Manim**: math or technical explainers. **Motion Canvas**: code-first explainer animation.
- **Blender (Python)**: photoreal 3D. Heavier, but possible.
- **Real footage and screen recordings**: composite them with ffmpeg or a `<video>` element whose `currentTime` is set in `seek()` (await the `seeked` event). Real recordings are the most credible product evidence.
- **AI image, video or music generation**: if the environment offers it, it's great for illustrated plates, B-roll or textures. Verify brand details and rights, and never use it as fake product evidence.

## Assets
- Pull from the source of truth: repo icon sets, the company site's uploads, brand kits. Use a real browser (Playwright or a browser tool) to read the site's computed styles for exact colors and fonts.
- Convert `.webp` to `.png` (`ffmpeg -i a.webp a.png`) to view it. SVG logos drop straight into `<img>`.
- If a brand font isn't available (e.g. Adobe Fonts or Typekit), use the site's declared fallback or the closest free face, and say so in the delivery notes.
