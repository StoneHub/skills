---
name: promo-video
description: Direct and build promo, launch, ad, explainer, and social videos entirely in code. Brainstorm and grill the concept with the user, gather real brand assets and approved claims, animate with HTML/JS (or Remotion, GSAP, Three.js…) where every frame is a function of time, render with Playwright + ffmpeg, add synthesized SFX, music, and ElevenLabs voiceover with synced captions, and review via contact sheets. Use this whenever someone wants a video, ad, promo, teaser, sizzle reel, launch clip, motion graphic, product demo video, animated explainer, or "something like those Opus videos" for a product, app, company, repo, or release, even if they don't say "skill" or name a tool, and also for making variants (vertical cut, 15-second cut, new hook) of an existing code-built video.
---

# Promo video

You're the director and the editor, not just the coder. The renderer is solved (see `scripts/`). Your leverage is in the idea, the truth of what's shown, and the craft of the edit. Move fast on mechanics and slow down on the concept.

Everything here is a default, not a constraint. If the idea wants 3D, real footage, a song, generated imagery, or a tool released after this skill was written, use it. Check what's current when it matters.

## Workflow

### 1. Grill the idea (default on)
Read `references/creative-grill.md` and run a short back-and-forth: the truth (audience, pain, proof, constraints, assets, sound), three genuinely different concepts with a recommendation, a pressure test of the chosen one, and a beat sheet the user approves. Offer options to react to, push back on vague answers, and bring bold ideas.

If the user wants speed ("just make it"), do a silent self-grill, build, and present the cut with the alternate concepts so they can redirect.

### 2. Gather truth and assets
Find assets before asking for them:
- **Repo:** app icons, UI source (real strings, layout, colors), README, releases.
- **Website:** logo SVGs, screenshots, computed brand colors and fonts (use a real browser), published stats and taglines.
- **Team channels and docs**, if available: past videos, testimonials, brand guides.

Record where each claim comes from. Read `references/claims-and-trust.md` once per project. It covers dramatization labels, verbatim claims, competitor framing, third-party logos and personal data.

### 3. Set up the project
In a working folder:
```bash
npm i playwright-core            # render.mjs uses the system Chrome if no Playwright browser is installed
cp <skill>/assets/template.html promo.html
```
The template has the helper kit (`prog`, easing, `spring`, `css`, `pop`, `typed`, seeded PRNG), the scene table, font preloading, and optional VO timing and captions. Read `references/pipeline.md` for the frame contract and when to use other engines.

### 4. Voice first (if there's narration)
Write the VO script during the grill. Generate it with `scripts/voiceover.py` (ElevenLabs; macOS `say` for free draft timing), include `vo/voice.js`, and schedule the beats from the line and word timings. See `references/audio-and-voice.md`.

### 5. Build
Write `promo.html` scene by scene against the beat sheet. Prefer real UI (screenshots, or UI rebuilt from source) over generic mockups. Use the brand's own motif for transitions. `references/craft.md` has pacing, motion and format notes from past runs.

### 6. Review with contact sheets (the loop that makes it good)
```bash
node <skill>/scripts/render.mjs promo.html sheet --every 1.5 --cols 4     # whole video at a glance
node <skill>/scripts/render.mjs promo.html sheet 3.2 8.75 12.9 --cols 3   # specific beats
```
Open the image and critique it hard: collisions, overflow, clipped or tiny text, dead space, off-brand details, story clarity with the sound off. Fix and re-sheet until clean. Seconds per loop beats minutes per full render. If you can't view images in your environment, ask the user to check the sheet.

### 7. Sound
- **SFX and beat bed:** write a cue sheet and run `python3 <skill>/scripts/sfx.py cues.json out/sfx.wav`, keeping cue times in sync with the scene table. For richer sound, consider generated or licensed music and SFX.
- **Mix:** `python3 <skill>/scripts/mix.py --video out/video-silent.mp4 --voice vo/voice.wav --sfx out/sfx.wav [--music m.mp3] --out final.mp4`. It ducks the bed under the voice and normalizes to −14 LUFS.

### 8. Render and verify
```bash
node <skill>/scripts/render.mjs promo.html video --fps 60 --out out/video-silent.mp4   # add --size 1080x1920 for vertical
```
Then sample frames from the final MP4 itself, especially scene boundaries, and check the duration and audio streams with ffprobe.

### 9. Deliver honestly
Share the file and a short beat-by-beat summary. Then list:
- what's dramatized, and what's recreated rather than real footage;
- font or asset substitutions;
- claims needing sign-off;
- cheap variants on offer (9:16, 15 s cut, alternate hook or CTA).

Don't post or upload anywhere without explicit approval.

## Scripts
| Script | Purpose |
|---|---|
| `scripts/render.mjs` | `stills`, `sheet` (labelled contact sheet), `video`; `--size`, `--fps`, `--from/--to`, `--every`, `--chrome` |
| `scripts/sfx.py` | Stdlib synth: whoosh, hit, chime, pop, blip, tick, keys, slap, buzz, ring, riser, beat bed, pads; JSON cues or a Python API |
| `scripts/voiceover.py` | ElevenLabs TTS with timestamps (or `say`): per-line WAVs, `voice.wav`, `voice.json`, `voice.js`; `--list-voices`, `--list-models` |
| `scripts/mix.py` | Side-chain ducking, loudness normalization, mux to MP4 |

## References (read when relevant)
- `references/creative-grill.md`: brainstorming and grilling, concept archetypes, self-grill.
- `references/craft.md`: pacing, premium motion, product truth, formats, review.
- `references/pipeline.md`: frame contract, toolkit, alternatives (Remotion, GSAP, Three.js, footage, AI generation), assets.
- `references/audio-and-voice.md`: ElevenLabs workflow, writing for the ear, VO-first timing, SFX and music, mixing.
- `references/gotchas.md`: problems hit in real runs and their fixes. Skim before building.
- `references/claims-and-trust.md`: honesty and brand-safety checklist.
- `examples/connect-android.html`: a complete 35 s promo from the first runs (a founder-frustration parody). Skim it for working patterns (scene tables, transitions, UI mockups, typed text). Don't reuse the concept.
