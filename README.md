# subtitle-styles (shared Claude Code skill)

Saved caption styles (Sub 1, Sub 2, …) that Claude burns onto an edit or exports as a transparent layer for Premiere.
Say **"subtitle"** to Claude to see an animated picker of every style, then click one.

## Install (once)
1. Install [Git](https://git-scm.com), [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) (the "full" build, it has whisper) and Python with Pillow (`pip install pillow`).
2. Clone this repo into your Claude skills folder:
   ```bash
   git clone https://github.com/theurbanntown-ship-it/subtitle-styles.git ~/.claude/skills/subtitle-styles
   ```
3. Optional: put a whisper model (`ggml-large-v3.bin`, from https://huggingface.co/ggerganov/whisper.cpp) in
   `~/.claude/skills/subtitle-styles/models/`, and install SF Pro / Helvetica Neue if you have them (else free Inter is used).
4. Check: `python ~/.claude/skills/subtitle-styles/scripts/fontkit.py`

## Staying in sync
Claude pulls the latest styles every time it uses the skill, and pushes every new or changed style straight back,
so whatever you or your collaborators add shows up for everyone.
