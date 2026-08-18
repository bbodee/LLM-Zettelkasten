# architecture.md — LLM-Zettelkasten (`zk`)

Structural reference: what exists, where it lives, what each piece is responsible for.
Rules and constraints live in [CLAUDE.md](CLAUDE.md). Full vault schema lives in
[docs/SPEC.md](docs/SPEC.md).

This file is a **rendering of ratified state** (D-068). Every claim traces to SPEC.md, a
decision entry, or [docs/problem.md](docs/problem.md). It introduces nothing, and any
conflict between this file and its sources resolves **toward the source**.

**rendered-against: D-071**

*Diagnostic.* The gap between that value and the tail of
[docs/decisions.md](docs/decisions.md) is the **bound on how stale this file can be** —
not proof of drift, but a visible upper limit. Every decision bumps the field; a decision
touching rendered content re-renders the section as well (CLAUDE.md, wrap discipline).

State: **planning phase.** Only docs exist. `scripts/`, `skills/`, `tests/`, and
`.claude/` are target state, not built yet. Build order is fixed by D-008: scripts
(pytest green) → skills (iterated live) → demo vault.

## Shape

A Python CLI plus two Agent Skills that manage an Obsidian vault as cross-session
memory. Three layers, deliberately separable:

- **Vault** — markdown + YAML on disk. The source of truth. No database.
- **Scripts** — deterministic operations over the vault. LLM-agnostic; any agent can
  drive them from a shell.
- **Skills** — thin Claude-specific wrappers that orchestrate scripts and do the
  judgment work (drafting, summarizing, deciding what's durable).

No MCP server. Claude Code reads and writes the vault natively.

These map to SPEC §0's three enforcement rungs (D-013), which every rule in SPEC is
tagged against:

| Rung | Enforced by | Verified by |
|---|---|---|
| `[lint]` | `zk_lint.py` | running lint |
| `[script]` | the script's own implementation | pytest |
| `[skill]` | SKILL.md instruction | nothing mechanical |

Every `[skill]` tag marks a known soft spot — E-002 parks promotion to hooks.

## Repository layout

```
LLM-Zettelkasten/
├── README.md                    # install + usage; root by convention
├── CLAUDE.md                    # rules and constraints; root by convention
├── architecture.md              # this file; root by convention
├── zk.toml.example              # copy to zk.toml and edit; never read
├── .gitattributes               # `* text eol=lf` — pinned in transport (D-071)
├── LICENSE
├── docs/                        # ALL prose docs live here — never at root
│   ├── problem.md               # origin spec: scope, acceptance criteria
│   ├── SPEC.md                  # vault schema — single source of truth,
│   │                            # referenced by both skills
│   ├── decisions.md             # repo-level: durable, binding choices (D-NNN)
│   ├── enhancements.md          # repo-level parking lot (E-NNN)
│   ├── research.md              # prior-art survey (closed)
│   ├── plan.md                  # build state and chunk boundaries (D-069)
│   └── tasks/T-NN-<slug>.md     # one per chunk; contract + DoD (D-069)
├── scripts/                     # Python; five scripts, per D-007
│   ├── zk_config.py
│   ├── zk_read.py
│   ├── zk_recall.py
│   ├── zk_index.py
│   └── zk_lint.py
├── tests/                       # one module per script; lint split by layer (D-069)
│   ├── conftest.py              # vault factories; ZK_VAULT per test (D-006)
│   ├── fixtures/vaults/<name>/  # plural; each extends D-062's ground state
│   └── meta/                    # invariants whose violation is silent (D-028)
├── skills/
│   ├── zk-recall/SKILL.md
│   └── zk-log/SKILL.md
└── .claude/
    └── settings.json            # deny-rule template for private/ + archive/
```

Root holds tooling-convention files only. Any other `.md` goes in `docs/`.

Planning artifacts are living text, edited in place (D-069, D-040). Fixture vaults are
plural because D-053, D-062, and D-063 each require a different one; the ground state is
built by a conftest factory rather than committed, since git tracks no empty directory
and a `.gitkeep` would be a stray file in the one fixture that must be pristine (D-069).

*Corrected 2026-08-18 — D-069, D-071.* This block previously showed a single
`tests/fixtures/vault/` and no home for planning artifacts or line-ending policy.

The script count is fixed at five (D-007). Vault creation is a flag on `zk_config.py`,
not a sixth script (D-061).

## Scripts — responsibilities

| Script | Responsibility | CLI |
|---|---|---|
| `zk_config.py` | Locate the vault; create one. | `zk_config.py [--init <path>]` |
| `zk_read.py` | Note loading, frontmatter parse, slug resolution, **`private/` + `archive/` exclusion**. | `zk_read.py <slug>` \| `--list` |
| `zk_recall.py` | Assemble a context bundle for one project. | `zk_recall.py <project> [--logs N] [--deep] [--topics a,b]` |
| `zk_index.py` | Regenerate `index.md` from frontmatter. | `zk_index.py [--check]` |
| `zk_lint.py` | Validate schema + directive style. | `zk_lint.py [path] [--fix]` |

### `zk_config.py`

- Resolution order: `ZK_VAULT`, then `zk.toml` searched within a **repo-root fence**
  (D-014, D-015). Neither found → exit 2 naming both mechanisms and `--init`.
- Every script prints its resolved vault and the mechanism that chose it, to **stderr**
  (D-014).
- `--init` creates `projects/`, `topics/`, and `index.md`. It does **not** create
  `private/` or `archive/` — those are reserved names, not territory (D-061).
- `--init` calls `zk_index.py`'s render path rather than writing `index.md` itself, so
  the file has exactly one author and first-command determinism holds by construction
  (D-062).

### `zk_read.py`

- The **single chokepoint** for exclusion. No other script walks the vault directly — a
  bypass is a bug, not a shortcut.
- Exclusion matches `private` or `archive` as **any component** of a vault-relative
  path, casefolded, on either the walked path or its resolved target (D-053).
- Exposes `resolve_project(slug)` returning **three** states — `CHARTED`, `UNCHARTED`,
  `ABSENT` — which both skills branch on and neither reimplements (D-020).
- Opens with `utf-8-sig`, so BOM handling exists in exactly one place (D-028).
- Enforced structurally (D-053): a behavioral fixture vault asserting zero excluded
  paths in any read, index, or bundle; plus a grep companion barring `os.walk`,
  `iterdir`, `glob`, `rglob`, `scandir`, and `listdir` anywhere else in `scripts/`.
- Has a **minimal CLI** exposing existing library functions only (D-067):
  `zk_read.py <slug>` prints a project's note paths and frontmatter, `--list` prints the
  known slugs. The chokepoint must be drivable by a non-Claude agent without
  reimplementing exclusion — otherwise walking the vault directly becomes the path of
  least resistance, which is the bypass the grep companion exists to catch.

### `zk_recall.py`

- Emits one markdown bundle to stdout, in order: index section → `project.md` →
  `decisions.md` → last N logs (default 5, `--deep` = all) → topic notes matching the
  project's tags. Hard-excludes `private/` and `archive/` regardless of flags.
- `--topics a,b` **replaces** the tag join rather than unioning with it (D-070). The join
  is a computed default judgment; the flag is the user overruling it, and a union could
  only add.
- The "index section" is **computed at read time**, not stored — index lines whose path
  starts with `projects/<slug>/`, plus tag-matched Topics lines. No per-project index
  file exists (D-010).
- **Absent sections are omitted entirely** — no empty headers, no narration of what is
  missing (D-021).
- Opens with one factual inventory comment naming what the bundle contains; on any skip
  the comment additionally names the skipped file and the lint remedy (D-021, D-052).
- **Warnings never enter the bundle** — the bundle is retrieval surface. Diagnostics go
  to lint and MAY go to stderr, never to stdout (D-024). Bundle *self-description* is a
  separate category and is permitted (D-052).

### `zk_index.py`

- `--check` exits nonzero if regeneration would change the file — stable on a second
  run, usable in a git hook later.
- Output is **byte-deterministic** (D-012): pinned sort, mandatory path tiebreak,
  explicit `\n`, forward slashes, no iteration order leaking.
- The `generated:` timestamp tracks **content**, not runs — a no-op run leaves the file
  untouched (D-012).
- Header carries `notes:` (diagnostic) and `skipped:` when nonzero, so the index
  declares its own gaps (D-049, D-051).
- Unparseable notes are **skipped, not fatal** — a stale index is worse than an
  incomplete one. This is only acceptable because `skipped:` declares it; the two are
  removable only together (D-052).
- Runs an **index-size check** on every invocation, warning on stderr at 200k and 400k
  characters and naming the parked enhancement whose trigger has fired (D-034).

### `zk_lint.py`

- `--fix` **preserves testimony and may repair representation** (D-046, D-059): line
  endings, BOM, frontmatter key order and quoting, fence delimiters. It never alters
  body content, frontmatter values, or fence contents.
- `--fix` **never moves, renames, or deletes files** — a standing prohibition, not an
  unimplemented feature (D-024). Mechanical means *provably meaning-preserving*
  (D-044).
- Severity encodes exactly one bit: whether automation may act (D-055). Two tiers, never
  three.
- Announces warning accumulation at ~20 with the remedy split; exit stays 0, because the
  threshold is diagnosis, not control flow (D-055).
- ZK codes are permanent identity; message, severity, and logic may change under a
  stable code, and retired numbers are never reissued (D-054).

## Skills — responsibilities

**`zk-recall` (`/zk:recall`)** — runs `zk_recall.py`, reads the bundle, confirms loaded
scope in one line. Does not dump the bundle back at the user. Branches on `zk_read.py`'s
**three** slug states (D-020):

| State | Behaviour |
|---|---|
| `CHARTED` | proceed |
| `UNCHARTED` | name the missing `project.md`; offer to scaffold the charter |
| `ABSENT` | list known slugs; offer to scaffold a new project by brief interview, then lint it |

*Corrected 2026-08-18 — D-020.* This section previously described a two-state flow
("unknown project → offer to scaffold"), which collapsed a half-created directory and a
missing project into one branch despite their needing different remedies.

Normalizes slugs **upstream, in conversation** — a user who types `game_x` is offered
`game-x` before anything is created (D-025).

**`zk-log` (`/zk:log`)** — drafts the log note from the live conversation, then:

1. Appends to vault `decisions.md` **before finalizing the log**, so the `D-NNN` exists
   when the log's pointer is written (D-045). Writes `superseded-by:` on any entry the
   new decision replaces, with a scope tail if the supersession is partial (D-002,
   D-056), and refreshes the file's domain-list summary in the same step (D-009).
2. Writes or updates a `topics/` note if a cross-project insight emerged — reading the
   current version first (D-004).
3. Offers `status` transitions conversationally when the session suggests one (D-032).
4. Runs `zk_lint.py --fix`, then **acts on errors and mentions warnings** — never both
   alike (D-039). Surfaces the warning-accumulation announcement on the mention rung
   (D-055).
5. Runs `zk_index.py`.
6. Reports files written.

Refuses to write against a non-`CHARTED` slug — a log has nowhere to record what the
project is (D-020). Never writes into `private/` (D-053).

SKILL.md files follow Agent Skills conventions: `name` + `description` frontmatter,
description states what it does **and** when to trigger, body under 200 lines, scripts
referenced by relative path and executed — never pasted inline.

## Vault layout

Separate tree from the repo, located by `ZK_VAULT` or `zk.toml` (D-014, D-015).

```
vault/
├── index.md                     # GENERATED — never hand-edited
├── projects/<slug>/
│   ├── project.md               # charter: Stack, Conventions, Current state
│   ├── decisions.md             # append-only D-NNN entries
│   └── log/YYYY-MM-DD-<topic>.md
├── topics/<slug>.md             # cross-project knowledge
├── private/                     # any-component match; never enters context
└── archive/                     # legacy vault, read-only, ignored by all scripts
```

`private/` and `archive/` are **reserved names, not territory** — they are not created
at init and appear only once used (D-061).

Required frontmatter: `type` (project|topic|log|decision), `project` (required except on
topics), `tags` (lowercase-kebab), `updated` (YYYY-MM-DD), `summary` (one dense line —
the note's retrieval surface). `status` is **type-scoped**:

| Type | `status` | Values |
|---|---|---|
| `project` | required | `active` \| `completed` \| `abandoned` |
| `topic` | required | `active` \| `deprecated` |
| `log` | absent | immutable, no states to move between |
| `decision` | absent | a decision log accumulates; per-entry status is `superseded-by` |

*Corrected 2026-08-18 — D-032.* This section previously described `status` as a single
`active|deprecated` enum required on every note. That was true of the original draft and
false after D-032 split the enum by type and removed the field from logs and decision
files.

Log bodies use fixed sections: `## Done`, `## Decisions`, `## Gotchas`, `## Next`. Empty
sections omitted. Unknown names and duplicates are errors; wrong order is a warning,
because the expected violator is our own tooling (D-044).

Mutation policy differs per file and is tabled in SPEC §7.0 — read-modify-write for
charters and topics, immutable testimony for logs, append-only for decisions, generated
for the index (D-046).

`index.md` is grouped by type, one line per note, sorted by `updated` descending with a
path tiebreak:
`- projects/game-x/log/2026-08-14-save-system.md — <summary> [tags]`. Non-active states
carry a parenthesized marker. Carries `generated:`, `notes:`, and `skipped:` when
nonzero. `private/` and `archive/` never appear.

Index lines are a **rendering, not a serialization** — nothing parses them back, and any
consumer needing structure goes through `zk_read.py` (D-050).

## Two files named decisions.md

- **`docs/decisions.md`** — repo-level. Choices binding how `zk` itself is built.
- **`<vault>/projects/<slug>/decisions.md`** — vault-level. Written by `/zk:log` about
  the user's own projects.

Same `D-NNN` format, same append-only rules, different scope. IDs are zero-padded to
three digits, unique per file, **contiguous** — a gap is tamper evidence, since an
append-only file leaves no other trace of a deletion (D-047).

Three amendment species are permitted on append-only files and no others (D-057):
`superseded-by:` on a decision (D-002, D-056), `graduated-by:` on an enhancement
(D-023), and grammar completion of an existing marker where the information is already
ratified elsewhere.

## Claude Code integration

- `.claude/settings.json` in this repo is a **template**: a `Read` deny rule for
  `<vault>/private/**` and `<vault>/archive/**`. It does nothing until the user merges
  it into their own project or user settings. README must say so.
- Per-project `CLAUDE.md` snippet for vault users:
  `At session start, run /zk:recall <project-slug>.`
- Install is manual — symlink or copy `skills/zk-recall/` and `skills/zk-log/` into the
  consuming project's `.claude/skills/`, and set `ZK_VAULT` (D-007). Plugin packaging is
  parked at E-007.
