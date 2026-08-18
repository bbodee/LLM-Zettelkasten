---
type: log
project: game-x
tags: [save-system, serialization]
updated: 2026-08-14
summary: Replaced the pickle serializer with versioned JSON; v1 loader stays until 0.9
---

## Done
- Swapped the pickle serializer for versioned JSON at `src/save/format.py`.
- Added `schema_version` to the save header; the loader dispatches on it.

## Next
- Delete the v1 loader once 0.9 ships.
