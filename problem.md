# problem.md — LLM-Zettelkasten Rebuild

## Problem statement

Rebuild `claude-zettelkasten-librarian` (a Python CLI managing an Obsidian vault as
cross-session memory for Claude) as a standard Anthropic-workflow project:
**Agent Skills + slash commands with bundled scripts, no MCP server.**

This is a greenfield rebuild. The old repo is reference only. The old vault becomes
a read-only archive; no migration.

## Design decisions (already made — do not relitigate)

1. **Skills-first, no MCP.** Claude Code reads/writes the vault natively. Scripts
   handle deterministic operations; skills orchestrate. Markdown + YAML + Python
   scripts are the LLM-agnostic core; skills are a thin Claude-specific wrapper.
2. **v1 = two skills only: `recall` and `log`.** Index generation and lint are
   scripts invoked automatically by `log`, not user-facing skills. Deferred: xref,
   inbox, plan, synthesize. Do not build them.
3. **Vault is machine-first.** The human does not browse it. Optimize for
   predictable paths, dense frontmatter, and one generated entry point — not
   link-walking or human serendipity.
4. **Project-centric structure**, not classic flat zettelkasten.
5. **Privacy = location, not a flag.** The old `llm_safe: false` frontmatter is
   replaced by a `private/` directory, enforced by (a) script-level exclusion and
   (b) a Claude Code permission deny rule. Understand: this gates what enters
   context, not what reaches Anthropic — anything Claude reads is sent.
6. **Directive-style note bodies by default.** Terse bullets: facts, constraints,
   gotchas, decisions. No narrative prose. Enforced by lint at write time, which
   eliminates the old `zk:compress` command entirely.
7. **Fresh vault.** Old vault mounted/copied to `archive/` untouched.

## Repository layout (deliverable)

```
zk/
├── README.md
├── SPEC.md                      # vault schema spec — single source of truth,
│                                # referenced by both skills
├── scripts/
│   ├── zk_config.py             # locate vault (env var ZK_VAULT or zk.toml)
│   ├── zk_read.py               # note loading, frontmatter parse, private/ filter
│   ├── zk_recall.py             # assemble context bundle for a project
│   ├── zk_index.py              # regenerate index.md from frontmatter
│   └── zk_lint.py               # validate schema + directive style; --fix mode
├── skills/
│   ├── zk-recall/SKILL.md
│   └── zk-log/SKILL.md
└── .claude/
    └── settings.json            # deny rule template for private/
```

Scripts: Python 3.11+, stdlib + `pyyaml` only. Must run on Windows and POSIX
(use `pathlib` throughout; the user's vault lives under OneDrive on Windows).
Every script is independently invocable via CLI (`python -m` or direct) so any
future non-Claude agent can drive the vault with zero changes.

## Vault schema (put full version in SPEC.md)

```
vault/
├── index.md                     # GENERATED — never hand-edited
├── projects/<slug>/
│   ├── project.md               # charter: stack, conventions, current state
│   ├── decisions.md             # append-only ADR-lite entries
│   └── log/YYYY-MM-DD-<topic>.md
├── topics/<slug>.md             # cross-project knowledge
├── private/                     # mirrors projects/ + topics/; never enters context
└── archive/                     # old vault, read-only, ignored by all scripts
```

### Frontmatter — required on every note

```yaml
type: project | topic | log | decision
project: <slug>                  # required for project/log/decision; absent on topic
tags: [lowercase-kebab, ...]
status: active | deprecated
updated: YYYY-MM-DD
summary: one dense line; this is the note's representation in index.md
```

### Body style rules (lint-enforced)

- Bullets and short headers only; no paragraphs > 2 sentences.
- Log notes use fixed sections: `## Done`, `## Decisions`, `## Gotchas`,
  `## Next`. Empty sections omitted.
- Code blocks allowed and encouraged for exact commands/snippets.
- Obsidian `[[wikilinks]]` allowed but never required for retrieval — scripts
  resolve by path/frontmatter, not links.

### index.md format (generated)

Grouped by type, one line per note:
`- projects/game-x/log/2026-08-14-save-system.md — <summary> [tags]`
Sorted by `updated` descending within groups. `private/` and `archive/` never
appear. Include a generation timestamp header.

## Script interfaces

`zk_recall.py <project> [--logs N] [--deep] [--topics tag1,tag2]`
- Emits a single markdown context bundle to stdout:
  1. `index.md` project section, 2. `project.md`, 3. `decisions.md`,
  4. last N logs (default 5, `--deep` = all), 5. topic notes matching the
  project's tags (or explicit `--topics`).
- Hard-excludes `private/` and `archive/` regardless of flags.
- Exit nonzero with a clear message if project slug not found; list valid slugs.

`zk_index.py [--check]`
- Rebuilds `index.md`. `--check` exits nonzero if regeneration would change it
  (usable in git hooks later).

`zk_lint.py [path] [--fix]`
- Validates frontmatter completeness, enum values, date format, filename
  conventions, section structure for logs, prose-density heuristic.
- `--fix` autocorrects mechanical issues (missing `updated`, tag casing);
  reports but never auto-rewrites prose.

`zk_read.py` — shared library, not user-facing. Central place for the
private/archive exclusion so it cannot be bypassed by other scripts.

## Skills

Follow Agent Skills conventions: SKILL.md with `name` + `description`
frontmatter; description states what it does AND when to trigger, phrased
assertively to avoid undertriggering; body < 200 lines; scripts referenced
by relative path, executed not pasted.

### zk-recall (`/zk:recall`)

- Trigger: session start on a known project, "load context", "what do we know
  about <project>", or explicit slash command.
- Behavior: run `zk_recall.py`, read the bundle, confirm loaded scope in one
  line ("Loaded game-x: charter, 4 decisions, 5 logs, 2 topics"). Do not dump
  the bundle back at the user.
- If project unknown: offer to scaffold `projects/<slug>/project.md` by
  interviewing the user briefly (stack, goals, conventions), then lint it.

### zk-log (`/zk:log`)

- Trigger: "log this session", session wrap-up, or explicit slash command.
- Behavior:
  1. Draft the log note from the live conversation using the fixed sections.
     Directive style; capture decisions and gotchas over narrative.
  2. If a durable architectural choice was made, append an entry to
     `decisions.md` (date, decision, why, alternatives rejected — 4 lines max).
  3. If a reusable cross-project insight emerged, write/update a `topics/` note.
  4. Run `zk_lint.py --fix` on everything written; fix any residual complaints.
  5. Run `zk_index.py`.
  6. Report: files written + one-line summary each. Show the user; incorporate
     corrections if offered, then re-lint and re-index.
- Never write into `private/`. If the user says content is sensitive, tell them
  to place it in `private/` themselves and record only a pointer-free stub.

## Claude Code integration

- `.claude/settings.json` template with a `Read` deny rule for
  `<vault>/private/**` and `<vault>/archive/**`. Document that the user must
  merge this into their project or user settings — a template in the repo does
  nothing by itself.
- Per-project `CLAUDE.md` snippet (document in README):
  `At session start, run /zk:recall <project-slug>.`

## Acceptance criteria

1. Fresh vault scaffolds from empty: create dirs, seed `index.md`.
2. `zk_recall.py demo` on a seeded demo project prints a well-formed bundle;
   a note placed in `private/` never appears, even with `--deep`.
3. `zk_lint.py` catches: missing frontmatter field, bad enum, prose-heavy body,
   misnamed log file. `--fix` resolves the mechanical ones.
4. `zk_index.py --check` is stable (second run = no diff).
5. Both skills install into `.claude/skills/` (or via plugin) and trigger from
   their slash commands in a live Claude Code session.
6. End-to-end: recall on empty project → scaffold → work → `/zk:log` →
   files exist, lint-clean, index updated → new session recall reflects the log.
7. All scripts run identically on Windows (PowerShell) and POSIX.

## Out of scope for v1

xref/search skill, inbox/triage, plan/synthesize, embeddings or semantic
search, git automation, MCP server, multi-vault support, migration tooling.
Revisit only after ~20 real logs exist and recall quality can be judged.

## Open questions (ask the user before building if unclear)

- Vault path for dev/testing vs. the real OneDrive vault.
- Plugin packaging (marketplace-style plugin dir) vs. plain `.claude/skills/`
  checked into each project — default to a standalone repo the user symlinks
  or installs, but confirm.
