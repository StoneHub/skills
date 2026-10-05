# StoneHub skills

Shared [Claude Code](https://claude.com/claude-code) skills, packaged as a plugin marketplace.

## Install

In Claude Code:

```
/plugin marketplace add StoneHub/skills
/plugin install promo-video@stonehub-skills
/plugin install android-cli@stonehub-skills
```

Get updates later with `/plugin marketplace update stonehub-skills`.

## Skills

| Plugin | What it does | Needs |
|---|---|---|
| `promo-video` | Builds promo, launch, explainer and social videos in code, with SFX, music and voiceover. | Node + Playwright, ffmpeg, Python 3, and your own `ELEVENLABS_API_KEY` in your shell for voiceover |
| `android-cli` | Android project setup, deploys, SDK management and diagnostics. | The `android` CLI and Android SDK |

## Adding a skill

1. Make `plugins/<name>/skills/<name>/SKILL.md` (plus any `references/`, `scripts/`, `assets/`).
2. Add `plugins/<name>/.claude-plugin/plugin.json` (copy an existing one).
3. Add an entry to `.claude-plugin/marketplace.json`.
4. Run `claude plugin validate .`, then commit and push.

Never commit API keys. Scripts should read them from environment variables.
