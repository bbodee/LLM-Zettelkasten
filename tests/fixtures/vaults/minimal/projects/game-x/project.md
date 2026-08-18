---
type: project
project: game-x
tags: [engine, save-system]
status: active
updated: 2026-08-14
summary: 2D engine sandbox; save format is versioned JSON with the v1 loader kept until 0.9
---

## Stack
- Python 3.14, `pygame-ce`, no external asset pipeline.
- Saves live at `src/save/format.py`.

## Conventions
- `pathlib` throughout; every write passes `newline="\n"`.
- One module per subsystem under `src/`.

## Current state
- Save/load round-trips v2. Tilemap chunking is next.
