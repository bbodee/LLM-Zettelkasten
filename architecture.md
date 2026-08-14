# architecture.md — LLM-Zettelkasten (`zk`)

Structural reference: what exists, where it lives, what each piece is responsible for.
Rules and constraints live in [CLAUDE.md](CLAUDE.md). Full vault schema lives in
[docs/SPEC.md](docs/SPEC.md).

State: **planning phase.** Only docs exist. `scripts/`, `skills/`, and `.claude/` are
target state, not built yet.

## Shape

A Python CLI plus two Agent Skills that manage an Obsidian vault as cross-session
memory. Three layers, deliberately separable:

- **Vault** — markdown + YAML on disk. The source of truth. No database.
- **Scripts** — deterministic operations over the vault. LLM-agnostic; any agent can
  drive them from a shell.
- **Skills** — thin Claude-specific wrappers that orchestrate scripts and do the
  judgment work (drafting, summarizing, deciding what's durable).

No MCP server. Claude Code reads and writes the vault natively.

## Repository layout

```
LLM-Zettelkasten/
├── README.md                    # install + usage; root by convention
├── CLAUDE.md                    # rules and constraints; root by convention
├── architecture.md              # this file; root by convention
├── LICENSE
├── docs/                        # ALL prose docs live here — never at root
│   ├── problem.md               # origin spec: scope, acceptance criteria
│   ├── SPEC.md                  # vault schema — single source of truth,
│   │                            # referenced by both skills
│   ├── decisions.md             # repo-level: durable, binding choices (D-NNN)
│   ├── enhancements.md          # repo-level parking lot (E-NNN)
│   └── research.md              # prior-art survey (closed)
├── scripts/                     # Python; each independently CLI-invocable
│   ├── zk_config.py
│   ├── zk_read.py
│   ├── zk_recall.py
│   ├── zk_index.py
│   └── zk_lint.py
├── skills/
│   ├── zk-recall/SKILL.md
│   └── zk-log/SKILL.md
└── .claude/
    └── settings.json            # deny-rule template for private/ + archive/
```

Root holds tooling-convention files only. Any other `.md` goes in `docs/`.

Moved: `problem.md` → `docs/problem.md`. **This was completed**

## Scripts — responsibilities

| Script | Responsibility | CLI |
|---|---|---|
| `zk_config.py` | Locate the vault: env `ZK_VAULT`, else `zk.toml`. | library |
| `zk_read.py` | Note loading, frontmatter parse, **`private/` + `archive/` exclusion**. | library |
| `zk_recall.py` | Assemble a context bundle for one project. | `zk_recall.py <project> [--logs N] [--deep] [--topics a,b]` |
| `zk_index.py` | Regenerate `index.md` from frontmatter. | `zk_index.py [--check]` |
| `zk_lint.py` | Validate schema + directive style. | `zk_lint.py [path] [--fix]` |

`zk_read.py` is the **single chokepoint** for exclusion. No other script walks the
vault directly — a bypass is a bug, not a shortcut.

`zk_recall.py` emits one markdown bundle to stdout, in order: index section →
`project.md` → `decisions.md` → last N logs (default 5, `--deep` = all) → topic notes
matching the project's tags. Hard-excludes `private/` and `archive/` regardless of flags.

`zk_index.py --check` exits nonzero if regeneration would change the file — stable on
a second run, usable in a git hook later.

`zk_lint.py --fix` autocorrects mechanical issues only (missing `updated`, tag casing).
It reports prose problems; it never rewrites prose.

## Skills — responsibilities

**`zk-recall` (`/zk:recall`)** — runs `zk_recall.py`, reads the bundle, confirms loaded
scope in one line. Does not dump the bundle back at the user. Unknown project → offer to
scaffold `projects/<slug>/project.md` by brief interview, then lint it.

**`zk-log` (`/zk:log`)** — drafts the log note from the live conversation, then:
appends to vault `decisions.md` if a durable choice was made (with `superseded-by:` on
any entry it replaces) → writes/updates a `topics/` note if a cross-project insight
emerged → `zk_lint.py --fix` → `zk_index.py` → reports files written. Never writes into
`private/`.

SKILL.md files follow Agent Skills conventions: `name` + `description` frontmatter,
description states what it does **and** when to trigger, body under 200 lines, scripts
referenced by relative path and executed — never pasted inline.

## Vault layout

Separate tree from the repo, located by `ZK_VAULT` or `zk.toml`.

```
vault/
├── index.md                     # GENERATED — never hand-edited
├── projects/<slug>/
│   ├── project.md               # charter: stack, conventions, current state
│   ├── decisions.md             # append-only D-NNN entries
│   └── log/YYYY-MM-DD-<topic>.md
├── topics/<slug>.md             # cross-project knowledge
├── private/                     # mirrors projects/ + topics/; never enters context
└── archive/                     # old vault, read-only, ignored by all scripts
```

Required frontmatter on every note: `type` (project|topic|log|decision), `project`
(required except on topics), `tags` (lowercase-kebab), `status` (active|deprecated),
`updated` (YYYY-MM-DD), `summary` (one dense line — the note's retrieval surface).

Log bodies use fixed sections: `## Done`, `## Decisions`, `## Gotchas`, `## Next`.
Empty sections omitted.

`index.md` is grouped by type, one line per note, sorted by `updated` descending:
`- projects/game-x/log/2026-08-14-save-system.md — <summary> [tags]`. Carries a
generation timestamp header. `private/` and `archive/` never appear.

## Two files named decisions.md

- **`docs/decisions.md`** — repo-level. Choices binding how `zk` itself is built.
- **`<vault>/projects/<slug>/decisions.md`** — vault-level. Written by `/zk:log` about
  the user's own projects.

Same `D-NNN` format, same append-only + supersession rules. Different scope.

## Claude Code integration

- `.claude/settings.json` in this repo is a **template**: a `Read` deny rule for
  `<vault>/private/**` and `<vault>/archive/**`. It does nothing until the user merges
  it into their own project or user settings. README must say so.
- Per-project `CLAUDE.md` snippet for vault users:
  `At session start, run /zk:recall <project-slug>.`
