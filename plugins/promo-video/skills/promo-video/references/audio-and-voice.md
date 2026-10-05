# Audio and voice

## Decide the sound strategy early
- **Sound-off first.** The video must work muted. Then sound adds energy (SFX, music) and, when it helps, narration.
- **VO or not?** VO works for explainers, founder stories and testimonial-style pieces. Pure motion graphics with SFX often feel snappier for 15–35 s social ads. Ask during the grill.

## Voiceover with ElevenLabs (`scripts/voiceover.py`)
1. **Key:** the user exports `ELEVENLABS_API_KEY` in their own shell or a git-ignored `.env`. Never ask them to paste it into chat, and never write it to files or logs.
2. **Pick a voice:** `python3 voiceover.py --list-voices` (IDs, names, labels). Shortlist 2–3 that fit the brand. Generate the hook line in each and let the user listen before committing.
3. **Pick a model:** `python3 voiceover.py --list-models`. Models change; check what's current rather than trusting a hard-coded name. Rough guide: expressive or flagship models for hero ads, multilingual or stable models for consistency, fast or flash models for drafts.
4. **Write for the ear.** Short sentences. Spell out things a TTS might mangle ("T-B-I", "speed dot A I", "fourteen-day"). Use punctuation for pauses. Read it aloud at ~150–170 words per minute: 30 s is roughly 75–85 words.
5. **Generate per line.** The script sends `previous_text`/`next_text` so separately generated lines keep natural intonation. Regenerate single lines freely. A fixed `seed` helps reproducibility.
6. **Timing:** the API's `with-timestamps` endpoint returns per-character alignment. The script turns it into word timings in `vo/voice.json` and `vo/voice.js`.

### VO-first timing
When there's narration, let the voice set the clock: generate the VO, include `vo/voice.js`, and schedule beats from `VOICE.lines[id].start/end` (see `at()` in the template). Visual hits that land on the stressed word feel intentional. Burn in captions from the word timings (`captions(t)` in the template), since most viewers are muted.

Use `"provider": "say"` (macOS) to rough out timing for free while the script is in flux, then switch to ElevenLabs for the final. The timings will shift slightly, so re-render.

## SFX and music
- `scripts/sfx.py` synthesizes whooshes, hits, chimes, ticks, typing, phone rings, a kick/hat/bass beat bed and pads from a JSON cue sheet. It's fast and license-free, and fine for a draft or a minimal style.
- For richer sound, consider (check what's available and licensed):
  - **Generated SFX and music**, e.g. ElevenLabs' sound-effects and music generation APIs, or similar services.
  - **Licensed stock music.** Note the license in the delivery.
  - The user's own brand music or sonic logo.
- Place SFX on visual events (cuts, stamps, counters landing, alerts). Keep cue times in sync with the scene table: change one, change both.

## Mixing (`scripts/mix.py`)
- Ducks the SFX and music bed under the voice with side-chain compression, then loudness-normalizes to −14 LUFS integrated / −1.5 dBTP (social and web). Use −16 for quieter platforms and −23/−24 for broadcast.
- Don't rely on peak normalization alone. One loud hit makes everything else quiet. Balance gains in the cue sheet, then let `loudnorm` set the final level.
- Listen to the final MP4 (or ask the user to). Measured loudness doesn't tell you whether the mix feels right.
