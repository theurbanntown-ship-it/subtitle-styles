# subtitle-styles (shared Claude Code skill)

> **Just want it?** Paste this repo's link into Claude Code and say **"install this skill"**. Claude does the rest.

## Instructions for Claude (when a user asks you to install this skill from this link)
1. Clone it into the user's personal skills folder (create `~/.claude/skills` if needed):
   `git clone https://github.com/theurbanntown-ship-it/subtitle-styles.git ~/.claude/skills/subtitle-styles`
   If it's already there, run `git -C ~/.claude/skills/subtitle-styles pull --rebase --autostash` instead.
   This repo is private: if the clone asks for sign-in or says "not found", the user must accept their collaborator
   invite (https://github.com/theurbanntown-ship-it/subtitle-styles/invitations) and sign in to GitHub when Git asks.
2. Check the tools: `python ~/.claude/skills/subtitle-styles/scripts/fontkit.py`. If FFmpeg is missing, help the user
   install the "full" build (Windows: `winget install Gyan.FFmpeg`; macOS: `brew install ffmpeg`). If Pillow is missing:
   `pip install pillow`. Missing SF Pro / Helvetica fonts are fine (free Inter is used).
3. Optional, for word timings: put a whisper model (`ggml-large-v3.bin` or `ggml-small.en.bin`, from
   https://huggingface.co/ggerganov/whisper.cpp) in `~/.claude/skills/subtitle-styles/models/`. Ask before downloading (it's large).
4. Tell the user it's installed and that saying **"subtitle"** shows the style picker. The skill starts working in their
   next Claude Code session (or after they restart the current one).

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
