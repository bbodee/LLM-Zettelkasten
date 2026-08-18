# T-10 — Skill: `zk-recall`

**Size:** M · **Depends on:** T-05, T-07 (T-09 for a green script layer) · **Status:** todo
**Binds:** SPEC §2, §7.1, §8.1 · D-008, D-011, D-013, D-016, D-020, D-021, D-025, D-032

D-008's boundary. Scripts are verified, so every failure from here is a **skill** failure
— that separation is the reason for the ordering and must not be blurred by touching
script code to make a skill behave.

*Dependency added 2026-08-18 by the plan audit.* The T-07 edge was undeclared. The
scaffold lints its charter (problem.md, `/zk:recall` step: "then lint it"), and the
charter section codes ZK018, ZK021, and ZK022 are `structure` layer. The edge holds
regardless of how P-35 is verdicted; P-35 only strengthens it from "lint runs" to "lint
clean on the first pass".

## Interface contract

`skills/zk-recall/SKILL.md`

```yaml
---
name: zk-recall
description: >
  Loads a project's accumulated context from the zk vault — charter, decisions,
  recent logs, related topics — and scaffolds the project if it does not exist yet.
  Use at session start on a known project, when the user asks to load context or
  what is known about a project, and on /zk:recall.
---
```

Body under 200 lines. Scripts referenced by relative path and **executed, never pasted
inline**. Description states what it does **and** when to trigger, phrased assertively —
undertriggering is the failure mode.

## Contract

1. Run `zk_recall.py <slug>`.
2. **Read the bundle. Do not dump it back at the user.**
3. Confirm loaded scope in **one line** — `Loaded game-x: charter, 4 decisions, 5 logs,
   2 topics`.
4. Branch on the script's exit and message. **Never reimplement the state check** —
   `resolve_project` is the single source (D-020).

| State | Behaviour |
|---|---|
| `CHARTED` | proceed |
| `UNCHARTED` | name the missing `project.md`; offer to scaffold the charter |
| `ABSENT` | list known slugs; offer to scaffold a new project by brief interview, then lint it |

## Behaviour that must be exact

- **Slug normalization happens upstream, in conversation** (D-025). A user who types
  `game_x` is offered `game-x` **before anything is created**. The ZK031 lint error is the
  backstop, not the interface.
- **The scaffold writes exactly one file**: `projects/<slug>/project.md` (D-021).
  No `decisions.md`, no `log/`, no stubs, no placeholders. Their absence is never an
  error, and they are created on first write.
- **The interview fills all three required sections** — `## Stack`, `## Conventions`,
  `## Current state` — because §7.1 requires them non-empty and they are filled at
  creation. `## Constraints` and `## Glossary` are **omitted entirely** when unused;
  present-but-empty is an error.
- **The charter uses the closed H2 vocabulary and no other heading.** `## Tech Stack`
  beside `## Stack` is the exact failure D-011 exists to prevent, and it is a warning not
  an error precisely because the skill is expected to get this right.
- **`summary:` is drafted dense at write time** — state what the project is and what it
  is for, name concrete nouns. It is the note's retrieval surface, and a vague one fails
  silently by simply not participating in recall.
- **The summary must add retrieval information beyond what the heading and filename
  already carry** (D-037's routed intent — the check was dropped as semantic and lives
  here now).
- **Run `zk_lint.py` on the scaffolded charter** and **act on errors, mention warnings**
  (D-039). Never the reverse, never both alike — a skill told to resolve every complaint
  rewrites correct content to satisfy an approximate check.
- **Never write into `private/`.** If the user says content is sensitive, tell them to
  place it there themselves and record at most a pointer-free stub elsewhere.
- Scaffolding is the skill's job; **vault init is not** (D-061). `--init` is zero-judgment
  and maximal-consequence, which is the script rung's profile. If no vault is configured,
  surface the script's message naming `zk_config.py --init` rather than acting.

## Definition of done

- SKILL.md exists, under 200 lines, frontmatter valid, scripts referenced by relative
  path.
- Triggers from `/zk:recall <slug>` in a live session. **This can only be validated by
  live triggering** — that is D-008's stated reason for sequencing skills after scripts.
- All three states exercised live against a real vault: CHARTED loads; UNCHARTED offers
  the charter and names the missing file; ABSENT lists slugs and interviews.
- A scaffolded charter lints **clean** on the first pass.
- The confirmation line is one line and the bundle is not echoed.
- `game_x` typed by the user results in `game-x` being offered before creation.
- **AC-5 (half)**: installs into `.claude/skills/` and triggers from its slash command.

## Contract deviations

*(record here during execution — none yet)*
