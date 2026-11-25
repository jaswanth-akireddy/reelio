# Reelio script guide: why the prompts say what they say

The AI follows the standard in `reelio/prompts.py` (`GUIDE`). This page records the research behind it (November 2026).

## What the data says

| Finding | Number | What we do about it |
|---|---|---|
| Viewers leave in seconds 1–3 | 30–50% | First word at 0.3 s, no greeting, most surprising fact first |
| Viewers leave in seconds 3–10 if there's no payoff | another 15–25% | Name the stakes for the viewer by second 8 |
| Shorts start on mute | 60–80% | The hook must work as title + caption alone; captions from the first frame |
| Visual change rhythm | every 1.5–2 s (dips above 2.5 s) | 14–20 short beats; each beat gets its own title, most get a label |
| Healthy "viewed vs swiped away" | ~70%+ is strong; under 60% hurts reach | Track it in YouTube Studio for every video |
| Educational / list Shorts | can hold 85–95% average viewed | Keep the explainer dense, 40–50 s |
| Endings that loop into the opening | raise rewatches | The last line is a comment question that flows back into the hook |

These benchmarks come from creator studies and community data; YouTube doesn't publish official thresholds.

## How a script is made

1. **Hook lab:** web research for verified facts, then 8 competing hooks across 6 types, each scored on stop, clarity, curiosity and truth. The best one wins. You see the top 4 on Telegram.
2. **Write:** a 14–20 beat script from the outline (hook → stakes → payoff chain with re-hooks every 8–10 s → punchline + takeaway → loop CTA).
3. **Self-review:** a 9-point checklist. The AI rewrites until it passes, then reports a scorecard.

## After publishing: what to watch

- **Viewed vs swiped away** below 60%: the hook failed. Try a different hook type on the next video.
- **Average % viewed** below 70%: find the drop point. It's usually a calm beat or a slow scene.
- Tell the bot what worked. Its feedback goes into the next revision.

## Sources

- [The YouTube Shorts Retention Curve Playbook (2026)](https://aibrify.com/blog/youtube-shorts-retention-curve-playbook)
- [The First 3 Seconds: Hook Structures That Stop Scroll on Shorts](https://virvid.ai/blog/first-3-seconds-hook-faceless-shorts-2026)
- [Short-Form Video Scripting in 2026: The 3-Second Hook & Retention Blueprint](https://www.grow-it.se/en/resources/short-form-video-scripting-retention-hooks)
- [YouTube Audience Retention 2026](https://socialrails.com/blog/youtube-audience-retention-complete-guide)
