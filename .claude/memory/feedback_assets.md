---
name: Asset sources workflow
description: How Karel provides downloaded assets and expects them to be handled
type: feedback
---

Downloaded assets are placed in the `sources/` folder at the project root.

**Why:** Karel downloads assets manually; I should pick them up from there and copy to the right game directories.

**How to apply:** When working with new art assets, always check `sources/` first. Copy (don't just reference) needed files to their proper location in the game structure (e.g., `dungeoneer/assets/`). Never use files directly from `sources/` in game code.
