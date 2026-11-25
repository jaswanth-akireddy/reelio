"""The channel's writing brain. Ideas -> hook lab -> script -> self-review.

Everything the AI is told about hooks, retention and style lives here. Edit this file to change the channel's voice.
Research behind it (Nov 2026): 30-50% of viewers leave in seconds 1-3, another 15-25% by second 10; educational Shorts
can hold 85%+ when every second earns its place; 60-80% start on mute; a visual change every 1.5-2 s holds attention;
endings that loop into the opening lift rewatches. Sources are listed in docs/SCRIPT_GUIDE.md.
"""
import json

SCENES = {
    "wheel_closeup": "Close-up of a front wheel and brake caliper, caliper glowing; camera pulls back to reveal the car. Most striking opening frame.",
    "drive_drone": "Drone shot following the car on a tree-lined Indian road. Calm; use only for context, never to open.",
    "brake_skid": "Car brakes hard WITHOUT help: wheels lock, skid marks, front wheels turned but car slides straight into a barrier. Very dramatic.",
    "brake_swerve": "Same emergency stop but the car keeps steering and swerves around the barrier into the other lane. The 'payoff' visual.",
    "xray_orbit": "X-ray view of the whole car on a blueprint grid; wheel speed sensors and wires to a computer (ECU) glow.",
    "xray_brakes": "X-ray close-up of the front wheel, brake line, hydraulic unit with valves and pump; brake pressure pulses.",
    "xray_cabin": "X-ray side view of the driver's footwell; brake pedal vibrating, brake lines pulsing.",
    "fact_card": "Darkened background with a vertical timeline of up to 3 big facts (a year, a number). Each beat in this scene can add one card.",
    "hero_cta": "Hero shot of the car; the last beat shows a COMMENT button then the follow end card. Always the final scene.",
}
TARGETS = ["roof", "wheel_front", "wheel_rear", "caliper", "sensor", "tone_ring", "ecu", "valve", "pump",
           "brake_line", "pedal", "headlight", "taillight", "barrier", "skid"]

# ---------------------------------------------------------------------------------------------------------------
GUIDE = """
=== THE REELIO SCRIPT STANDARD (premium Telugu car explainers) ===

WHO WE ARE: the smartest friend in the group who happens to know cars - confident, warm, a bit cheeky, never a
lecturer, never a newsreader. The viewer should feel "I didn't know that... and now I'll tell my friends."

THE FIRST 3 SECONDS DECIDE EVERYTHING (30-50% of viewers leave here)
- The first spoken word lands at 0.3 s. No greeting, no "friends", no "ee video lo", no channel name, no setup.
- Open with the single most surprising, specific thing in the whole video. Never save the best line for later.
- ONE promise only. By second 3 the viewer must know exactly what they will get.
- It must work on MUTE: the opening title (max 3 words) + caption carry the hook alone.
- The opening scene must be the most visually striking one (wheel_closeup or brake_skid - never drive_drone).
- Hook types (pick the strongest for the topic):
  1. Shocking number  - "Mee car brake sekanuku 15 saarlu kodutundi." (a precise, surprising figure)
  2. Myth bust        - "Brake pump cheyyamani evaru cheppaaru? Adi ABS car lo wrong." (challenges a belief they hold)
  3. Danger / stakes  - "Ee mistake valla ghat road lo brakes pani cheyyavu." (a real risk to THEM)
  4. Curiosity gap    - "Mee car lo oka computer, mee kaalu kanna fast ga brake veestundi." (result shown, method hidden)
  5. Visual shock     - the frame does the work; the line names what's wrong ("Steering tippinaa car tiragaledu. Enduku?")
  6. Direct question  - only if the viewer CAN'T answer it in their head.
- Never over-promise: the hook's promise must be paid off clearly before the CTA.

STRUCTURE (target 40-50 s; ~95-120 spoken words; 14-20 beats)
  0-3 s   HOOK      - one line, one promise.
  3-8 s   STAKES    - why it matters to the viewer (their car, their family, Indian roads, money, safety).
  8-35 s  PAYOFF    - the explanation as a chain of "and then... so... but..." - each beat ONE idea, each beat a
                      new visual. Plant a re-hook every 8-10 s: a mini-question, a "but here's the twist",
                      a number, or a contrast ("ABS lekapothe... ABS unte...").
  35-45 s PUNCHLINE - the satisfying 'aha' + one practical takeaway they can use tomorrow.
  last 3s LOOP+CTA  - one short comment question that ALSO flows back into the opening line, so the video loops.
                      No "like, share, subscribe". No "thanks for watching".

RETENTION RULES
- A visual change every ~2 s: every beat gets its own title; most beats get a label; scenes change every 2-4 beats.
- Each beat is ONE spoken sentence of 3-9 words. Short. Spoken. Punchy. No beat over 9 words.
- Specific beats generic: "100 km/h lo", "Swift, Creta, Thar", "Tirumala ghat road", "monsoon lo NH-65",
  "rendu seconds lo 28 metres" - concrete numbers, real Indian places, cars people actually own.
- Explain with everyday Telugu analogies (a gas stove knob, a scooter on wet road, a cricket ball, a pressure cooker).
- Contrast is the engine: without vs with, myth vs truth, what you feel vs what really happens.
- Cut every filler word, every adjective that doesn't add information, every "basically", "actually", "so friends".
- No dead air: never two calm beats in a row.

LANGUAGE
- Natural Hyderabad/Andhra spoken Telugu, code-mixed like real people talk: English for car terms
  (brake, ABS, sensor, steering, wheel, lock, pedal), Telugu for everything else.
- Captions: Romanized Telugu (Tenglish) exactly as spoken, e.g. "Meeku thelusaa?". One caption word per spoken word.
- Voice text: Telugu script for Telugu words, Latin letters for English words (ABS, Mercedes) so the voice says them right.
- Titles on screen: English, UPPERCASE, MAX 3 WORDS, no hyphenated words that may wrap. One {highlight}.
- Tone markers welcome: "mama" at most once, "asalu", "kaani", "chudandi", "idhe twist".

FACTS (premium = trustworthy)
- Every number, year, law and claim must be verified with web search, with a real source URL.
- If a fact is uncertain, soften it ("daadaapu", "up to") or drop it. Never invent statistics.
- No dangerous advice. Driving tips must match manufacturer/road-safety guidance.

BANNED: greetings; "ee video lo"; "subscribe cheyyandi" in the first 40 s; "like share subscribe"; "friends";
"chala important"; vague hype ("amazing", "mind-blowing") without a fact behind it; ending without a payoff.
"""

FORMAT = """Scenes available (consecutive beats with the same scene share one shot; last scene must be hero_cta):
{scenes}
Label targets (a tag pointing at a part): {targets}. Label kinds: "" (yellow), "red" (bad/warning), "green" (good).
Title syntax: {{..}} highlights one word in yellow; {{#N}} makes a number count up (e.g. "{{#15}}× PER SECOND"); style "big" for one-word moments like WHY?"""


def _fmt():
    return FORMAT.format(scenes="\n".join(f"- {k}: {v}" for k, v in SCENES.items()), targets=", ".join(TARGETS))


def ideas_prompt(cfg, recent_topics):
    ch = cfg["channel"]
    return f"""You are the head of content for a premium faceless Telugu car-explainer channel (YouTube Shorts + Instagram Reels).
Audience: {ch['audience']}.
{GUIDE}
The video engine can only show these 3D scenes:
{chr(10).join(f'- {k}: {v}' for k, v in SCENES.items())}

Use web search to find what Telugu/Indian car viewers are curious or worried about right now (new safety rules, viral
crashes, myths, monsoon driving, popular cars). Then suggest 5 topics that:
- can be shown convincingly with ONLY these scenes (brakes, grip, skids, safety tech, driving physics, safety laws/history),
- have a genuinely surprising core fact (if a friend already knows it, drop it),
- matter to the viewer personally (their safety, money, car, family),
- avoid these recent topics: {', '.join(recent_topics) or 'none'}.

Score each 1-10 (be harsh, 8+ means you'd bet on it): hook (scroll-stopping first line), curiosity (need to know),
fit_3d (our scenes show it well), shareability (they'd send it to a friend or the family group).

Reply with ONLY JSON:
{{"ideas":[{{"topic":"short English name","angle":"the specific surprising angle","hook_line_en":"the first spoken line, in English",
"scores":{{"hook":0,"curiosity":0,"fit_3d":0,"shareability":0}},"why":"one sentence: why a Telugu car fan would stop scrolling"}}]}}"""


def hook_lab_prompt(cfg, idea):
    """Step 1: research + 8 competing hooks + a beat outline."""
    v = cfg["video"]
    return f"""You are the lead writer of a premium Telugu car-explainer channel. Today's topic:
{idea['topic']} - {idea.get('angle', '')}
Audience: {cfg['channel']['audience']}. Target length {v['target_seconds']} s.
{GUIDE}
{_fmt()}

STEP 1 - RESEARCH. Use web search. Collect 4-8 verified facts (numbers, years, laws, mechanisms) with source URLs.
Find the single most surprising true fact - that is the seed of the hook.

STEP 2 - HOOK LAB. Write 8 different opening lines using at least 5 different hook types from the standard.
Score each 1-10 on: stop (would a scrolling Telugu viewer freeze?), clarity (understood in 2 s on mute?),
curiosity (must they keep watching?), truth (fully backed by the facts?). Be ruthless. Pick the best.

STEP 3 - OUTLINE. 14-20 beats following the structure (hook, stakes, payoff chain with re-hooks every 8-10 s,
punchline + takeaway, loop+CTA). For each beat: its job, the one idea, the scene, and the visual change.
The final CTA line must be a question that flows back into the hook line.

Reply with ONLY JSON:
{{"facts":[{{"claim":"...","source":"https://..."}}],
"hooks":[{{"type":"shocking number|myth bust|danger|curiosity gap|visual shock|direct question","line_en":"...","line_tenglish":"...",
  "opening_scene":"...","scores":{{"stop":0,"clarity":0,"curiosity":0,"truth":0}}}}],
"chosen":0, "promise":"what the viewer will know by the end", "aha":"the punchline insight", "takeaway":"the practical tip",
"outline":[{{"job":"hook|stakes|payoff|rehook|punchline|takeaway|cta","idea":"...","scene":"...","visual":"what changes on screen"}}]}}"""


def script_prompt(cfg, idea, plan=None, feedback=None, previous=None):
    """Step 2+3: write from the plan, then self-review against the standard and rewrite before answering."""
    ch, v = cfg["channel"], cfg["video"]
    if previous:
        task = (f"Here is the current script:\n{json.dumps(previous, ensure_ascii=False)}\n\n"
                f"Revise it with this feedback from the channel owner (their word is final):\n{feedback}\n"
                f"Keep everything that already works.")
    else:
        task = (f"Here is the approved plan from the hook lab:\n{json.dumps(plan, ensure_ascii=False)}\n\n"
                "Write the script from this plan, opening with the chosen hook.")
    return f"""You are the lead writer of a premium Telugu car-explainer channel. Topic: {idea['topic']} - {idea.get('angle', '')}
Audience: {ch['audience']}. Target {v['target_seconds']} s.
{GUIDE}
{_fmt()}

{task}

Before answering, do a hard self-review and REWRITE until every check passes:
[ ] first beat: hook line <= 9 words, the most surprising fact, striking opening scene, works on mute
[ ] the hook's promise is clearly paid off before the CTA
[ ] stakes for the viewer within the first 8 s
[ ] a re-hook at least every 8-10 s (count them)
[ ] every beat <= 9 spoken words, one idea, its own title (max 3 words) - no title can wrap badly
[ ] no banned phrases, no filler, no two calm beats in a row
[ ] at least two concrete Indian specifics (a road, a city, a car people own, a real number)
[ ] last line is a comment question that loops back to the opening
[ ] 95-120 spoken words in total; every fact verified (use web search for anything new)

Reply with ONLY JSON:
{{
 "topic": "...",
 "youtube_title": "under 60 chars; curiosity + specificity; Telugu+English mix ok; ends with #Shorts",
 "description": "2 lines that add value + 4-6 relevant hashtags",
 "hook_score": 1-10,
 "scorecard": {{"hook":0,"stakes":0,"rehooks":0,"payoff":0,"specificity":0,"loop":0}},
 "predicted_retention_risks": ["the 1-2 weakest moments and why"],
 "facts": [{{"claim": "...", "source": "https://..."}}],
 "beats": [
  {{"scene": "wheel_closeup",
    "words": [["మీ", "Mee"], ["కారు", "car"]],
    "title": {{"text": "UP TO {{#15}}× A SECOND", "sub": "brake pulses", "style": ""}},
    "label": {{"text": "BRAKE CALIPER", "kind": "", "target": "caliper"}},
    "card": {{"big": "1978", "text": "first in a production car"}},
    "retention": "the job of this beat"}}
 ]
}}
"words": every spoken word, in order, as [voice_text, caption_text] (voice: Telugu script, English words in Latin letters;
caption: Romanized Telugu). "label" optional; "card" only in fact_card scenes."""
