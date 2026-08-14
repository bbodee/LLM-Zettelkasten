# CLAUDE.md — LLM-Zettelkasten (`zk`)

Constitution for work **on this repo**. Not the vault's per-project CLAUDE.md.

**Structure lives in [architecture.md](architecture.md)** — repo layout, script and
skill responsibilities, vault schema. Read it before creating files or deciding where
something goes. This file is rules only.

## What this is

A Python CLI + two Agent Skills managing an Obsidian vault as cross-session memory for
Claude Code. **Skills + slash commands with bundled scripts. No MCP server.**

Greenfield rebuild of `claude-zettelkasten-librarian`. The old repo is reference only;
the old vault becomes a read-only `archive/` — no migration.

State: **planning phase.** Only docs exist.

## Non-negotiables (settled — do not relitigate)

From [docs/problem.md](docs/problem.md) §"Design decisions" and [docs/decisions.md](docs/decisions.md):

1. Skills-first, no MCP. Scripts are deterministic; skills orchestrate.
2. **v1 = exactly two skills: `zk-recall` and `zk-log`.** Index and lint are scripts
   called by `zk-log`, not user-facing skills.
3. Vault is machine-first. Optimize for predictable paths and dense frontmatter, not
   human link-walking or serendipity.
4. Project-centric structure, not flat zettelkasten.
5. Privacy = location, not a flag. `private/` directory, enforced by script exclusion
   **and** a Claude Code deny rule. This gates what enters context, not what reaches
   Anthropic — anything Claude reads is sent.
6. Directive-style bodies. Terse bullets, no paragraph over two sentences — in vault
   notes and in repo docs alike. Lint-enforced at write time.
7. Fresh vault; old one untouched in `archive/`.
8. Deferrals live in `enhancements.md`, never `decisions.md` (D-005).
9. Vault decision entries get `D-NNN` IDs; the only permitted amendment to an old entry
   is an appended `superseded-by: D-NNN (YYYY-MM-DD)` line (D-002).
10. `summary:` is retrieval-critical — dense at draft time, mechanically backstopped by
    lint (D-003).
11. Read-before-write: never update `project.md` or an existing `topics/` note without
    reading the current version first; never duplicate an existing section (D-004).

## Scope fence

**Authoritative list: [docs/problem.md](docs/problem.md) §"Out of scope for v1".** Read it before
proposing or building anything not already in [architecture.md](architecture.md).

Anything on that list is not built in v1 — not as a stub, not as a flag, not "while
we're in here." An out-of-scope idea that surfaces during work goes to
`docs/enhancements.md` and the work continues. Revisit at the ~20-log checkpoint.

## Where to record what

| Kind of thing | Goes in |
|---|---|
| Durable choice that binds future work | `docs/decisions.md`, new `D-NNN` |
| Deferral (has a revisit condition) | `docs/enhancements.md` with `trigger:` |
| Out-of-scope idea worth keeping | `docs/enhancements.md`, no trigger |
| Reversal of an earlier choice | New `D-NNN` **and** `superseded-by:` on the old |

Both files are append-only. IDs are sequential, unique per file, never reassigned. A
fired trigger graduates via a new decision entry or is consciously re-parked.

## Script constraints

- **Python 3.11+, stdlib + `pyyaml` only** at runtime. A new runtime dependency requires
  a decision entry. Test-only dependencies (pytest) are exempt.
- Interpreter is not on PATH: `C:\Users\bbodee\AppData\Local\anaconda3\python.exe`.
- **Windows and POSIX both.** `pathlib` throughout — no `os.path` string joins, no
  hardcoded separators. The real vault lives under OneDrive on Windows (spaces in path).
- Every script runs standalone from the CLI so a non-Claude agent can drive the vault
  with zero changes. Skills invoke scripts; they never reimplement script logic.
- **`zk_read.py` is the single chokepoint for `private/` and `archive/` exclusion.** No
  other script may walk the vault directly.
- Nonzero exit + actionable message on failure (unknown project slug → list valid slugs).
- Never write into `private/`. If the user says content is sensitive, tell them to place
  it there themselves and record only a pointer-free stub.

## Task and commit discipline

- **Before ending any task:** update `plan.md` status, append decisions to
  `decisions.md`, note contract deviations in the task file.
- **pytest green before any commit to `zk/`.**

## Open questions

Ask before building past them:

- Dev/test vault path vs. the real OneDrive vault.
- Packaging: standalone repo the user symlinks/installs (current default) vs.
  marketplace-style plugin dir vs. `.claude/skills/` per project.
