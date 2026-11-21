# Reelio

Daily faceless car explainers (Telugu narration, Tenglish captions, 3D visuals) for YouTube Shorts and Instagram Reels, with you approving each step from Telegram.

## How a day works

| Step | What happens | You do |
|---|---|---|
| 1. Ideas | At 9 am IST the AI sends 5 topics to Telegram, scored on hook, curiosity, 3D fit and shareability | Reply `1`–`5` |
| 2. Script | The AI writes a beat-by-beat Telugu script with the viral formula (3-second hook, open loop, step-by-step payoff, comment CTA), swipe-away risks and fact sources | Reply `ok`, or type changes |
| 3. Video | ElevenLabs reads it; word timings drive captions and scene cuts; the 3D template renders it; music is ducked under the voice | Watch the preview on Telegram |
| 4. Publish | Uploads to YouTube Shorts | Reply `publish`, or `redo <changes>` |

Other commands: `/ideas` (start now), `/status`, `/cancel`.

GitHub Actions checks Telegram every 30 minutes from 7:30 am to midnight IST, so replies are picked up within half an hour. To run a step immediately, open **Actions → reelio → Run workflow**.

## One-time setup

1. **Telegram bot**: in Telegram, message `@BotFather`, send `/newbot`, and copy the token. Send any message to your new bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser and copy `"chat":{"id": ...}`.
2. **AI key**: the default is Gemini. Get a free key at aistudio.google.com and save it as `GEMINI_API_KEY`. To use Claude instead, set `llm.provider: "claude"` in `config.yaml` and add `ANTHROPIC_API_KEY` (billed separately from a Claude Pro plan).
3. **ElevenLabs API key**: Profile → API keys. Telugu needs the `eleven_v4` or `eleven_v3` model (already set in `config.yaml`). Posting commercially needs a paid plan (Starter or above).
4. **Add secrets**: in this repo, go to Settings → Secrets and variables → Actions → New repository secret:
   - `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY` if you use Claude)
   - `ELEVENLABS_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - optional, for auto-posting: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`
5. Edit `config.yaml`: your handle, series name, voice, posting hour.
6. Go to Actions → reelio → **Run workflow** to test. Then send `/ideas` to your bot.

## Try it locally (no API keys needed)

```bash
pip install -r requirements.txt && npm install && npx playwright install chromium
python scripts/dry_run.py --stills 2,20,40     # a few frames
python scripts/dry_run.py                      # full silent video from samples/abs_te.json
```

## Files

- `reelio/prompts.py`: the idea and script prompts. This is where you tune the channel's style.
- `reelio/tick.py`: the Telegram state machine (state lives in `state/state.json`).
- `reelio/voice.py`: ElevenLabs narration and word timings.
- `reelio/produce.py`: rendering, music and the final mix.
- `template/index.html`: the 3D scene library and on-screen template.
- `template/render.js`: renders the template frame by frame.

## Known limits (next steps)

- The 3D scene library covers brakes, safety and driving physics only (see `SCENES` in `prompts.py`). New topics such as turbos or engines need new scenes added to `template/index.html`.
- Instagram auto-posting isn't built yet. Download the video from Telegram and post it by hand.
- Videos are stored as prerelease assets on this repo's Releases page.
- Actions usage is about 1,000 to 1,500 minutes a month, within the 2,000 free minutes for private repos.
