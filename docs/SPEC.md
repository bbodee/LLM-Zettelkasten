# SPEC.md — Vault Schema (`zk`)

The vault data contract. Single source of truth for both skills and all five scripts.

- Rules for building `zk` → [CLAUDE.md](../CLAUDE.md).
- Component responsibilities and CLI shapes → [architecture.md](../architecture.md).
- This file defines **what a conforming vault looks like** and **what lint enforces**.

**Scope** (D-041): every rule here binds **vault notes** unless explicitly marked
otherwise. Repo document style is CLAUDE.md's jurisdiction. The two overlap in exactly
one place, deliberately — CLAUDE.md's directive-style rule is dual-scoped by its own
text, *"in vault notes and in repo docs alike"* — but only the vault half is
lint-enforced, since `zk_lint.py` runs on the vault. Repo docs keep the norm without the
check, which is why this file opens with an H1 that a vault note may not have.

## 0. Normative language (D-013)

Keywords carry their RFC 2119 meaning — obligation strength, nothing more. **MUST** is a
hard requirement, **SHOULD** a strong recommendation, **MAY** explicit permission
(unchecked, but deliberately granted rather than merely unmentioned).

**Enforcement is tagged per rule, never inferred from the verb.** Three rungs:

| Tag | Means | Enforced by | Verified by |
|---|---|---|---|
| `[lint]` | a property of a file on disk | `zk_lint.py` — MUST → error, SHOULD → warning | running lint |
| `[script]` | behavior of a `zk_*.py` script | the script's own implementation | pytest |
| `[skill]` | behavior of `zk-recall` / `zk-log` | SKILL.md instruction | nothing mechanical |

An unmarked MUST is `[lint]`. Every `[skill]` tag marks a known soft spot — it is the
instruction rung D-004 named as cheapest, and the population E-002 would harden.

**Numeric thresholds name their failure class in the same sentence as their number**
(D-033). A threshold that cannot say which failure it detects is a guess, and its value
will be wrong in a direction nobody notices.

**Every element carries one of three labels** (D-049, D-051):

| Label | Means | Sweep behaviour |
|---|---|---|
| `reasoned` | has a named failure class (D-033) | normal review |
| `conventional` | any consistent answer works; only fixedness is normative | do not "improve" — there is no rationale to serve |
| `diagnostic` | read by a human or model, acted on by neither; bound by nothing | **inert-rule sweep passes over it** |

The third label exists because D-036 removes rules that cannot fire, and a diagnostic
element fires nothing *by design*. **Designed-unread-by-machines is not the same as
dead**, and only the label carries that distinction.

**Rules that cannot fire are not listed** (D-036). There is no statements-of-intent
category — an inert rule is indistinguishable from an active one to a reader and to an
implementer, and produces dead code, a dead test, and false coverage. Intent worth
recording belongs in the why-line of the rule that actually enforces it.

**Each constraint has exactly one normative home** (D-030). Other sections point; they
do not restate. A restatement that drifts is a defect, fixed by deleting the copy.

**Partial coverage is not coverage** (D-037). A check catching a small fraction of a
failure class is dropped, not narrowed — the false impression of coverage stops anyone
looking for the real mechanism. When a mechanical check is dropped as semantic, its
intent routes to the relevant SKILL.md as a drafting rule, with E-001 as the backstop.

**Severity is bounded by two things, whichever is lower** (D-039, D-043):

1. **Predicate exactness** — an error asserts a fact about the file; a detector that
   admits it approximates cannot assert one.
2. **Remediation legitimacy** — if the only mechanical remedy is prohibited elsewhere in
   this spec, the check caps at warning, because D-039's consumer chain means a skill
   would otherwise perform it.

   **The remediation cap binds only where automation could act** (D-056). Where **no**
   mechanical remedy exists in any direction, there is nothing for automation to do
   wrongly and exactness alone grades — error there means *stop and tell a human*, which
   is correct behaviour, not a mis-remediation.

**Every rule declares its layer** (D-042, D-064). **A rule's layer is the surface its
predicate reads** — not what it is about, not what it protects. That definition is what
makes assignment a lookup rather than a judgment.

| Layer | Reads | Fence opacity | Severity |
|---|---|---|---|
| `file` | bytes and paths — encoding, BOM, newlines, filename shape, path length | no effect | ungated |
| `frontmatter` | the parsed YAML mapping — field presence, enums, values | no effect | ungated |
| `structure` | parsed markdown blocks — headings, sections, list items, entries | **exempt by construction** | ungated |
| `content` | **body prose inside a block** — currently sentence counting | **exempt by construction** | **warning-capped** |

`content` is warning-capped **by construction** (D-064): a predicate that reads prose is
approximate by nature, so §0's severity law binds at the layer instead of being
re-argued at each code.

**Derivation rule** — assignment is mechanical:

| The predicate reads… | Layer |
|---|---|
| a path only | `file` |
| a declared value **against** a path | `structure` — location is authoritative (D-031) |
| a frontmatter field value | `frontmatter` |
| body prose | `content` |

The declared-vs-path clause is a **principle, not family-scoped**. It was found on
ZK027–ZK030 but governs every check of that shape, including ZK006 and ZK020.

**Dual-layer codes require the two-codes-rejected argument.** ZK001 is the only one:
locating `---` on line 1 is byte-level, parsing what follows is not, and splitting would
produce two codes for one failure class — which the growth clause below rejects. A
second dual is a signal the taxonomy is wrong, not that duals are normal.

Together with the failure class above, layer is one of the two things a rule must state
before it is ready to be written.

**Every rule that permits a traceless failure needs a paired guard** (D-047, D-048).
Such rules are cheap precisely because the failure they allow leaves no evidence — which
is also why they cannot stand alone. A guard is either a **detector** (lint, after the
fact) or an **upstream obligation** (a skill contract, before the fact); where the
emitter is ours, preventing beats detecting.

| Rule | Permits, untraceably | Guard | Kind |
|---|---|---|---|
| Logs immutable (D-021) | a silent later edit | `updated` ≠ filename date — ZK020 | detector |
| No stub notes (D-021) | a promised note never written | dangling `[[link]]` — ZK039 | detector |
| `decisions.md` append-only (D-002) | a hand-deleted entry | ID gap — ZK013 | detector |
| `decisions.md` accrues (D-009) | summary drifts as entries pile up | refresh-on-append — §7.4 | upstream obligation |
| Unparseable notes skipped (§8) | an absent group reads as "none exist" | `skipped: N` in the index header | detector (data field) |

Exposure citation: D-021's no-stub rule shipped **unguarded** and stayed that way for
twenty-two decisions, until D-043 supplied a detector by accident while reviewing
wikilinks. This principle exists so the next such rule does not ship bare.

**The rendering contract** (D-068). A *rendering* is a document derived from ratified
state. Three clauses, and four instances in this repo:

1. **Derived** — every claim traces to a source; nothing originates in a rendering.
2. **Non-normative** — a conflict with the source resolves **toward the source**.
3. **Self-declaring currency** — the artifact states how current it is, by the strongest
   means available to it.

| Rendering | Source | Currency declared by |
|---|---|---|
| `architecture.md` | SPEC, decisions, problem.md | `rendered-against: D-NNN` header |
| §13 examples | fixture files | structural coupling — the example *is* the fixture |
| `index.md` | vault frontmatter | `generated:`, `notes:`, `skipped:` |
| recall bundle | vault notes | inventory comment + mandatory skip notice |

**Machine-facing identifiers are stable and opaque; human-facing text is descriptive and
free to change** (D-019, D-052, D-054). Exit codes are the caller's control flow and
error messages the human's diagnosis; ZK codes are a rule's identity and its message is
its description. Merging the two degrades both.

**`[skill]` Skills act on errors and mention warnings** (D-039) — never the reverse, and
never both alike. This guards **skill-amplified false positives**: a human seeing a
spurious warning shrugs, while a skill told to resolve complaints *obeys* and rewrites
correct content to satisfy a miscount. Tolerance for approximate checks is a property of
the consumer, and an LLM consumer has none.

## 1. Vault location

Resolution order, first hit wins:

1. Env var `ZK_VAULT` — absolute path to the vault root. Found here, nothing below runs.
2. `zk.toml`, searched within a fence (D-015). Establish the fence first, then search:
   - **Repo root** = nearest ancestor of cwd, cwd included, where `.git` **exists** —
     file or directory. It is a *file* in git worktrees and submodules, holding a
     `gitdir:` pointer, so `is_dir()` would silently drop the fence there.
   - **Repo found** → search cwd upward through the repo root, inclusive. Stop.
   - **No repo** → search cwd only. No walk.
3. Neither → hard error (D-006), listing every directory searched, marking where the
   search stopped, and naming `zk_config.py --init` as the way to create one (§12).

No default, ever — never silently create or assume a vault (D-006).

`zk.toml` schema (D-017, D-022):

```toml
[zk]
vault = "C:/Users/you/OneDrive/vault"
ignore = [".obsidian", "attachments"]
```

- The value MUST be an **absolute** path. Relative paths are not resolved (E-012).
- Any parseable TOML string form is accepted — `"C:/Users/you"`, `"C:\\Users\\you"`, or
  `'C:\Users\you'` (single-quoted literal). `pathlib` normalizes separators after
  parsing, so all three behave identically.
- `[script]` An **unescaped** backslash path — `"C:\Users\you"` — is invalid TOML, since
  `\U` opens a Unicode escape. The file fails to parse before any value is read, so this
  is caught and re-emitted per D-016 with the corrected line shown, never as a raw
  `TOMLDecodeError`.
- `[script]` An unknown key is a hard error naming the near-match:
  `unknown key 'valut' in zk.toml — did you mean 'vault'?` Never silently ignored — a
  typo would otherwise fall through to D-006's "no vault configured," sending the user
  hunting for a file that is sitting right there.
- `ignore` (D-022) is optional and defaults to empty. Exact top-level directory names
  only — no globs, no paths. It **silences warnings and grants nothing**: an ignored
  directory is still never indexed, linted, or recalled. Listing `private` or `archive`
  is a hard error, not a no-op (E-015 parks the opposite feature, a `read` list).
- Parsed with `tomllib` — stdlib from Python 3.11, so no new dependency.
- `zk.toml.example` lives at the repo root and opens with
  `# Copy to zk.toml and edit — this file is never read.`

`[script]` **Every script announces its vault** (D-014). One line to **stderr** on
startup, naming the resolved path and the mechanism that chose it:

```
zk: vault C:/Users/bbodee/OneDrive/vault  (from ZK_VAULT)
zk: vault C:/Users/bbodee/OneDrive/vault  (from C:/work/proj/zk.toml)
```

Stderr, not stdout — `zk_recall.py` emits its bundle on stdout and a banner there would
land inside the context bundle. Both mechanisms are set-and-forget; the banner, not the
precedence order, is what stops a stale path from resolving silently.

- `zk.toml` is gitignored. `zk.toml.example` is committed.

**Normalization (D-018)** — identical for both sources. Expand `~`, collapse `.` and
`..`, follow symlinks and junctions (`Path.resolve()`).

- The result MUST be absolute. A relative value from **either** source is a hard error,
  never anchored to cwd (E-012 parks relative-to-`zk.toml`).
- No environment variable expansion inside the value (E-013).
- `resolve()` follows the junctions OneDrive uses, so D-014's banner may print a path
  differing from what was typed. That is the real location, and intended.
- Resolved path missing or not a directory → exit 2.

## 2. Directory layout

```
<vault>/
├── index.md                          # GENERATED — never hand-edited
├── projects/<project-slug>/
│   ├── project.md                    # charter
│   ├── decisions.md                  # append-only D-NNN entries
│   └── log/YYYY-MM-DD-<topic-slug>.md
├── topics/<topic-slug>.md            # cross-project knowledge
├── private/                          # mirrors projects/ + topics/; never enters context
└── archive/                          # old vault, read-only, ignored by all scripts
```

**Slug resolution (D-020).** `zk_read.py` exposes `resolve_project(slug)` returning one
of three states. Both skills branch on it; neither reimplements the check.

| State | Condition | Exit | Message + offer |
|---|---|---|---|
| `CHARTED` | `projects/<slug>/project.md` exists | 0 | proceed |
| `UNCHARTED` | directory exists, `project.md` does not | 1 | name the missing file; offer to scaffold the charter |
| `ABSENT` | no such directory | 1 | list known slugs; offer to scaffold a new project |

```
zk: 'game-x' has no charter.
  projects/game-x/ exists but projects/game-x/project.md is missing.
  Run /zk:recall game-x to scaffold the charter, or create the file directly.

zk: unknown project 'game-x'.
  Known projects: budgeting-y, website-z
  Run /zk:recall game-x to scaffold a new project.
```

- The known-slug list is built by scanning for `project.md`, so `UNCHARTED` directories
  do not appear in it.
- `[skill]` `zk-recall` interviews and scaffolds. `zk-log` refuses to write against a
  non-`CHARTED` slug — a log has nowhere to record what the project is.
- An `UNCHARTED` directory's logs **are** indexed normally. `index.md` may list Logs
  lines for a project absent from the Projects group; lint raises the missing charter
  (ZK024) rather than the index hiding valid content.
- `decisions.md` and `log/` are created on first write; their absence is not an error.
- No other top-level directories are recognized. Unrecognized ones **warn** (D-022),
  never error and never pass silently:

  ```
  ZK025 warning: '.obsidian/' is not in the vault schema.
    Add ".obsidian" to `ignore` in zk.toml to silence.

  ZK026 warning: 'project/' is not in the vault schema — did you mean 'projects/'?
    If intentional, add "project" to `ignore` in zk.toml to silence.
  ```

  Near-miss matching uses stdlib `difflib.get_close_matches`. The near-miss message
  leads with the correction, not the silence option — the likely truth is a typo, and
  a typo'd directory makes every note inside it invisible to retrieval.
  `[skill]` Scripts state the remedy; `zk-log` may offer to perform the `zk.toml` edit
  conversationally. Scripts never prompt.
- Files outside these paths (e.g. `projects/<slug>/notes.md`) are skipped silently by
  `zk_index.py` and `zk_recall.py`, and reported by `zk_lint.py` (ZK019). **Warnings
  never enter the bundle** (D-024) — the bundle is retrieval surface, and anything in it
  is consumed as knowledge by the reading model. Diagnostics go to lint, and MAY
  additionally go to `zk_recall.py`'s stderr; never to stdout.
- A stray file that carries a **valid `type`** is a different, worse case — it is a real
  note in the wrong place, invisible to retrieval. Caught by the type/location coherence
  family, ZK027–ZK030 (§10).
- A stray file whose **name near-misses a schema shape** warns separately (ZK045). This
  is the case the coherence family **cannot** see: that family keys on a declared `type`,
  and a file with no recognizable type gives it nothing to compare.
- **Stray files get no ignore list**, unlike unrecognized directories (D-058). Two
  reasons. *Population*: directories persist — `.obsidian/` is permanent, recreated by
  the co-tenant, unfixable — so its warning recurs forever and needs suppression; a stray
  file always has a terminating remedy (fix it, type it, or move it to `private/`), so a
  file ignore list would be config for an empty room. *Principle*: a config key that
  makes specific files unmentionable reintroduces config-driven invisibility — the
  `llm_safe` pattern problem.md deliberately replaced with location, and the backdoor to
  §9's location-only exclusion.

## 3. Naming

**Slugs** — project, topic, **and log topic**: `^[a-z0-9]+(-[a-z0-9]+)*$`, max **60
characters**. Lowercase kebab. Governs directory names and filenames, not only tag
values (D-025).

*Why one format everywhere:* tags are lowercase-kebab, and topic→project joins are exact
string matches on tags. If a directory could be `save_system` while its tag must be
`save-system`, every join becomes a normalization question and every script needs a
canonicalization step that must agree everywhere. Case collision on case-insensitive
filesystems is a real second reason, but it explains only the case rule — the underscore
ban is about the join.

- ZK031, error, directional: name the kebab form in the message.
  `invalid slug 'game_x' — use 'game-x'`
- `--fix` never corrects it. Renaming is a file move, prohibited under D-024.
- `[skill]` The skills normalize **upstream**, in conversation: a user who types `game_x`
  is offered `game-x` before anything is created. The lint error is the backstop, not
  the interface.
- ZK032, error: slug over **60 characters**. Failure class: *path-budget contribution* —
  a slug appears in every path containing it, so this number is **derived** from ZK033's
  240 (60 is what keeps a four-level vault path inside it). **Coupling clause: revisit
  the two together if 240 moves** (D-065). A derived number that outlives its source is
  a number nobody can re-derive.
- ZK033, warning: absolute resolved path over **240 characters** — 20 under Windows' 260
  limit. Failure class: *path overflow*. A warning, not an error, because overflow
  depends on where the vault lives, which is not the note's fault.

**Log filenames**: `YYYY-MM-DD-<topic-slug>.md`.

- The date prefix is fixed-width, so parsing is **positional**: `stem[:10]` is the date,
  `stem[10]` MUST be `-`, `stem[11:]` is the topic slug. No splitting on hyphens — the
  date contains two of its own.
- The date is **immutable identity** (D-026) — when the work happened. It is fixed at
  creation and never moves, even if the file is later touched.
- `updated` MUST equal it **always**, not only at creation. `updated` is kept on logs
  precisely because that equality is the **tamper detector** for D-021's immutability
  rule: the only way the two can diverge is an edit that should not have happened.
  ZK020 is bidirectional —

  ```
  error:   log 'updated: 2026-08-11' precedes its filename date 2026-08-14.
           One of the two is wrong.

  warning: log 'updated: 2026-08-19' is later than its filename date 2026-08-14.
           Logs are immutable (D-021) — record the correction as a new log
           rather than editing this one.
  ```

  Earlier is an error because no legitimate sequence produces it. Later is a warning
  because the content is real and the right response is to redirect the author, not
  reject what they wrote.
- Collision on the same date + topic slug → append `-2`, `-3`, … to the topic slug
  (`2026-08-14-save-system-2.md`), chosen as **highest existing plus one**. Never fill a
  gap left by a deleted file: filenames are identity, and identities are not reissued
  (D-027).
- The suffix is **unrecoverable by design**. `save-system-2` is a legal slug and is
  indistinguishable from a topic genuinely named that. No script may parse a filename to
  infer collision order, count, or sequence.
- `[script]` **Log writes are create-only.** If the resolved filename exists at the
  moment of writing, exit 2 — do not overwrite, do not append, do not back up. This is a
  contract independent of the naming rule above: it holds even if suffix selection is
  buggy, two writes race, or the file was created by hand.

**Encoding**: UTF-8, no BOM (D-028).

- `[script]` `zk_read.py` opens with **`utf-8-sig`** — tolerant of a BOM, and only at the
  chokepoint, so BOM handling lives in exactly one place.
- A BOM is still flagged (ZK034, warning, `--fix` strips it) with a directional message:

  ```
  ZK034 warning: projects/game-x/project.md starts with a UTF-8 BOM.
    Usually written by Notepad or PowerShell 5.1 `Out-File`/`>`.
    zk reads it fine, but a BOM breaks naive `startswith("---")` frontmatter
    checks in other tools. Run zk_lint.py --fix to strip it.
  ```

  Tolerating it here does not make it harmless — the vault must stay readable by any
  agent, not only by `zk`.

- `[script]` **No bare `open()` anywhere in `scripts/`.** Every call passes
  `encoding="utf-8"` explicitly; every write also passes `newline="\n"` (D-018). On
  Windows a missing `encoding` silently falls back to the system ANSI codepage and
  mangles non-ASCII content — no exception, one platform, discovered late.
- `[script]` Enforced by a **meta-test** scanning `scripts/*.py` for `open(` without
  `encoding=` and write modes without `newline=`. Invariants whose violation is silent
  get a test, not a convention.

## 4. Frontmatter

Every note MUST open with a YAML frontmatter block: `---` on line 1, `---` closing,
`yaml.safe_load`-parseable, mapping at the top level.

| Field | Type | Required on | Rule |
|---|---|---|---|
| `type` | enum | all | `project` \| `topic` \| `log` \| `decision` |
| `project` | slug | project, log, decision | MUST equal the owning directory name; MUST be absent on `topic` |
| `tags` | list of slugs | all | lowercase-kebab; MAY be empty; duplicates removed |
| `status` | enum | **project, topic only** | see below — MUST be absent on log and decision |
| `updated` | date | all | `YYYY-MM-DD`; date of last content change |
| `summary` | string | all | one dense line — see §5 |

**Unknown keys are cargo** (D-029) — preserved, allowed, and inert.

- **Preserved.** `--fix` rewrites the block wholesale, so preservation is an explicit
  contract: every unrecognized key survives with its value intact. **Semantic**, not
  byte-level — values must round-trip equal; quoting, flow style, and whitespace may
  normalize. Guaranteed by a round-trip fixture in `--fix`'s test contract (§10).
- **Allowed.** The vault is co-tenanted. Obsidian and its plugins legitimately write
  `aliases`, `cssclasses`, `publish`, and their own keys. An unknown key is valid and,
  on its own, silent.
- **Inert.** No script may read, interpret, index, join on, sort by, or branch on an
  unknown key. Carried, never consumed — otherwise the vault grows undeclared schema
  that lint cannot validate and no one can discover.
- **Near-miss only** (ZK035, warning), firing **only when the lookalike known key is
  absent**:

  ```
  ZK035 warning: unknown key 'sumary' — did you mean 'summary'? ('summary' is missing)
  ```

  `sumary` alongside a valid `summary` stays silent: the failure it would predict does
  not exist. This is deliberately *unlike* D-022's plain-warn rule for directories — a
  stray directory is always the user's own doing, while a stray key is routinely written
  by co-tenant tools, and warning on every plugin key would devalue every warning.

- Key order on write: `type`, `project`, `tags`, `status`, `updated`, `summary`, then
  unknown keys in their original relative order. **Conventional** (D-066) — fixedness
  only.
- `type` and location must agree. **Normative home: §10, ZK027–ZK030** (D-030 — each
  constraint is stated in exactly one place; other sections point).

**`status` is lifecycle** (D-032), and only two types have one.

| Type | `status` | Values |
|---|---|---|
| `project` | required | `active` \| `completed` \| `abandoned` |
| `topic` | required | `active` \| `deprecated` |
| `log` | MUST be absent | — immutable (D-021), no states to move between |
| `decision` | MUST be absent | — a decision log only accumulates; per-entry status is `superseded-by` |

Present on `log` or `decision` is a lint error (ZK004), as is a value outside its type's
enum. The enums are split because one shared vocabulary fit neither type — a project is
not "deprecated," a topic is not "completed."

- **Non-active states are surfaced in `index.md`**, active ones are not:
  `- projects/game-x/project.md (completed) — <summary> [tags]`. Parentheses, so the
  marker cannot be confused with the tag list. The common case costs nothing.
- **Bundles never filter on status.** A completed, abandoned, or deprecated note is
  included with its status visible. Hiding content is how knowledge dies quietly
  (D-020, D-021, D-024) — an abandoned project's charter and decisions are precisely
  what stops the work being re-done.
- `[skill]` `/zk:log` offers transitions conversationally when a session suggests one.
  A status field nobody is prompted to update is a status field that rots — the same
  reasoning that put `superseded-by` into the log flow (D-002).

## 5. `summary:` — the retrieval surface

With index-based retrieval, this line **is** the note's representation to a future
session. A vague summary fails silently: the note stops participating in recall (D-003).

`[skill]` Write-time rules — nothing mechanical verifies these:

- State what was decided, learned, or changed — not that work happened.
- Name the concrete nouns: subsystem, file, error, decision. Those are what a future
  question matches against.
- One line. No trailing period needed. No markdown, no wikilinks.

`[lint]` Mechanical backstop:

Three layers, each detecting exactly one failure class (D-033) — **length** catches
non-attempts, **banned patterns** catch lazy shapes, **semantic quality** is E-001's
parked job and no other layer's.

- MUST be present, non-empty, and a single line.
- MUST be ≥ **20 characters** — the floor detects **non-attempts**, and that class
  includes single vague words: `WIP`, `misc`, `various`, `Fixed it` are all rejected on
  length alone, which is why none of them appears in the shape list below (D-036). It
  governs manual writes; skill-drafted summaries clear it structurally.
- SHOULD be ≤ **200 characters** — the ceiling detects **multi-topic packing**, not
  size (D-034). A summary that long is usually two summaries, and the note behind it is
  usually two notes. Catalog size is a vault-level property and is measured as one
  (§8); a per-note limit cannot detect it.

  ```
  ZK017 warning: summary is 247 characters — likely two summaries in one line.
    Split the note, or tighten to the single durable fact.
  ```
- MUST NOT match a banned **shape** (ZK011) — a phrase whose grammatical form describes
  the *act of working* rather than its *result*. Case-insensitive, start-anchored.
  **Normative home for this list** (D-030); it lives here and nowhere else.

  | Pattern | Match | Class |
  |---|---|---|
  | `worked on` | start-anchored | activity, not outcome |
  | `session notes` | start-anchored | activity, not outcome |
  | `notes on` | start-anchored | activity, not outcome |

  `[script]` **The list grows only from observed lazy summaries**, each addition
  recorded as a decision entry naming the summary that motivated it — never
  speculatively (D-035). Vague *words* are not lazy *shapes*: `Progress bar stalls at
  99% when the download completes early` is a real gotcha, and vocabulary judgment is
  E-001's job.

- MUST NOT equal the filename stem with hyphens replaced by spaces. This one is
  genuinely mechanical — a de-kebabbed slug is a shape no honest summary produces by
  accident. The parallel heading check was dropped (D-037): prose-vs-prose equality is
  semantic judgment in mechanical clothing, and it caught only verbatim copy-paste.
  That intent lives in `zk-log`'s drafting rules instead — a summary must add retrieval
  information beyond what the heading and filename already carry — with E-001 as the
  eventual backstop.

## 6. Body style

Directive style. Terse bullets: facts, constraints, gotchas, decisions. No narrative.
Bullets, short headers, tables, and code blocks only.

**Block structure follows CommonMark** (D-038) — the model Obsidian renders. A linter
whose block model disagrees with the renderer reports errors the user cannot see in the
file.

- **Indented continuation lines belong to the block above.** A wrapped bullet is bullet
  content, not prose.
- **Fenced code blocks are opaque at any nesting depth** — including inside list items.
  Their contents never become headings, paragraphs, or list items, so no **structure**
  rule can reach them: a `#!/usr/bin/env python` line is not an H1, and a paragraph of
  comments is not a paragraph. This exempts the structure layer **by construction**, and
  only that layer — file-layer checks still apply to a note containing a fence (D-042).
- Everything else **inherits its container's kind**.

**Sentence cap — two sentences, everywhere** (D-038). Failure class: *narrative creep*
(D-065) — the vault is machine-first and directive-style, and paragraphs are where
explanation displaces fact.

| Unit | Cap | Grade | Code |
|---|---|---|---|
| Paragraph — consecutive prose lines, i.e. any block that is not a heading, list item, blockquote, table row, or fence | 2 | warning | ZK012 |
| List item, including its continuation lines | 2 | warning | ZK036 |

**Sentence boundary** (D-039): `.`, `!`, or `?` followed by whitespace or end of line —
with a bounded abbreviation guard. These are **not** boundaries:

```
e.g.   i.e.   etc.   vs.   cf.   al.
```

`[script]` The guard is data and grows **only from observed miscounts** in the real
vault, never speculatively (D-035). The counter is deliberately crude: it detects
multi-sentence *runs*, not English. Requiring whitespace after the terminator already
handles the frequent technical cases — `3.5 MB`, `src/save/format.py`, `v1.2.3`.

Both codes are layer `content`, which is **warning-capped by construction** — a predicate
that reads prose is approximate by nature, so the cap binds at the layer rather than
being re-argued here (§0, D-064).

The bullet exemption from ZK012 is the design: bullets are the goal form, paragraphs the
capped exception. ZK036 exists because CLAUDE.md's style law already applies to bullets
and nothing was checking it. Warning rather than error, because a long bullet is the
right form done imperfectly while a paragraph is the wrong form.

**Headings** are `##` and `###` only (D-041). Both bans are **error** grade — heading
level is a character count at line start, an exact predicate.

  | Banned | Code | Failure class |
  |---|---|---|
| `#` H1 | ZK037 | structural redundancy — the filename is already the title; Obsidian renders an H1 as a peer of your `##` sections and breaks outline view |
| `####` or deeper | ZK038 | taxonomy growth — four levels of nesting means the note should be two notes |

`###` is permitted. The schema locks section **vocabulary** (§7.1, §7.2), not section
**interiors**; restricting interiors would require observed abuse, and the depth cap
already bounds the sprawl.

**Code blocks** are encouraged for exact commands, paths, and snippets.

**Wikilinks.** Obsidian `[[wikilinks]]` MAY appear but are never load-bearing: scripts
resolve by path and frontmatter, never by link. **Unresolvable simple links warn**
(ZK039, failure class *reference rot*, D-043).

| Form | Checked |
|---|---|
| `[[name]]` | yes — exact slug match against `topics/` slugs and project slugs, nothing else |
| `[[name\|text]]`, `[[name#section]]`, `[[name^id]]` | no — Obsidian's dialect, tolerated |
| any `[[...]]` inside a fence | no — fences are opaque (§0 layer taxonomy) |

We validate the form **our** tools write and tolerate the form the co-tenant writes —
the write-side mirror of §4's unknown-key tolerance.

Warning, not error, despite an exact predicate: every remediation is a content decision
(write the topic, fix the link, delete it), and the one an automated pass would take —
creating a stub — is banned by D-021 (§0's severity law).

It earns its place because a dangling link is the **only** detector for a
promised-but-absent note: D-021 bans stubs, so such a note leaves no file, no index
line, and no error — the link is the sole surviving evidence it was intended.

## 7. Note types

### 7.0 Mutation policy

**Governing distinction** (D-046): rules in this table bind **testimony** — asserted
content, what a note claims is true — and never **representation** — encoding, tag
casing, whitespace, frontmatter key order. `--fix` operates only on representation,
because D-044 defines mechanical as provably meaning-preserving, and an operation that
preserves meaning cannot alter testimony.

| File | Policy | Home |
|---|---|---|
| `project.md` | read-modify-write; read current version before writing | D-004, §7.1 |
| `topics/*.md` | read-modify-write | D-004, §7.3 |
| `log/*.md` | **immutable testimony**; create-only writes; corrections are new logs | D-021, D-027, §7.2 |
| `decisions.md` | append-only; sole amendment is a `superseded-by:` line | D-002, §7.4 |
| `index.md` | generated wholesale; never hand-edited | D-012, §8 |

`[script]` **Mechanical fixes never touch `updated`** — it is the tamper detector for
testimony (D-026), and repairing representation is not tampering. The one exception is
filling a **missing** value: ZK016 writes today's date for `project` and `topic`, and
the **filename date** for logs.

### 7.1 `project.md` — charter

Closed H2 vocabulary (D-011). Unlike logs, required sections are **not** omitted when
empty — they are filled at creation by `zk-recall`'s scaffold interview.

| Section | Rule |
|---|---|
| `## Stack` | Required. MUST be present and non-empty. |
| `## Conventions` | Required. MUST be present and non-empty. |
| `## Current state` | Required. MUST be present and non-empty. |
| `## Constraints` | Optional. Omitted entirely when unused; present-but-empty is an error. |
| `## Glossary` | Optional. Same rule. |
| anything else | Warning (ZK018), not an error. |

The vocabulary is closed so that D-004's "never append a section that already exists"
is decidable by string match rather than judgment. `## Tech Stack` alongside `## Stack`
is the failure this prevents.

`[skill]` Read-before-write (D-004): never regenerate this file from conversation
context. Read the current version, merge, write. Never append a section that already
exists.

### 7.2 `log/YYYY-MM-DD-<topic>.md` — session log

Fixed H2 sections, in this order: `## Done`, `## Decisions`, `## Gotchas`, `## Next`.
The order is **conventional** (D-066) — fixedness is normative, the particular sequence
is not, and there is no rationale behind it to "improve" toward.

- Empty sections omitted. Three separate checks, one per failure class (D-044):

  | Check | Code | Grade | Failure class |
  |---|---|---|---|
  | Unknown section name | ZK009 | error | closed vocabulary — `## Gotcha` beside `## Gotchas` |
  | Sections out of order | ZK040 | warning | **emitter conformance** — the order is `zk-log`'s drafting contract |
  | Duplicate section name | ZK041 | error | breaks name-based parsing — "the Gotchas section" stops being well-defined |

  Order is a warning because nothing parses positionally: a reader is unharmed, the
  primary violator will be the skill itself, and the note must not be blocked for the
  tool's drift. `[skill]` The order belongs in `zk-log`'s SKILL.md as a drafting rule.

  Duplicates are an error because they are the one malformation that genuinely breaks
  parsing. Remediation is a **human merge** — `--fix` never touches it, and the skill
  surfaces it rather than concatenating, since ordering between the two blocks is a
  content decision.
- `## Decisions` here holds **pointers**, not records. **Normative home: §7.4** (D-030).
- Logs are **immutable testimony** — a correction is a new log, not an edit. Mechanical
  representation repair (`--fix`) remains legal on old logs; it cannot alter testimony by
  construction. **Normative home: §7.0** (D-046).
- A misspelled topic slug is **not** repairable — the filename is identity (D-025,
  D-027). ZK043 warns when a log's topic slug near-misses another log's topic slug in the
  same project. It cannot fire on the first log about a subject; that harshness is
  accepted, since retrieval resolves by frontmatter and index line, never by filename
  spelling.

### 7.3 `topics/<slug>.md` — cross-project knowledge

- No `project:` key. Free H2 structure.
- `tags` are the join to projects: recall pulls topics whose tags intersect the
  project's tags.
- `[skill]` Updated in place as knowledge accumulates — read-before-write applies (D-004).

### 7.4 `decisions.md` — append-only decision log

One file per project. Frontmatter labels the **container**, not any entry (D-009):
`type: decision`, and **no `status` field** — a decision log accumulates and has no
lifecycle (§4, D-032). Per-entry status is carried solely by `superseded-by`. `updated`
tracks the last appended entry.

Entry format — one `##` per decision, newest appended at the bottom:

```markdown
## D-007 — 2026-08-14 — Short imperative title
- Decision: what was chosen. One or two lines.
- Why: the reason that survives the context being forgotten.
- Rejected: the real alternatives and why they lost.
- superseded-by: D-012 (2026-09-02)      # appended later, only when replaced
```

- IDs are `D-` + zero-padded 3-digit serial, **unique per file**, **contiguous**, never
  reassigned or reused. Vault `D-NNN` and repo `D-NNN` are separate sequences.
- **Sequential means contiguous** (D-047). A missing `D-003` between `D-002` and `D-004`
  is a ZK013 **error** — the gap is this file's **tamper detector**. The file is
  append-only, so a hand-deletion leaves no marker, no timestamp change, and no index
  line; the gap in the sequence is the only surviving evidence an entry existed. No
  mechanical remediation exists or is wanted — the correct response is a human
  accounting for what was removed.
- Padding is 3 digits. `D-999` exceeds the design life of a single decisions file: D-001's
  context trigger fires long before a thousand entries, so overflow is E-008's or E-004's
  problem, seen and deliberately not engineered around.
- **Newest appended at the bottom**, which keeps the write path a pure append and content
  restructuring out of it entirely (§10's restructuring boundary).
- Entries are append-only. The **only** permitted amendment to an existing entry is
  appending a `superseded-by:` line (D-002). **Marker grammar** (D-056) — stated here
  once, so ZK015 has exact syntax to bind:

  ```
  superseded-by: D-NNN (YYYY-MM-DD)
  superseded-by: D-NNN (YYYY-MM-DD) — status clause only
  ```

  The optional ` — <scope>` tail marks a **partial** supersession. Without it, the scope
  of a partial reversal can only live in the *superseding* entry's prose, where the
  reader of the *superseded* entry never sees it.
- ZK015, **error**, failure class **dangling supersession**: the
  target MUST exist in the same file, and MUST differ from the carrying entry. A marker
  pointing nowhere is worse than no marker — the record discounts its own testimony in
  favour of nothing, and the entry still enters every bundle wearing a false resolution.
- **Cross-project supersession has no syntax and needs none.** `D-NNN` is unique per file
  (D-002), so a bare cross-file reference is ambiguous. It **composes**: record a local
  supersession in the affected project and cite a `topics/` note carrying the
  cross-project reasoning.
- `superseded-by` is a pointer, never a gate: superseded entries are not deleted, not
  hidden, and still enter recall bundles.
- Body: **4 lines max** per entry (`superseded-by` excluded from the count). Failure
  class: *record bloat* (D-065) — an entry needing more is a document, and this file is
  read whole on every recall, so entry length is charged to every future session rather
  than to its author.
- `[skill]` `/zk:log` MUST read existing entries before appending, and MUST write the
  marker on the old entry when the new one replaces it.

**The two-place structure** (D-045). A decision appears twice, deliberately:

| Where | What | Answers |
|---|---|---|
| `log/*.md` → `## Decisions` | a **pointer** — `Versioned JSON over pickle — see decisions.md D-004` | what happened this session |
| `decisions.md` → `## D-NNN` | the **durable record** — decision, why, rejected | what is true about this project |

This does not violate D-030's one-normative-home rule: **restatement duplicates,
citation indexes.** A second copy of a rule can drift; a pointer into the one home
cannot.

- ZK042, warning, failure class **record displacement** — every
  bullet under a log's `## Decisions` carries a `D-NNN` reference. A full decision
  written into a log and never promoted is still indexed, so nothing is lost, but it is
  found as *session history* rather than as *a standing decision*, and D-002's
  supersession machinery cannot reach it without an ID.
- `[skill]` **Sequencing contract**: `zk-log` appends to `decisions.md` **before**
  finalizing the log, so the `D-NNN` exists when the pointer is written. This makes the
  obvious false positive — "not written yet" — a true positive instead: it is a skill
  sequencing bug, and the check should catch it.
- Warning on both caps: emitter conformance (the violator is our own tooling — fix the
  skill, do not block the note) and remediation legitimacy (promotion is a content act,
  and deciding what is durable is the judgment `/zk:log` exists to make).

**Summary phrasing.** The file's `summary:` MUST be a domain list, never a count:

- Good — `Decisions on save format, tilemap storage, and input rebinding`
- Bad — `8 decisions covering save format and build tooling`

`[skill]` **Not lint-checked** (D-048). The failure class is *accrual staleness*, and it
is guarded **upstream** by the refresh-on-append rule below rather than detected
downstream — a regex for count phrasing was wrong in both directions and redundant with
the guard that works. Drafting rule lives in `zk-log`'s SKILL.md; E-001 is the backstop.

A count is wrong on the very next append and lint cannot detect the drift. A domain list
only goes stale when a genuinely new domain appears — which is exactly when the author is
most likely to notice. `/zk:log` MUST refresh this line in the same step that appends an
entry (`[skill]`); the whole file is already in context from the D-002 read, so it costs
nothing.

## 8. `index.md` — generated

Never hand-edited. Regenerated wholesale by `zk_index.py` from frontmatter.

```markdown
# index

generated: 2026-08-14T09:12:04Z
notes: 47
skipped: 3

## Projects
- projects/game-x/project.md — <summary> [engine, save-system]

## Decisions
- projects/game-x/decisions.md — <summary> [architecture]

## Logs
- projects/game-x/log/2026-08-14-save-system.md — <summary> [save-system, serialization]

## Topics
- topics/serialization.md — <summary> [serialization, versioning]
```

`[script]` **Header field scope** (D-051): header fields describe the contents of **this
file**, not the vault. `notes:` counts what is indexed; `skipped:` is the sole reference
to anything absent; totals are derivable and never stated.

- `generated:` is **diagnostic** (D-066) — read by a human, acted on by nothing. It is
  excluded from `--check`'s comparison and tracks content rather than runs (below).
- `notes:` is **diagnostic** — context for §8's index-size warnings, since 2,000 small
  notes and 200 bloated summaries yield the same character count and need different
  remedies. Bound by nothing: no threshold, no check, no exit code. D-001's "measure,
  don't count" forecloses note count as a *threshold*, not as *context beside* one.
- Group order is **arbitrary-but-fixed** (D-049): Projects, Decisions, Logs, Topics.
  Only the *fixedness* is normative — it belongs to the determinism rules below, since
  iteration-order emission would produce phantom diffs. The particular order has no
  failure class behind it; this is a **conventional** choice, not a reasoned one.
- Empty groups omitted — a header with no entries is a stub (D-021).
- **Groups are independent, and two asymmetries follow. Both are intended:**
  an UNCHARTED project's logs are indexed (D-020), so a project can appear in **Logs but
  not Projects**; a freshly scaffolded project has only a charter (D-021), so it can
  appear in **Projects and nowhere else**.
- Line format: `- <vault-relative-path>[ (<status>)] — <summary> [<comma-space-joined tags>]`.
  The parenthesized status appears **only for non-active states** (D-032); active notes
  and types without a `status` field carry no marker.
- **Em dash separator — reasoned** (D-050). Failure class: *generation-side separator
  distinctness*. Index lines are slug-dense — paths, dates, and kebab tags are all
  hyphen-rich — so a plain hyphen would be indistinguishable from a dozen others on the
  line. The em dash appears nowhere else in a generated line.
- **Comma-space join and bracket characters — conventional** (D-049). Any consistent
  choice works.
- Empty tag list → the brackets are **omitted entirely**, never emitted empty (D-021's
  family). An empty `[]` is a stub, and it costs density on the surface D-001 requires to
  be dense.

- Sorted by `updated` descending, then path ascending as tiebreak. The tiebreak is
  mandatory — without it, two notes sharing an `updated` date may swap between runs and
  produce a phantom diff indistinguishable from a real one.
- `[script]` **Byte-deterministic (D-012).** Identical vault content MUST render byte-identical
  output. No dict or `os.walk` iteration order may leak into the result; newlines are
  explicit `\n`; paths use forward slashes on every platform.
- `[script]` **The timestamp tracks content, not runs.** `zk_index.py` renders the index, compares
  it against the file on disk **ignoring the `generated:` line**, and writes only when
  the content differs. A no-op run leaves the file completely untouched — same bytes,
  same mtime, no sync churn. `generated:` therefore means "when the catalog last
  changed."
- `--check` performs the same comparison and writes nothing. Exit 1 on difference.
- `[script]` **Index-size check** (D-034), run on every invocation including `--check`.
  Warns on **stderr**; never affects exit status — nothing is broken, the vault is
  approaching a design boundary. Failure class: *the flat catalog no longer fits
  comfortably alongside a working session's own content.* Measured in characters, not
  note count, per D-001's "measure, don't count."

  | Threshold | Basis | Cites |
  |---|---|---|
  | 200,000 chars (~50k tokens) | catalog stops being cheap to load | E-008 — two-tier index, the cheaper first move |
  | 400,000 chars (~100k tokens) | catalog dominates a working context | E-004 — embeddings |

  The warning **names the parked enhancement whose trigger has fired** and points at
  `docs/enhancements.md`. D-005 requires fired triggers to graduate or be consciously
  re-parked; this makes the firing impossible to miss rather than dependent on someone
  checking at the 20-log review.

  ```
  zk: index.md is 214,300 characters (~54k tokens) — the flat catalog no longer
    fits comfortably alongside a working session.
    Trigger fired: E-008 (two-tier pointer index). See docs/enhancements.md.
  ```
- `private/` and `archive/` never appear.
- Paths use forward slashes on every platform.
- A note whose frontmatter fails to parse is skipped and reported on stderr; it does not
  abort the rebuild (D-052). Aborting would freeze `index.md`, and a **stale** index is
  worse than an **incomplete** one, because everything downstream reads it.
- **Jurisdiction:** the index's question is **binary — renderable or not.** It does not
  grade parse failures. `zk_lint.py` owns severity discrimination across the three cases
  (no frontmatter, malformed YAML, valid YAML of the wrong shape). A stray `.md` with no
  frontmatter is counted and skipped like anything else — **no exempt category**.
- Fail-soft depends on `skipped:` below being emitted. **The two are removable only
  together**; without the counter this rule silently discards content.
- `[script]` **The index declares its own gaps** (D-049). `skipped: N` appears in the
  header whenever N > 0, and is omitted at zero. Both `notes:` and `skipped:` are
  content-derived and deterministic, so `--check` compares them like any other content.

  Without it the failure is traceless: stderr is transient, so a vault whose entire
  `topics/` directory fails to parse yields an index with **no Topics group**, which
  reads as "this vault has no topics" — an absence indistinguishable from a fact. The
  header makes the distorted surface declare its own incompleteness. No lint code is
  needed; the field **is** the detector.

`[script]` **Normative non-goal: index lines are a rendering, not a serialization**
(D-050). **Nothing parses them back.** Any consumer needing structure goes through
`zk_read.py`, which reads frontmatter from the source notes — the same chokepoint that
enforces exclusion.

Consequently **no constraints are placed on summary characters**: a summary may contain
em dashes, brackets, or anything else. Constraining prose to protect a parser that does
not exist would cost real retrieval quality (§5) for an imaginary benefit.

Recall's "index section" for a project = all index lines whose path starts with
`projects/<slug>/`, plus Topics lines whose tags intersect the project's tags. No
per-project index file exists (E-004/E-005 park the alternatives).

### 8.1 Recall bundle composition (D-021)

Order: index section → `project.md` → `decisions.md` → last N logs → tag-matched topics.

`[script]` **`--topics a,b` replaces the tag join; it never unions with it** (D-070). Only
the named topics are pulled, and naming a tag the project does not carry is not an error —
reaching outside the join is the point of an override.

*Added 2026-08-18 — D-070.* This section named the tag-matched topics without saying what
an explicit `--topics` does to them, leaving override and union equally readable. The tag
join is a computed default judgment (D-010) and the flag is the user overruling it; a
union could only add, and that outcome is already reachable by omitting the flag.

`[script]` **Absent sections are omitted entirely.** No empty headers, no placeholder
text, no narration of what is missing. A project with only a charter emits a charter.

The bundle opens with one factual inventory comment naming only what it contains. It is
**diagnostic by category and load-bearing by obligation** (D-066) — nothing branches on
it, *and* D-052 makes it mandatory on any skip, where it is the only surface declaring a
bundle incomplete. It is exempt from unread-deletion on **both** grounds; a future reader
finding "nothing consumes this" must answer both objections, not one.

```
<!-- zk: game-x | charter, 4 decisions, 5 logs, 2 topics -->
<!-- zk: game-x | charter -->
```

Absent categories do not appear in it. The counts are regenerated every run and cannot
go stale, which is why they are permitted here and banned in a `decisions.md` summary
(§7.4).

`[script]` **On any skip the inventory comment is mandatory and names the omission** —
the skipped file and the lint remedy (D-052):

```
<!-- zk: game-x | charter, 4 decisions, 5 logs -->
<!-- zk: SKIPPED projects/game-x/log/2026-08-11-tilemap.md — frontmatter did not
     parse. Run zk_lint.py on it. -->
```

A bundle silently missing a note from the project under discussion is the
highest-stakes omission in the system, so it is declared on the surface the model
actually reads.

**This is not a diagnostic in D-024's sense.** D-024 keeps *vault diagnostics* —
complaints about other notes — out of the bundle, because a model consumes them as facts
about the domain. This is **bundle self-description**: a report on the completeness of
what is being handed over, the same category as the inventory comment itself and as
`skipped:` in the index header. An artifact may always describe itself (§8, D-051).

This is the acceptance-criteria-6 path: recall on a fresh project → scaffold → work →
`/zk:log` → recall again reflects the log.

## 9. Exclusion — `private/` and `archive/`

**Governing asymmetry** (D-053): **exclusion errs toward excluding — an ambiguous path is
private.** Every other rule here trades retrieval quality; this one trades privacy.
Over-excluding costs a note the user must move; under-excluding puts private content in a
context window and sends it to Anthropic. Ties are not split.

- `[script]` `zk_read.py` is the **single chokepoint**. No other script walks the vault
  directly.
- A path is excluded when `private` or `archive` appears as **any component** of its
  **vault-relative** path, compared **casefolded** — unconditionally, regardless of flags
  including `--deep`.

  | Path | Excluded | Why |
  |---|---|---|
  | `private/budgeting-y/accounts.md` | yes | root private |
  | `archive/old-vault/…` | yes | root archive |
  | `projects/game-x/private/secrets.md` | yes | any-component — unmistakable intent |
  | `projects/private/notes.md` | yes | any-component; **slug shadowing**, warns via ZK044 |
  | `Private/…` | yes | casefolded |
  | `projects/private-api/…` | no | component match, not substring |

  Casefolding is required because this test runs **before** lint — it cannot depend on
  D-025's lowercase rule having passed.
- **Symlinks: exclude on either the walked path or its resolved target.** Testing only
  the walked path misses a link *into* `private/`; testing only the target misses a link
  *from* it.
- `[script]` **ZK044 is emitted by the chokepoint itself**, not by a normal lint pass —
  nothing downstream can see an excluded path. A project or topic slug equal to a
  reserved name vanishes silently otherwise, which is the traceless-failure principle
  (§0) applied to exclusion.
- Exclusion is by location only. There is no `llm_safe`-style frontmatter flag, and none
  will be added.
- `[script]` `[skill]` Neither scripts nor skills may write into `private/`. Sensitive
  content is placed there by the user by hand; the vault records at most a pointer-free
  stub elsewhere.
- `archive/` is read-only reference: never read into context, never linted, never indexed.
- This gates what enters context, not what reaches Anthropic. Anything Claude reads is
  sent.

`[script]` **Enforcement is structural** (D-053) — the strongest instance of D-028's
meta-test class, because this is the only rule whose failure costs privacy rather than
retrieval quality:

1. **Behavioral fixture vault**, built from the adversarial table above — every row,
   every flag, `--deep` included. Asserts **zero excluded paths** appear in any read, in
   `index.md`, or in any bundle. D-006 already commits a synthetic `private/` note under
   fixtures for exactly this purpose.
2. **Grep companion** enforcing the sole-walker chokepoint: no `os.walk`, `iterdir`,
   `glob`, `rglob`, `scandir`, or `listdir` anywhere in `scripts/` outside `zk_read.py`.

One rule, one function, one fixture suite.

## 10. Lint rules

`zk_lint.py [path] [--fix]`. Exit codes per §11.

**Severity encodes exactly one bit: whether automation may act** (D-055). Error → act;
warning → mention (D-039). That is its entire job, which is why there are two tiers and
not three. Finer discrimination between warnings is **presentation** — output may sort
and group by layer and failure class, both already in this table — and is **never a
third grade**.

`[script]` **Warning accumulation is announced** (D-055). Failure class:
*reckoning-avoidance* — each warning is correctly ignored in isolation, so the pile grows
invisibly. At **~20 warnings** (the class is named; the number is honestly a guess and
should move once real vault data exists) lint's summary says so and splits the remedy:

```
zk: 23 warnings. 14 are mechanical — run zk_lint.py --fix.
    The other 9 need review; see the list above.
```

Exit status stays **0**: nothing failed, and the threshold is **diagnosis, not control
flow**. `[skill]` `/zk:log` surfaces the announcement conversationally on the mention
rung — the reckoning arrives through the existing consumer chain, with no new machinery.

**Codes are permanent identity** (D-054). Three clauses:

1. A code names the **rule**, not its current wording.
2. **Message, severity, and detection logic may all change under a stable code**, by
   decision entry. ZK012 moved error → warning under D-039 and stayed ZK012; every test
   asserting it remained correct.
3. **Retirement is forever.** ZK023 was deleted by D-048 and its number stays retired.
   Unlike `D-NNN` (§7.4), gaps here are history, not tamper evidence.

**Numbering is flat and conventional** (D-049) — only stability is normative. Layer is
carried by the declaration in §0, never encoded in the number, so **adjacency between
codes is an accident of when they were written**. ZK027–ZK030 are a family because they
were added together, not because a range was reserved.

**Growth clause — a new code requires all four, by decision entry only:**

| Requirement | Home |
|---|---|
| a named failure class | D-033 |
| a declared layer | D-042 |
| a grade passing the severity law | D-039, D-043 |
| a row in §0's guard table, if it guards a traceless-failure rule | D-047, D-048 |

A code that cannot supply all four is not ready to exist.

Codes are opaque by design — `ZK027` describes nothing on its own. That is **accepted,
not fixed**: messages self-describe (D-016), this table is the **sole** code→rule
mapping, and no parallel slug-name scheme exists to drift out of sync.

This table is the **sole layer declaration** for all 44 codes (D-064).

| Code | Severity | Layer | Check | `--fix` |
|---|---|---|---|---|
| ZK001 | error | `file` + `frontmatter` | Frontmatter present and parseable | no |
| ZK002 | error | `frontmatter` | Required field present (§4) | no |
| ZK003 | error | `frontmatter` | `type` value is one of the four enum members | no |
| ZK004 | error | `frontmatter` | `status` contract: present iff project/topic, value in that type's enum (§4) | no |
| ZK005 | error | `frontmatter` | `updated` is `YYYY-MM-DD` | no |
| ZK006 | error | `structure` | `project` matches owning directory; absent on topics | no |
| ZK007 | error | `frontmatter` | Tags are lowercase-kebab slugs | yes — lowercase, kebab, dedupe |
| ZK008 | error | `file` | Filename matches convention for its type | no |
| ZK009 | error | `structure` | Unknown log section name (§7.2) | no |
| ZK010 | error | `frontmatter` | `summary` present, one line, ≥ 20 chars (§5) | no |
| ZK011 | error | `frontmatter` | `summary` not a banned **shape** (§5) | no |
| ZK012 | warning | `content` | Paragraph over 2 sentences (§6) | no |
| ZK013 | error | `structure` | Decision IDs `D-NNN`, unique, **contiguous** — gaps are tamper evidence (§7.4) | never |
| ZK014 | error | `structure` | Decision entry body ≤ 4 lines | no |
| ZK015 | error | `structure` | `superseded-by` target exists in the same file and differs from its carrier (§7.4) | never |
| ZK016 | warning | `frontmatter` | `updated` missing | yes — today for project/topic, **filename date** for logs (§7.0) |
| ZK017 | warning | `frontmatter` | `summary` over 200 chars — multi-topic packing (§5) | no |
| ZK018 | warning | `structure` | Unknown H2 in `project.md` — vocabulary drift (§7.1) | no |
| ZK019 | warning | `file` | Unrecognized file location — unreachable content (§2) | no |
| ZK020 | error / warning | `structure` | Log `updated` ≠ filename date — **error** if earlier, **warning** if later (§3) | no |
| ZK021 | error | `structure` | Required `project.md` section missing or empty (§7.1) | no |
| ZK022 | error | `structure` | Optional `project.md` section present but empty (§7.1) | no |
| ZK024 | error | `file` | `projects/<slug>/` has no `project.md` — UNCHARTED (§2) | no |
| ZK025 | warning | `file` | Unrecognized top-level directory (§2) | no |
| ZK026 | warning | `file` | Unrecognized top-level directory, near-miss to a schema name (§2) | no |
| ZK027 | error | `structure` | `type: log` not under `projects/<slug>/log/` | never |
| ZK028 | error | `structure` | `type: project` not at `projects/<slug>/project.md` | never |
| ZK029 | error | `structure` | `type: topic` not at `topics/<slug>.md` | never |
| ZK030 | error | `structure` | `type: decision` not at `projects/<slug>/decisions.md` | never |
| ZK031 | error | `file` | Slug not lowercase-kebab — directory or filename (§3) | never |
| ZK032 | error | `file` | Slug over 60 characters (§3) | never |
| ZK033 | warning | `file` | Absolute resolved path over 240 characters (§3) | no |
| ZK034 | warning | `file` | UTF-8 BOM at start of file (§3) | yes — strip it |
| ZK035 | warning | `frontmatter` | Unknown key near-matches an **absent** known key (§4) | no |
| ZK036 | warning | `content` | List item over 2 sentences (§6) | no |
| ZK037 | error | `structure` | `#` H1 heading present (§6) | no |
| ZK038 | error | `structure` | Heading `####` or deeper (§6) | no |
| ZK039 | warning | `structure` | Unresolvable simple `[[wikilink]]` (§6) | never |
| ZK040 | warning | `structure` | Log sections out of order (§7.2) — emitter conformance | never |
| ZK041 | error | `structure` | Duplicate log section name (§7.2) | never |
| ZK042 | warning | `structure` | Log `## Decisions` bullet without a `D-NNN` (§7.4) — emitter conformance | never |
| ZK043 | warning | `file` | Log topic slug near-misses another log's topic slug in the same project (§7.2) | never |
| ZK044 | warning | `file` | Project or topic slug shadows a reserved name (`private`, `archive`) — emitted by the chokepoint (§9) | never |
| ZK045 | warning | `file` | Stray file's name near-misses a schema shape (§2) | never |

### Type/location coherence — ZK027–ZK030

**Normative home for the `type`↔location constraint** (D-030). §4 points here.

`type` declares what a note is; location determines whether anything can find it. This
is **one comparison, reported once** (D-031) — declared type versus location-implied
type — keyed by the *declared* type so one code names one intent. Two failure shapes:

**Misfiled** — right type, wrong place. Fails closed: invisible to retrieval, damage
bounded to that note. No near-miss check catches it, because the filename is usually
correct.

```
ZK027 error: projects/game-x/2026-08-14-save-system.md declares `type: log`
  but is not under log/.
  Expected: projects/game-x/log/2026-08-14-save-system.md
  Move the file, or change `type` if it is not a log. --fix will not move it.
```

**Mistyped** — right place, wrong type. Fails **open**, which is why this family is
error-grade: the note is found and then miscategorized. A log declaring `type: topic`
lands in the Topics group of `index.md` and is pulled by tag intersection into the
bundles of *unrelated projects*, presenting one project's session notes as cross-project
knowledge. The damage crosses project boundaries.

```
ZK029 error: projects/game-x/log/2026-08-14-save-system.md
  location implies `type: log`; frontmatter declares `type: topic`.
  Either move the file to topics/, or correct the type to `log`.
```

The message states both facts and **does not guess** which side is wrong — both are
plausible, and `--fix` can resolve neither (moving is prohibited; rewriting `type` would
pick one of two intentions silently).

`[lint]` **Location is authoritative for applying every other rule** (D-031). A note at
`projects/game-x/log/x.md` declaring `type: topic` is still validated as a **log** —
fixed sections, filename-date/`updated` equality, all of it — while the mismatch is
reported. A note cannot escape its location's ruleset by mislabeling itself.

`[script]` **`--fix` never moves, renames, or deletes files** — for this family or any
other. A wrong guess about intent relocates real content, and lint's remit is to report
malformed structure, not to restructure the vault. The `never` column above is stronger
than `no`: it is a standing prohibition, not an unimplemented feature.

`[script]` **The restructuring boundary** (D-044): `--fix` is mechanical-only, and
**mechanical means provably meaning-preserving**. Reordering log sections was the first
candidate tested against this and rejected — cross-section references (`## Next` saying
"the above", a gotcha referring to a decision by position) are meaning-bearing and
invisible to a block mover. Later restructuring proposals cite this test rather than
relitigating it.

- `--fix` autocorrects mechanical issues only. It **never** rewrites prose: ZK010–ZK012
  are reported for the author to fix.
- `[skill]` Skills **act on errors and mention warnings** (D-039). This supersedes
  problem.md line 173's unscoped *"fix any residual complaints"* — which, as written,
  would have a skill rewrite correct prose to satisfy an approximate check.
- `--fix` **preserves testimony and may repair representation** (§7.0, D-059). It has one
  guarantee, not two dialects:

  | May repair — representation | Never touches — testimony |
  |---|---|
  | line endings → `\n` (D-018) | any word of body content |
  | BOM stripped (ZK034) | frontmatter **values** |
  | frontmatter key order, quoting, flow style (D-029) | fence **contents** |
  | fence **delimiters** — style and length | |

  The drafted phrase "preserves body bytes" is gone: newline normalization and BOM
  stripping both change body bytes on conforming input, so it was a contract
  contradicted by shipped behaviour.
- `[script]` **`--fix` round-trip fixture** — part of `--fix`'s test contract, not an
  optional test. A fixture note carrying assorted unknown keys (`aliases`, `cssclasses`,
  a nested mapping, a list, a quoted string) is asserted **semantically equal** after a
  fix pass: every key present, every value equal. Formatting is explicitly not
  guaranteed — quoting, flow style, and whitespace may normalize.
- Linting `private/` or `archive/` is a no-op (§9).

## 11. Exit codes

**The test (D-019): did the script get to do its job?**

| Code | Test | Examples |
|---|---|---|
| 0 | Did its job; result is positive | anything that succeeded (warnings may print) |
| 1 | Did its job; result is negative | lint found errors, unknown project slug, `--check` diff |
| 2 | Could not do its job at all | no vault configured, vault path missing or not a directory, bad flag |

Tiebreak for genuine ambiguity: if the same command, unchanged, would fail identically
for *every* possible invocation in this environment, it is 2; otherwise 1.

`[script]` **Overloaded codes disambiguate in the message, never by adding codes**
(D-052). One code legitimately covers several conditions — `zk_index.py --check` exits 1
both for "the index is stale" and for "the vault has broken notes," and its report names
which header fields moved and why. The exit code is the **caller's control flow**; the
message is the **human's diagnosis**. Multiplying codes to encode conditions degrades
both.

`[script]` Every new failure path MUST be classified by this test as part of the change
that introduces it. No unclassified nonzero exits.

`[script]` Every nonzero exit prints an actionable message to stderr naming the
resolution, per D-016. Unknown project slug MUST list the valid slugs.

## 12. Fresh vault scaffold

`[script]` **`zk_config.py --init`** creates a vault. Explicit, never implicit — D-006
forbids silent vault creation. **Create-only: it refuses a nonempty target.** On success
it prints the next step (set `ZK_VAULT`, or write `zk.toml`), and D-006's no-vault error
names this command.

1. `mkdir` `projects/`, `topics/`.
2. Write `index.md` with the header and zero groups.
3. Nothing else. No sample project, no placeholder notes.

**`private/` and `archive/` are not created** (D-061). They self-create on first use.

*Territory vs. reserved names:* `projects/` and `topics/` are **territory** — places the
schema routes writes into, so they must exist. `private/` and `archive/` are **reserved
names** — a rule about what §9 excludes, and a name rule needs no directory. Pre-creating
one is a **stub of a purpose**; `archive/` is the sharper case, since its documented
purpose is holding a legacy vault a fresh install does not have. Git tracks neither empty
directory anyway.

The resulting `index.md` is a header and zero groups — truthful self-description with
`notes: 0` (§8).

`[script]` **`--init` calls `zk_index.py`'s render path; it does not write `index.md`
itself** (D-062). `index.md` has exactly **one author**, so byte-identity between what
init writes and what the next `zk_index.py` run renders holds **by construction** — §8's
determinism contract cannot break on the user's first command, because there is no second
implementation to drift.

**Ground state** — `--init`'s test expectation, and the base fixture every other test
vault extends:

```
<vault>/
├── index.md      # header only: notes: 0, no groups
├── projects/     # empty
└── topics/       # empty
```

A vault with no projects is valid. `zk_recall.py <anything>` on it exits 1 — but with
**its own message**, not a populated-vault message with an empty list (D-062, D-052's
pattern):

```
zk: this vault has no projects yet.
  Run /zk:recall <slug> to create the first one.
```

`Known projects:` followed by nothing is a line that trails off, and it implies a lookup
failed against a populated set. `[script]` The zero-slug vault is a **message-test
fixture**: any message template interpolating a collection needs an empty-collection
case, because the zero case is where a template degrades and is exactly the case its
author never has in front of them.

## 13. Conforming examples

`[script]` **These are renderings of lint-verified fixture files** (D-063) — the §12
ground state plus deltas — not prose typed into this document. A conformance test asserts
them clean forever; an example is instruction-shaped, so a stale one is an instruction
trap inside the document that bans them.

**Section licence.** Examples are **non-normative**. Conflicts between an example and a
rule resolve **toward the rule**. Annotations describing *the example itself* are legal
(§8's self-description principle); comments *explaining a rule* are banned — that is
restatement, and every rule has one normative home (§0).

**A shape earns a rendering when multiple conventions interact** and their interaction is
not derivable from any single rule. That criterion, not a census, decides what appears
here — `project.md` is absent because a closed section vocabulary is a single-rule shape,
and single-rule shapes are their own example.

`projects/game-x/log/2026-08-14-save-system.md`:

```markdown
---
type: log
project: game-x
tags: [save-system, serialization]
updated: 2026-08-14
summary: Save format moved to versioned JSON; v1 loader kept for migration until 0.9
---

## Done
- Replaced pickle serializer with versioned JSON at `src/save/format.py`.
- Added `schema_version` to the save header; loader dispatches on it.

## Decisions
- Versioned JSON over pickle — see decisions.md D-004.

## Gotchas
- `Path.write_text` defaults to platform newlines; saves diffed dirty on Windows.
  Pass `newline="\n"`.

## Next
- Delete the v1 loader once 0.9 ships.
```

*Exercised deliberately:* no `status` field (§4 — logs have no lifecycle); the wrapped
`## Gotchas` bullet, which is one list item under §6's CommonMark continuation rule and
sits exactly at the two-sentence cap.

`projects/game-x/decisions.md` — five conventions meet here: container frontmatter,
contiguous zero-padded IDs, newest-at-bottom, the marker grammar, and a partial scope
tail.

```markdown
---
type: decision
project: game-x
tags: [save-system, tilemap, input]
updated: 2026-09-02
summary: Decisions on save format, compression, tilemap chunking, and input rebinding
---

## D-001 — 2026-07-28 — Store action names, not scancodes
- Decision: input rebinding persists action names; scancodes resolve at load.
- Why: scancodes are layout-dependent and broke on non-QWERTY keyboards.
- Rejected: scancodes plus a layout tag — the tag goes stale on OS changes.

## D-002 — 2026-08-11 — Chunk the tilemap at 64x64
- Decision: autotile recalculation operates on 64x64 chunks.
- Why: full-map recalc exceeded one frame past roughly 200x200 tiles.
- Rejected: per-tile incremental updates — correct, but harder to verify.

## D-003 — 2026-08-14 — Versioned JSON over pickle for saves
- Decision: saves are JSON with a `schema_version` header; v1 loader kept until 0.9.
- Why: pickle ties the format to Python internals and blocks external tooling.
- Rejected: msgpack — a runtime dependency, against the stdlib rule.
- superseded-by: D-004 (2026-09-02) — compression clause only

## D-004 — 2026-09-02 — Compress save payloads, not headers
- Decision: the JSON payload is zlib-compressed; the version header stays plain.
- Why: saves passed 4 MB on large maps, and the header must stay readable to sniff.
- Rejected: compressing the whole file — the version header becomes unreadable.
```

*Exercised deliberately:* no `status` field (§4 — a decision log accumulates, it has no
lifecycle); `updated` tracking the last appended entry, not the file's creation; a
domain-list summary with no count (§7.4); D-003's partial marker, whose scope tail is
visible to a reader of D-003 rather than buried in D-004.

`topics/serialization.md`:

```markdown
---
type: topic
tags: [serialization, versioning]
status: active
updated: 2026-08-14
summary: Version the payload header before shipping any serializer; retrofitting needs a sniffer
---

## Rule
- Write `schema_version` from day one. Adding it later means sniffing unversioned blobs.

## Seen in
- game-x save system (2026-08-14)
```
