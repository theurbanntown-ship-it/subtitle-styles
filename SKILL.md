---
name: subtitle-styles
description: Burn or layer the user's saved subtitle styles onto a finished edit (UGC ads, reels). Use when the user says just "subtitle"/"subtitles"/"captions" (show the style gallery first), asks for subtitles or captions in a saved style ("Sub No. 1", "sub 1"), wants captions like a reference reel, or wants a transparent caption layer (.mov) for Premiere.
---

# Subtitle styles

Saved styles, by the name the user gives them. Apply the one they name.

**SHARED SKILL, KEPT IN SYNC THROUGH GIT (user's rule, 2026-11-16).** This folder is a git clone shared with
collaborators; anyone's new or changed style must reach everyone.
- **Before using the skill** (showing the picker, applying or editing a style): `git -C <this folder> pull --rebase --autostash`
  (quietly; if offline or it fails, say so in one line and carry on with the local copy).
- **After saving or changing a style** (script, previews, picker tile, this file): `git -C <this folder> add -A`, commit
  "Add Sub N (<name>)" or "Update Sub N: <what>", then `git push`. If the push is rejected: pull --rebase and push again.
  If someone else took the same Sub number meanwhile, renumber yours to the next free number (files, picker tile,
  sendPrompt text, this file), then push. Tell the user it's synced.
- Never commit licensed fonts (SF Pro, Helvetica Neue; .gitignore blocks them), whisper models, or client videos.
- Setup check on a new computer: `python -I scripts/fontkit.py` (missing licensed fonts fall back to free Inter / Playfair).
- Word timings for any style: `python -I scripts/words.py edit.mp4 words.txt`.

**When the user says "subtitle" / "subtitles" / "captions" without naming a style (user's rule, 2026-11-16):** show the
**style picker right in chat**: read `previews/picker.html` and pass its contents to the `show_widget` tool
(title `subtitle_style_picker`). It's a grid of tiles, each showing a looping animated sample of one style; clicking a
tile sends "Go with Sub N". If the user wants to see it on real footage, also run `python -I scripts/gallery.py` and send
`previews/gallery.jpg`. Never pick for them.

**Saving a new style ("save this as sub N"):** after it's approved, also add its preview: 3 frames rendered on a plain
BLACK background (never client footage: the skill is shared; make a black clip with the edit's length and run the style on
it with the same words.txt), cropped `crop=1080:1440:0:240` (move the crop if text is cut) (`ffmpeg -ss <t> -i video -frames:v 1 -vf scale=360:-1`, then `hstack=3`) → `previews/subN.jpg`, a short label
→ `previews/subN.txt` ("Sub N — <look in a few words>", under about 45 characters so it fits), then re-run gallery.py. Add a tile for it to `previews/picker.html`: copy an existing `<button class="sp-tile">`
block, set `sendPrompt('Go with Sub N')`, the label, and a 2-4 word sample animated in that style's fonts, colours and
entrance (add keyframes next to the others; one `4s infinite` cycle, staggered by keyframe percentages, not delays).

## Sub No. 1 (saved 2026-11-16, first used on Perfora Ishaan H1)

The look:
- **Font and colour:** white SF Pro Display. Small words are Semibold 50 (line 1) / 64 (lines 2+). Key words are Bold 98.
- **Spacing:** tracking −4.5%.
- **Glow:** a soft white glow at 55% plus a faint dark shadow.
- **Layout:** lines are left-aligned inside a centred block whose top sits at y 1180 (1080×1920).
- **Animation:** words fade in and rise one at a time as they are spoken.
- **Text rules:** no punctuation. A product name always stays on one card (e.g. "the *Perfora* / Rechargeable Electric / *Toothbrush*").

Steps:
1. Get word timings of the final edit: `python -I scripts/words.py edit.mp4 words.txt` (FFmpeg's whisper filter; one
   `start end word` line per word, in seconds).
2. In a copy of `scripts/sub1_captions.py`, rewrite `PAGES`: one card per line, `/` is a line break, `*word*` marks a key word. The tokens must match the spoken words in order; an assert checks this.
3. Run `python -E -P sub1_captions.py edit.mp4 words.txt out.mov` to get a transparent ProRes 4444 layer for Premiere's top track, or `out.mp4` to burn the captions in.
4. Check a contact sheet of a few caption frames before sending.

Needs: FFmpeg, Python with Pillow, and SF Pro (found by `scripts/fontkit.py`; free Inter is used if it's missing).

## Sub No. 2 "stair stack" (saved 2026-11-16, from an Instagram reel; used on Channel 1 "Can You Drink Seawater" and UGC "Perfora Ishaan H1")

The look:
- **Stair stack:** one word per line, each line slightly overlapping the one above and stepped sideways (STEP list), so a 2-4 word phrase builds into a zig-zag tower; it clears when the next phrase starts.
- **Filler words:** white Helvetica Neue Bold 96, tracking −3%, hard black drop shadow (6,7 px, no blur).
- **Key word (one per phrase):** Playfair Display Bold 170, slate blue #5A76A7, 5 px white edge + soft dark offset shadow.
- **Animation:** each word pops in on its spoken start (scale 1.2 → 1 in 0.1 s). No punctuation.
- **Placement:** default first baseline y 1200; move a phrase into empty space with `@<y>` at the end of its PAGES line (the reference moves captions around the subject).
  Keep captions off mouths and eyes (brushing / close-up shots): drop them lower (`@1450`) or up onto empty wall (`@380`).
- **Text rules:** 2-4 words per phrase, one key word (two allowed on a product card). A product name stays on one card ("the *Perfora* Rechargeable Electric *Toothbrush*"). Numbers keep their commas (26,000).
- **Built in:** frame rate is read from the input (UGC edits are often 25 fps); long key words shrink to fit the width; a small word under a key word gets room for the serif's descenders.
- **Later, if wanted:** three more aesthetic variants were mocked up (A Editorial = Instrument Serif Italic white + even staircase; B Brand = DM Serif Display Italic in the brand colour, left-aligned; C Soft = Fraunces Italic cream, centred, glow; all with Helvetica Medium lowercase small words and a soft blurred shadow). Comparison image is on the original author's machine (Perfora project folder). Not applied; Sub No. 2 stays as above unless the user asks.

Steps: same as Sub No. 1, but with `scripts/sub2_captions.py` (PAGES = one phrase per line, `*word*` = key word, tokens must match the spoken words; an assert checks this). For a Channel 1/2 video, render it caption-free first (`QS='&nocap' node tools/capture.mjs video renders/<name>-nocap.mp4`) and use the project's `data/words.txt`.

## Sub No. 3 "one word + hero stack + animated hook" (saved 2026-11-16, from an Instagram reel; first used on UGC "Perfora Ishaan H1"; "sub 3" = captions AND the hook animation together)

The look:
- **Body:** one spoken word at a time, centred mid-frame (baseline y 1030), white SF Pro Display Bold 128, tracking −3%, soft dark shadow (blur 7, ~65%) so it reads on white walls. Punctuation is kept ("storytelling.", "Lastly,").
- **Hero moments (3-6 per video):** the hook, product name, key numbers and the CTA become a justified stack. Every line is scaled to the same block width (HERO_W 560), so short words get huge, with tight leading, building word by word.
- **Accent:** a hero line wrapped in `*...*` turns gold #F8D24A with an orange glow (numbers, brand name).
- **Animation:** each word fades in and rises 14 px over 0.1 s.
- **Placement:** heroes take `@x,y` (block centre-x, top-y). `BODY_MOVES` shifts body words off faces for given time ranges (e.g. brushing close-ups → y 1480, face filling the frame → y 420 on the wall).
- Not included (per-video motion graphics, not caption style): curved text, tumbling rotated words, hand-drawn boxes.

**Hook animation (`scripts/sub3_hook.py`, the first shot only):** the opening line splits into two justified stacks placed around the subject: one straight (top-right), one tilted about +7° so it rises to the right (lower-left). Word entrances: pop, zoom from tiny with blur, or slide in from the left edge with motion blur. The whole shot slowly zooms out (1.14 → 1.0) with the text locked to it, inside a dark oval vignette. Hand-drawn red doodles (sparkles; the reference used "?") pop above the head one by one and wobble every 3 frames. A sideways whip blur carries it into the next shot. Run it after sub3_captions: `python -E -P sub3_hook.py clean.mp4 sub3_burned.mp4 out.mp4`, and set CUT (first frame of the next shot; a one-shot hook clip = its frame count, so the whip exits into the next clip), STACKS, WORDS and DOODLES per video. `DOODLE_SHAPE = "?"` draws the reference's red hand-drawn question marks (good for "never thought about…" lines) instead of sparkles. Words are keyed by position, so a line may repeat a word ("I"). On white walls, raise the word shadow (alpha ~235, blur 9). Output `out.mp4` = burned in (footage zoom, vignette, footage whip); `out.mov` = transparent ProRes 4444 layer with just the hook text + doodles (zoom and whip applied to the text) for Premiere.

Steps: same as Sub No. 1, with `scripts/sub3_captions.py`. Edit `HEROES` (spoken words in order, `/` = line break) and `BODY_MOVES`; all other words show one at a time automatically. Check a contact sheet for words on mouths/eyes before sending.

## Subs 4-9 "phrase cards" (saved 2026-11-16, from a caption-app recording; first used on UGC "Perfora Ishaan H1")

One script, five presets: `python -E -P scripts/sub_cards.py sub4|sub5|sub6|sub7|sub8|sub9 edit.mp4 words.txt out.mp4|out.mov
[--y 1150] [--moves "12.9-15.35:1480,15.35-16.6:420"] [--keys "teeth,properly"]`. Words are grouped into 1-5 word cards
automatically (breaks at punctuation and pauses); key words default to the longest word of 4+ letters per card (numbers always),
or pass `--keys`. `--y` is the block's vertical centre; `--moves` moves it off faces for time ranges. Fonts live in `fonts/`.
- **Sub 4 "Adrian":** SF Pro Bold 66, black text on cream (#FBF3E6) line boxes sized to the full line; each word appears as
  spoken and the spoken word is red (#E0424A). The first card, and any lone key-word card, is a slightly tilted red box with white text.
- **Sub 5 "Nora":** Instrument Serif 96, white, centred, key words italic; each word fades in from a blur. Soft shadow.
- **Sub 6 "Kendrick":** Montserrat Bold 56; line 1 white on a black rounded box, line 2 (or a single line) black on a bright
  green (#2CF018) box tilted −2°; the whole card pops in (0.55 → 1.08 → 1).
- **Sub 7 "Kelly":** SF Pro Bold 62 white + Playfair Display Bold Italic 74 for key words; the card's upcoming words wait at
  35% and light up when spoken. Soft shadow.
- **Sub 8 "Bob":** Mali Bold 86, 1-2 words; white, key words yellow (#FFEC00), a lone key word 1.3× bigger; dim → lit. Soft shadow.
- **Sub 9 "Moxie"** (from a Moxie Beauty UGC reel, 2026-11-16): SF Pro Medium 108, white, all lowercase, punctuation kept;
  1-2 words per line, up to 4 tight lines (leading 0.84) in a ragged right-aligned block; key words SF Pro Semibold Italic in
  lime #E8FB44; each word appears as it's spoken (no fade). Soft shadow.


## Sub No. 10 "yellow key line" (saved 2026-11-20, from an Instagram "how I edit my videos on Claude" reel; first used on UGC "Perfora Two things V14 H1")

The look:
- **Small words:** white Inter Regular (wght 420) 46, tracking −2%. They build up one by one on the line as they are spoken (quick fade-in, 2 frames).
- **Key words:** on their own line, Inter Black (900) 104 in yellow #F3EB57 (sampled from the reference), tracking −6.5% so the letters touch. Each word appears exactly on its spoken start and grows 92% → 100% over 2 frames.
- **Layout:** a card is 1-3 lines (small line, key line, optional small line after). Lines are left-aligned inside a centred block whose top sits at y 1150 (chest height). Tight line stacking. A soft dark shadow (blur 6, ~35%) keeps it readable on light walls. The card clears when the next one starts.
- **Text rules:** no punctuation. A line is either all key words or all small words (an assert checks this). A product name stays on one card ("This is the / *Perfora* / Oscillating Toothbrush"). You may fix misheard words in PAGES (e.g. "IPX7" for a spoken "IP7"); the script prints a note for each.
- Not included: the small Claude logo the reference puts beside some key words (a graphic, not caption style).

Steps: same as Sub No. 1, with `scripts/sub10_captions.py` (PAGES = one card per line, `/` = line break, `*word*` = key word, `@y` at the end of a line moves that card's top to y). Run `python -E -P sub10_captions.py edit.mp4 words.txt out.mp4|out.mov`; the frame rate is read from the input.
