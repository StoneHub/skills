# Craft notes: what made the first promos work

These are observations, not rules. Break them when the concept calls for it.

## Story and pacing
- **Hook in the first 2 seconds.** Start mid-situation: a typing line, a live call, a stopwatch. No logo intro.
- **Text-led storytelling.** Most social video plays muted. The story should work from on-screen text alone; sound adds punch.
- **One idea per scene.** About 2–4 seconds per beat for text, 6–9 seconds for a product sequence.
- **Turn on a specific detail.** "Minute 47. Still 'Waiting for device…'" or "They never say 'TBI.' They say they hit their head." Specific beats generic.
- **End card holds 3–4 seconds**: logo, the line, one CTA, the URL, small proof badges.
- **Length:** 15 s (hook + payoff), 30–35 s (full arc), 60 s+ only for demo or explainer formats.

## Making it feel premium
- **Springs with slight overshoot** for entrances (see `spring()` in the template). Avoid linear moves.
- **Stagger related elements** by 60–120 ms (word pops, list items, stat columns).
- **Use the brand's own motif as the transition.** For example, the logo's slanted bars sweeping across the cut. It's cheap, on-brand and memorable.
- **Kinetic detail**: typewriter text for transcripts and terminals, counters for stats, marker-swipe highlights for key phrases, a camera push-in for tension, screen shake on a failure beat.
- **Depth**: soft radial-gradient backgrounds, big soft shadows on floating cards, a slight 3D tilt (`perspective` + `rotateY`) on screenshots.
- **Typography**: one display face (heavy weight or italic if the brand uses it) plus one UI face. Big type, few words.

## Product truth on screen
- **Prefer real UI.** Use real screenshots, or rebuild the UI from the app's actual source strings, layout and icon. Read the code for status messages and layout values when you can.
- When you recreate UI to show a scenario (for example, a dramatized call), match the product's visual language and label any dramatization.
- **Generated or illustrative art can carry metaphor, but not evidence.** Check every brand detail (icon, colors, name) against the source. Generated concept art once used the wrong app icon.

## Formats
- **16:9** (1920×1080) for X, YouTube, sites and READMEs. **9:16** (1080×1920) for Reels, Shorts, TikTok and LinkedIn mobile. **1:1 or 4:5** for feeds.
- Re-lay out for each aspect ratio rather than letterboxing. Keep important content out of the top ~12% and bottom ~20% on vertical, where platform UI sits.
- **60 fps** for smooth motion graphics; **30 fps** for drafts or footage-heavy cuts.

## Review loop
- Render a **contact sheet** of the key beats before the full video. It catches overlaps, overflow, clipped text, wrong layering and off-brand details for seconds of render time.
- Look at the sheet critically: text collisions, elements leaving the frame, unreadable small text, empty dead zones, inconsistent margins.
- After the final render, **sample frames from the MP4 itself** (transitions especially). Scene boundaries are where bugs hide.
