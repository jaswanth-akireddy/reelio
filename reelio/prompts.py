"""Prompts for the idea and script stages. Edit these to change the channel's voice."""

SCENES = {
    "wheel_closeup": "Close-up of a front wheel and brake caliper, caliper glowing; camera pulls back to reveal the car. Great for hooks.",
    "drive_drone": "Drone shot following the car on a tree-lined Indian road. Neutral; use for intros and context.",
    "brake_skid": "Car brakes hard WITHOUT help: wheels lock, skid marks, front wheels turned but car slides straight into a barrier.",
    "brake_swerve": "Same emergency stop but the car keeps steering and swerves around the barrier into the other lane.",
    "xray_orbit": "X-ray view of the whole car on a blueprint grid; wheel speed sensors and wires to a computer (ECU) glow.",
    "xray_brakes": "X-ray close-up of the front wheel, brake line, hydraulic unit with valves and pump; brake pressure pulses.",
    "xray_cabin": "X-ray side view of the driver's footwell; brake pedal vibrating, brake lines pulsing.",
    "fact_card": "Darkened background with a vertical timeline of up to 3 big facts (a year, a number) - each beat in this scene can add one card.",
    "hero_cta": "Hero shot of the car; the last beat shows a COMMENT button then the follow end card. Always the final scene.",
}
TARGETS = ["roof", "wheel_front", "wheel_rear", "caliper", "sensor", "tone_ring", "ecu", "valve", "pump",
           "brake_line", "pedal", "headlight", "taillight", "barrier", "skid"]

FORMULA = """Proven short-form formula (from a viral Telugu explainer reel):
1. HOOK (0-3 s): a surprising number or claim + the subject, e.g. "15 times a second" / "1000s of crores". No greetings, no "hi guys".
2. CURIOSITY: "Meeku thelusaa?" style question + a superlative or stake.
3. OPEN LOOP: a full-screen "WHY?" / "HOW?" moment the viewer needs answered.
4. PROBLEM: show what goes wrong without the thing.
5. SOLUTION step by step, one idea per beat, each beat visual.
6. NUMBERS: 1-3 concrete facts (years, counts) as cards.
7. PAYOFF: what it means for the viewer in real life.
8. CTA: ask an opinion question to drive comments, then follow, under the series name.
Re-hook every 8-10 seconds (new visual, new number, or a mini-question). Keep sentences short and spoken."""


def ideas_prompt(cfg, recent_topics):
    ch = cfg["channel"]
    return f"""You plan a faceless YouTube Shorts / Instagram Reels channel about cars.
Language: {ch['language']} narration. Audience: {ch['audience']}.

The video engine can only show these 3D scenes:
{chr(10).join(f'- {k}: {v}' for k, v in SCENES.items())}

Suggest 5 topics that can be explained convincingly with ONLY these scenes (brakes, braking, grip, safety tech,
driving physics, safety laws and history work well; engines or interiors do not yet).
Avoid these recent topics: {', '.join(recent_topics) or 'none'}.

{FORMULA}

Score each idea 1-10 on: hook (how hard the first 3 seconds stop the scroll), curiosity (how much a typical viewer
wants the answer), fit_3d (how well the scenes above can show it), shareability (would someone send it to a friend).

Reply with ONLY JSON:
{{"ideas":[{{"topic":"short English name","angle":"the specific angle","hook_line_en":"first spoken line in English",
"scores":{{"hook":0,"curiosity":0,"fit_3d":0,"shareability":0}},"why":"one sentence"}}]}}"""


def script_prompt(cfg, idea, feedback=None, previous=None):
    ch, v = cfg["channel"], cfg["video"]
    words_target = int(v["target_seconds"] * 2.3)
    base = f"""Write a {v['target_seconds']}-second vertical explainer video script.
Topic: {idea['topic']} - {idea.get('angle', '')}
Narration: natural spoken {ch['language']}, friendly, like explaining to a friend; keep common English car words
(ABS, brake, sensor) in English as people say them. About {words_target} words in total.
Captions: {ch['caption_style']}.
Audience: {ch['audience']}.

{FORMULA}

Available scenes (consecutive beats with the same scene share one shot; use 5-9 scenes; last scene must be hero_cta):
{chr(10).join(f'- {k}: {v2}' for k, v2 in SCENES.items())}
Label targets (a yellow tag pointing at a part): {', '.join(TARGETS)}.
Label kinds: "" (yellow), "red" (bad / warning), "green" (good).

Facts: only state facts you are sure of. Use web search to verify every number, year and law you include,
and list each one with its source URL.

Reply with ONLY JSON in this shape:
{{
 "topic": "...",
 "youtube_title": "under 70 chars, curiosity-driven, may mix Telugu and English, ends with #Shorts",
 "description": "2-3 lines + hashtags",
 "hook_score": 1-10, "predicted_retention_risks": ["where viewers may swipe and why"],
 "facts": [{{"claim": "...", "source": "https://..."}}],
 "beats": [
  {{"scene": "wheel_closeup",
    "words": [["తెలుగు పదం", "roman"], ...],   // every spoken word: native script for the voice, Romanized for captions, 1:1
    "title": {{"text": "UP TO {{#15}}× A SECOND", "sub": "brake pulses", "style": ""}},  // English, UPPERCASE, max 4 words; {{..}} = yellow highlight; {{#N}} = count-up number; style "big" for one-word moments like WHY?
    "label": {{"text": "BRAKE CALIPER", "kind": "", "target": "caliper"}},   // optional
    "card": {{"big": "1978", "text": "first in a production car"}},           // only in fact_card scenes
    "retention": "why this beat keeps them watching"}}
 ]
}}
Each beat is one sentence (4-14 words). Give every beat a title."""
    if previous:
        import json
        base += f"\n\nHere is the previous draft:\n{json.dumps(previous, ensure_ascii=False)}\n\nRevise it with this feedback from the channel owner:\n{feedback}"
    return base
