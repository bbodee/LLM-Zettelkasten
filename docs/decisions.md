# decisions.md — zk rebuild (repo-level)

Append-only. Format: D-NNN, date, decision, why, alternatives rejected.
IDs are sequential serial numbers, unique per file, never reassigned.
Deferred/out-of-scope items live in enhancements.md, not here (see D-005).

## D-001 — 2026-08-14 — Confirm index-based retrieval, no embeddings
- Decision: keep structured-index retrieval. Revisit trigger: index.md no longer
  fits comfortably in context (~2,000 notes is the literature's proxy figure,
  not a prescription — measure, don't count).
- Why: empirical claim (claude-memory-compiler / Karpathy) that LLM-reads-index
  beats vector similarity at personal scale because the LLM understands the
  question, not just similar words; advantage holds while the full catalog is
  visible in one window.
- Rejected: adding optional embeddings now — complexity before evidence of need.

## D-002 — 2026-08-14 — Supersession marker + contradiction check for vault decisions.md
- Decision: vault decision entries get sequential IDs (D-NNN, unique per file).
  Entries stay append-only with one permitted amendment: appending
  `superseded-by: D-NNN (YYYY-MM-DD)` to a replaced entry. /zk:log step 2 reads
  existing entries before appending; if the new decision replaces an old one,
  it appends the new entry AND writes the marker on the old — a pointer, never
  a gate; nothing is blocked or removed.
- Why: supersession rot is the documented #1 weak point of markdown ADRs; stale
  decisions enter every recall bundle looking alive. Automating the marker into
  the log flow (the moment the reversal is fresh) is what keeps it written.
- Rejected: one-file-per-decision (MADR) — team ceremony (PRs, review, per-file
  status) buys nothing at personal scale and loses chronological one-read order;
  strict immutability — date-stamped amendment beats it in practice per the
  canonical ADR repo; hand-maintained "current decisions" header — second source
  of truth that rots (though a *generated* one from markers stays possible).

## D-003 — 2026-08-14 — summary: is retrieval-critical; enforcement split
- Decision: primary enforcement is at write time — zk-log SKILL.md instructs
  dense summaries as notes are drafted. zk_lint backstops mechanically: present,
  one line, minimum length, banned lazy patterns ("worked on", "session notes",
  summary == filename).
- Why: with index-based retrieval the summary line IS each note's retrieval
  surface; a vague summary fails silently — the note simply stops participating
  in recall. Scripts can't judge semantic quality, so the LLM author is the
  contextual linter and the script catches detectable laziness.
- Rejected: presence-only validation; a mechanical quality heuristic beyond
  pattern-matching (doesn't exist). Semantic lint pass → enhancements.md E-001.

## D-004 — 2026-08-14 — Read-before-write rule in zk-log
- Decision: zk-log SKILL.md instructs: before updating project.md or any
  existing topics/ note, read the current version into context and write the
  merged result; never generate the file from conversation context alone; never
  append a section that already exists.
- Why: session context contains only this session — an update written without
  reading destroys prior content by omission, not decision. Silent knowledge
  loss defeats the vault's reason to exist. Instruction is the cheapest rung;
  Claude Code's Edit tool partially mitigates (refuses edits to unread files),
  leaving whole-file writes as the exposed surface.
- Rejected: hook enforcement now (needs read-state tracking infrastructure;
  promotion path → enhancements.md E-002); lint (sees the file only after the
  old content is gone).

## D-005 — 2026-08-14 — Split enhancements.md out of decisions.md
- Decision: decisions.md records only durable choices that bind future work.
  Deferrals and out-of-scope discoveries go to repo-level enhancements.md;
  entries there carry an optional `trigger:` field (deferral = enhancement with
  a named trigger; enhancement = one without). A fired trigger graduates the
  entry into work via a new decisions.md entry, or is consciously re-parked.
- Why: letting deferrals into decisions.md dilutes it into a journal, degrades
  its signal, and pads every context read of the file; the survey generated
  four parked items with no home.
- Rejected: recording deferrals as decision entries (the dropped draft D-005);
  cross-linked separate deferral/enhancement files — the trigger field makes
  one file sufficient.

## D-006 — 2026-08-14 — Dev/test vault: hard error on no config; fixtures ≠ demo
- Decision: missing vault config exits nonzero naming `ZK_VAULT` and `zk.toml`;
  never a silent default. `zk.toml` is gitignored, `zk.toml.example` committed.
  Tests set `ZK_VAULT` explicitly at `tests/fixtures/vault/`, copied to
  `tmp_path` per test so writing scripts (`zk_index.py`, `zk_lint.py --fix`)
  never dirty the working tree. The user-facing demo vault is a separate, later
  deliverable — not the test fixture. A synthetic `private/` note is committed
  under fixtures on purpose: "never write into `private/`" governs the live
  vault at runtime, not an adversarial fixture.
- Why: a committed default vault silently absorbs logs from a user who forgot
  to configure their real vault — misrouting the exact content the vault exists
  to preserve. Fixtures and demos pull opposite ways: fixtures want minimal and
  adversarial, demos want rich and legible.
- Rejected: committed `zk.toml` pointing at a bundled vault (silent misroute);
  one vault serving both roles (mutating tests dirty the tree; content goals
  conflict); purely programmatic fixtures (unwieldy once tests need real bodies).

## D-007 — 2026-08-14 — Packaging: standalone repo, manual install
- Decision: `zk` ships as a standalone repo. Install = user symlinks or copies
  `skills/zk-recall/` and `skills/zk-log/` into their project's
  `.claude/skills/`, and sets `ZK_VAULT`. No plugin manifest, no marketplace
  packaging in v1. README documents the step.
- Why: distribution polish before a working module is wasted work; the manual
  step is two commands and trivially reversible. Keeps the v1 surface at five
  scripts plus two SKILL.md files.
- Rejected: marketplace-style plugin dir (→ enhancements.md E-007);
  `.claude/skills/` checked into each consuming project — duplicates the skills
  per project and fans every update out by hand.

## D-008 — 2026-08-14 — Build order: scripts → skills → demo vault
- Decision: build and verify the five scripts first (pytest green, driven end
  to end from the CLI), then author the two SKILL.md files and iterate them
  against live sessions, then seed the demo vault last. Skills remain in v1
  scope — this is sequencing, not descoping.
- Why: skills are non-deterministic and can only be validated by live
  triggering; exercising them over unverified scripts confounds two failure
  sources. A verified script layer makes every skill failure a skill failure.
  The demo vault comes last because it should showcase finished behavior,
  including private-note exclusion.
- Rejected: skills-first or in parallel (couples LLM-behavior debugging to
  script debugging); dropping skills from v1 — contradicts CLAUDE.md
  non-negotiable 2 and acceptance criteria 5–6, and without `/zk:log` there is
  no automatic lint+index and no cross-session memory, only a vault CLI.

## D-009 — 2026-08-17 — `type: decision` labels the container, not an entry
- Decision: `projects/<slug>/decisions.md` carries normal note frontmatter with
  `type: decision`; individual `D-NNN` entries are `##` blocks in the body with
  no frontmatter of their own. File-level `status: active` describes the file
  and never changes — per-entry status is carried solely by `superseded-by`
  (D-002). `updated` = date of the last appended entry. The file therefore gets
  one line in `index.md`, whose `summary:` MUST be phrased as a domain list
  ("decisions on save format, tilemap storage, input rebinding"), never a count.
  `/zk:log` refreshes that summary in the same step it appends an entry.
- Why: the `type` enum lists `decision` but D-002 rejected one-file-per-decision,
  leaving the value with nothing to label. Labelling the container keeps decision
  logs visible in the catalog. The maintenance cost is near zero because D-002
  already requires `/zk:log` to read the whole file before appending (to detect
  supersession) — the summary refresh rides along on a read that already happens.
  Domain phrasing is what makes it survive: a count is wrong on the very next
  append, a domain list only goes stale when a genuinely new domain appears.
- Rejected: dropping `decision` from the enum so decisions.md carries no
  frontmatter and never appears in `index.md` — `zk_recall.py` pulls it by path
  either way, but decision logs would then be invisible to any cross-project
  browse; per-entry `status` fields (redundant with `superseded-by`, and the
  exact status-rot failure D-002 documented); count-based summaries (stale on
  next append, and lint cannot detect the drift — semantic backstop is E-001).
- superseded-by: D-032 (2026-08-17) — status clause only

## D-010 — 2026-08-17 — Recall's "index section" is computed, not stored
- Decision: `index.md` stays a single global file grouped by type, exactly as
  problem.md specifies. `zk_recall.py` synthesizes step 1 of the bundle at read
  time: every index line whose path starts with `projects/<slug>/`, plus Topics
  lines whose tags intersect the project's tags, group headers preserved. No
  per-project index file exists on disk and the index format is unchanged.
- Why: problem.md's phrase "the `index.md` project section" names a region that
  does not exist — grouping by type scatters a project's lines across four
  groups, interleaved with every other project. Computing the view costs one
  prefix match (the path is project-first, so one rule catches project.md,
  decisions.md, and every log) and keeps the whole catalog visible in one window,
  which is the precondition D-001's retrieval bet depends on. Recording it stops
  a future session from "fixing" the index format to create the missing section.
- Rejected: a two-tier pointer index (root = one line per project + full topic
  list, plus `projects/<slug>/index.md` per project) — scales with project count
  rather than note count and would push D-001's ceiling out by an order of
  magnitude, but kills cross-project scanning, which is the harder question and
  the one E-004 predicts degrades first; design sketch parked at E-008. Also
  rejected: grouping `index.md` by project then type (topics have no project and
  need a floating group anyway; cross-project browsing gets worse).

## D-011 — 2026-08-17 — `project.md` has a closed section vocabulary
- Decision: `project.md` uses a fixed H2 set. Required and always present:
  `## Stack`, `## Conventions`, `## Current state` — missing one is a lint error,
  and `zk-recall`'s scaffold interview fills them at creation. Optional and
  omitted entirely when unused: `## Constraints`, `## Glossary` — present but
  empty is an error. Any other H2 is a warning, not an error. `topics/` notes
  stay free-form; no vocabulary, no required sections.
- Why: D-004's "never append a section that already exists" is only enforceable
  if "exists" is decidable. Free-form headings make it undecidable — a session
  reads `## Stack` and writes `## Tech Stack` because it judged that name more
  apt, and now two sections both look current with no way to tell which is
  authoritative. That fails quietly, the same way D-004's clobber does. A closed
  vocabulary converts an LLM judgment call into a string match. Locking it now is
  free: per D-008 no scripts or skills exist yet, so nothing migrates.
- Rejected: free-form headings relying on D-004's instruction alone (fragments
  rather than clobbers — same silent loss, different mechanism); erroring on
  unknown H2 (project.md is the note most likely to be hand-edited; hard-failing
  someone's own file over an idiosyncratic heading is not worth it); imposing the
  same vocabulary on `topics/` (heterogeneous by nature; would yield empty
  headings). Note: this makes a stale `## Current state` findable in a fixed
  place, it does not fix it — research.md #4's stale-charter gap stands.

## D-012 — 2026-08-17 — `index.md` is byte-deterministic; timestamp tracks content
- Decision: identical vault content MUST render byte-identical output — pinned
  sort (`updated` desc, then path asc as tiebreak), explicit `\n` newlines,
  forward-slash paths on every platform, no iteration order leaking into output.
  `zk_index.py` renders, compares against the file on disk ignoring the
  `generated:` line, and writes only when content differs; a no-op run leaves the
  file completely untouched. `generated:` therefore means "when the catalog last
  changed." `--check` reports the same comparison without writing.
- Why: acceptance criterion 4 ("`--check` stable, second run = no diff") is
  unsatisfiable as literally written — the timestamp is regenerated every run, so
  a naive byte comparison is 100% false positive. Suppressing no-op writes needs
  the same ignore-the-timestamp comparison as a bare carve-out, so it is the same
  work spent better: the timestamp becomes informative, and a vault synced through
  OneDrive stops churning on runs that changed nothing.
- Rejected: carve the timestamp out of `--check` but always rewrite the file (the
  weaker half of the same mechanism; leaves `generated:` meaning "last time the
  script ran" and thrashes sync); dropping the timestamp entirely (problem.md
  requires it, and it is the cheapest staleness signal for a human); leaving the
  sort tiebreak unpinned — same-day notes could swap between runs and produce
  phantom diffs indistinguishable from real ones, surfacing as flaky tests.

## D-013 — 2026-08-17 — Normative words carry strength; enforcement is tagged by rung
- Decision: SPEC.md uses RFC 2119 keywords for obligation strength only (MUST =
  hard requirement, SHOULD = strong recommendation, MAY = explicit permission —
  unchecked but deliberately granted, not out of scope). Enforcement is stated
  per rule via three tags, never inferred from the verb: **[lint]** = a property
  of a file on disk, checked by `zk_lint.py`, MUST → error and SHOULD → warning;
  **[script]** = behavior of a `zk_*.py` script, verified by pytest; **[skill]** =
  behavior of `zk-recall`/`zk-log`, instruction in SKILL.md with nothing
  mechanical verifying it. An unmarked MUST is [lint].
- Why: the draft header bound MUST directly to "lint error," which is false for a
  third of the document. `zk_lint.py` reads files; it cannot know whether the
  skill read a file before writing it, refreshed a summary in the same step, or
  whether the index renders deterministically. Lint's job is to evaluate whether
  an entry is valid — read-before-write and summary refresh are outside its
  purview. The three rungs are not new: D-003 already split write-time from lint,
  D-004 named instruction as "the cheapest rung," and D-008 separates script
  verification from skill iteration. SPEC.md was collapsing all three onto lint.
- Consequence: every [skill] tag marks a known soft spot — nothing verifies it.
  That tag set is exactly the population E-002 would harden if promoted to hooks.
- Rejected: narrowing the keywords to strength only and leaving enforcement
  implicit in §10's table (severity is then discoverable only for rules that
  happen to have a ZK code — script and skill obligations have none); keeping the
  verb→lint mapping and listing exceptions inline (the exceptions are ~a third of
  the MUSTs, so the rule would be the minority case).

## D-014 — 2026-08-17 — `ZK_VAULT` outranks `zk.toml`; every script announces its vault
- Decision: resolution order is `ZK_VAULT` first, then `zk.toml` searched from cwd
  upward to the filesystem root, first hit wins (D-006 already fixes "neither
  found" as a hard error). Every script prints one line to **stderr** on startup
  naming the resolved vault and the mechanism that chose it —
  `zk: vault /path/to/vault  (from ZK_VAULT)`. Stderr specifically: `zk_recall.py`
  emits its bundle on stdout, and a banner there would land inside the context
  bundle.
- Why: prior docs said "env var or zk.toml" without ranking, leaving the
  both-exist-and-disagree case undefined. Precedence follows overridability —
  only the env var can be redirected for a single invocation, so if the file won,
  the env var would be dead weight. It also protects D-006: tests point `ZK_VAULT`
  at a fixture, and a stray `zk.toml` up the tree outranking it would run mutating
  tests (`zk_index.py`, `zk_lint.py --fix`) against a real vault.
- Consequence, explicitly accepted: an env var is just as set-and-forget as a
  file — the difference is that a file is visible and an env var is not. The
  banner is the mitigation and is doing the real work here; precedence alone does
  not fix the silent-shadow failure, visibility does.
- Rejected: `zk.toml` first (makes the env var useless as an override and
  reintroduces the D-006 test-misroute risk); no banner (both mechanisms fail
  silently and identically — a stale path resolves cleanly and looks correct);
  a `--vault` flag completing the cascade → enhancements.md E-009.

## D-015 — 2026-08-17 — `zk.toml` search is fenced at the repo root
- Decision: the `zk.toml` fallback (step 2 of D-014's order, reached only when
  `ZK_VAULT` is unset) is bounded, never unbounded. Establish the fence first,
  then search: repo root = nearest ancestor of cwd, cwd included, where `.git`
  **exists** — file or directory, not `is_dir()`. Repo found → search cwd upward
  through the repo root inclusive, then stop. No repo → search cwd only, no walk.
  Nothing found within the fence → D-006's hard error, listing every directory
  searched and marking where the search stopped.
- Why: an unbounded walk converts a *deleted* `zk.toml` into a *wrong vault*
  rather than an error — it climbs past the intended root and picks up whatever
  config sits higher, which is the silent-misroute class D-006 exists to prevent.
  D-014's banner reports the wrong vault after the fact; the fence stops it. The
  repo root is what "project root" means in practice and is the same boundary git
  uses, so it needs no explanation in the README. `.exists()` rather than
  `is_dir()` because in a git worktree or submodule `.git` is a *file* holding a
  `gitdir:` pointer — `is_dir()` would silently drop the fence in exactly the
  isolated-agent context where it matters most.
- Scope note: this is the first place `zk` knows git exists. It is one
  `Path.exists()` call, not git integration; problem.md's out-of-scope "git
  automation" means commits and hooks. Recorded so the check does not read as
  scope creep later.
- Consequence: `zk.toml` is gitignored (D-006), so a fresh worktree never has one
  and the fence correctly stops at the worktree root with a hard error. That is
  D-006 working as designed, not a bug. `ZK_VAULT` is the answer — env vars are
  inherited by child processes, which is a third argument for D-014's precedence
  alongside per-invocation override and test isolation.
- Rejected: fencing at the home directory (does not solve the stated problem — a
  stale `~/zk.toml` is still found, which is the antiquated-path case); cwd-only
  everywhere (absolute fence, but breaks running from any subdirectory);
  unbounded walk to filesystem root (the original draft); following the `gitdir:`
  pointer to the main repo before erroring → enhancements.md E-010 — it is real
  git-internals parsing, it punches a hole in the fence just erected, and the
  failure it prevents is already loud with a one-line fix.

## D-016 — 2026-08-17 — Error quality ranking: loud + directed > loud > soft
- Decision: every `zk` error message names the resolution, not just the fault.
  Ranked preference, binding on all scripts: (1) loud error stating what to do
  about it, (2) loud error, (3) soft/silent failure — never (3). Where a parser
  or library exception would surface raw, catch it and re-emit with the fix
  attached; the underlying exception text may follow, but never alone. Where a
  value is wrong but a near-match exists, name the near-match.
- Why: CLAUDE.md already requires "nonzero exit + actionable message"; this
  ranks the cases and makes "actionable" concrete. The upfront config path is
  where a new user meets the tool with the least context to debug it — a raw
  `TOMLDecodeError: Invalid \escape (at line 2, column 12)` is technically loud
  and practically useless. The vault's whole value is cross-session memory; a
  confusing failure at the config step costs the user the tool entirely.
- Rejected: relying on CLAUDE.md's general clause alone (states the floor, not
  the ranking, and does not require re-emitting library exceptions); logging or
  warning where an error is correct (D-006's posture is hard failure over
  clever defaults).

## D-017 — 2026-08-17 — `zk.toml` schema: bare key, absolute path, unknown key errors
- Decision: v1 `zk.toml` is a single bare top-level key, no table —
  `vault = "C:/Users/you/OneDrive/vault"`. The value is an **absolute** path; no
  relative-path resolution. Any parseable TOML string form is accepted (forward
  slashes, doubled backslashes, or a single-quoted literal) — pathlib normalizes
  separators after parsing, so all three work. `zk.toml.example` and the docs
  show forward slashes. An unknown key is a hard error naming the near-match
  (`unknown key 'valut' in zk.toml — did you mean 'vault'?`), never ignored.
  An unescaped-backslash parse failure is caught and re-emitted per D-016 with
  the corrected line shown, not as a raw `TOMLDecodeError`.
- Binding rule: any future enhancement that adds a setting MUST specify its
  `zk.toml` representation explicitly, and MUST convert the file to a `[zk]`
  table at that point (E-011). A second bare key is not permitted.
- Why: prior docs named the file and never its contents. One setting does not
  justify a table — `[zk]` inside a file named `zk.toml` says "zk" twice — and
  the conversion is cheap when a real second setting arrives. Absolute paths
  avoid specifying and testing a resolution base (relative to the file? to cwd?)
  and keep D-014's banner readable without mental resolution. Unknown-key errors
  matter because a typo otherwise falls through to D-006's "no vault configured,"
  sending the user to hunt for a file sitting in front of them. `tomllib` is
  stdlib from Python 3.11, so this adds no dependency — the 3.11 floor in
  CLAUDE.md is load-bearing here, not incidental; on 3.10 it would mean `tomli`.
- Rejected: `[zk]` table now (redundant at one setting → E-011); relative paths
  (→ E-012); rejecting valid backslash forms that parse and work — telling a user
  their correct config is wrong to enforce one style; ignoring unknown keys.

## D-018 — 2026-08-17 — Vault path normalization: expand `~`, collapse, require absolute
- Decision: whatever string arrives from `ZK_VAULT` or `zk.toml` is normalized
  identically — expand `~` (`expanduser`), collapse `.` and `..`, follow symlinks
  and junctions (`Path.resolve()`). The result MUST be absolute; a relative value
  from **either** source is a hard error, never anchored to cwd. No environment
  variable expansion inside the value (E-013).
- Why: `~/vault` must not be read as a literal directory named `~`, and shells
  only expand it before the process starts in some cases — quoted values, `zk.toml`
  contents, and Windows GUI-set variables all arrive unexpanded. `resolve()` over
  `absolute()` because `absolute()` merely prepends cwd and leaves `..` in place,
  so it would not deliver the collapsing behavior. Rejecting relative paths keeps
  D-017's "value MUST be absolute" honest — silently anchoring `../vault` to the
  invocation directory is exactly the kind of clever default D-006 rejects, and it
  would make the same config file mean different things from different shells.
  `expandvars()` is excluded because it leaves unknown variables as literal text:
  `$HOEM/vault` becomes the string `$HOEM/vault` and fails as "directory not
  found" rather than "unknown variable" — the undirected failure D-016 bans.
- Consequence: `resolve()` follows symlinks and junctions, which OneDrive uses, so
  D-014's banner may print a path differing from what the user typed. Correct — it
  is the real location — but occasionally surprising, and worth a README note.
- Rejected: `absolute()` (no collapsing, no symlink truth); env var expansion in
  v1 (→ E-013); anchoring relative paths to cwd (contradicts D-017); anchoring
  them to the `zk.toml` file's own directory (that is E-012's proposal, deferred).

## D-019 — 2026-08-17 — Exit codes are graded, and the grading test is "did it do its job"
- Decision: three codes, assigned by a stated test rather than by a lookup table.
  **The test: did the script get to do its job?** Completed its work and reports a
  result → 0 if positive, **1** if negative. Could not do its work at all → **2**.
  Tiebreak for genuine ambiguity: if the same command, unchanged, would fail
  identically for *every* possible invocation in this environment, it is 2;
  otherwise 1. A resolved vault path that is missing or not a directory is 2 — no
  argument could make that invocation work.
- Worked examples: unknown project slug → 1 (recall ran, looked, reported nothing
  found). Lint found errors → 1 (lint ran to completion; the findings *are* the
  result). `--check` reports a diff → 1 (the check ran and answered). No vault
  configured, vault path missing, vault path is a file, bad flag → 2 (nothing ran).
- Why: CLAUDE.md requires a nonzero exit and D-006 requires one for absent config,
  but neither grades them, so every new error would be sorted by feel. Grading only
  pays off if the grading is predictable — a table without a test produces a coin
  flip at the first borderline case and a wrong sort actively misleads, which is
  worse than no distinction. The distinction exists for future callers: a wrapper
  looping `zk_lint.py` over a vault must tell "this note has errors" (keep going)
  from "the vault is gone" (abort) without parsing message text. Follows the
  familiar grep/diff shape — 0 found, 1 not found, 2 something broke.
- Binding rule: every new failure path in any script MUST be classified by this
  test as part of the change that introduces it, and the classification stated
  where the error is specified. No unclassified nonzero exits.
- Rejected: a single nonzero code (loses the abort/continue distinction and forces
  text parsing); grading by severity or by which script raised it (neither is
  decidable from the caller's side); leaving the table without a test (the actual
  defect in the draft — it named the codes and not the rule).

## D-020 — 2026-08-17 — Project slugs resolve to three states, shared across both skills
- Decision: `project.md` is the test for whether a slug is a project, but the
  resolver returns three states, not a boolean. `resolve_project(slug)` lives in
  `zk_read.py` (the vault-walking chokepoint) and returns: **CHARTED** —
  `projects/<slug>/project.md` exists; **UNCHARTED** — the directory exists,
  `project.md` does not; **ABSENT** — no such directory. Both failure states exit 1
  per D-019 (the script ran, looked, reported). Messages differ per D-016:
  UNCHARTED names the missing file and offers to scaffold the charter; ABSENT lists
  the known slugs and offers to scaffold a new project. The list of known slugs is
  built by scanning for `project.md`, so UNCHARTED directories do not appear in it.
  Follow-up actions are per skill: `zk-recall` interviews and scaffolds;
  `zk-log` refuses to write against a non-CHARTED slug.
- Decision (indexing): an UNCHARTED directory's logs **are** indexed normally.
  `index.md` may therefore list Logs lines for a project absent from the Projects
  group. Lint raises the missing charter (ZK024, error); the index does not hide
  content over it.
- Why: no prior doc said what makes a slug *known*, so recall's "unknown project"
  branch had no defined trigger. A boolean collapses two different situations with
  different fixes — a half-created directory needs one file, a missing project
  needs a full interview — and reporting "unknown project 'game-x'" while
  `projects/game-x/` sits on disk is exactly the misdirected error D-016 bans.
  Orphaned logs are indexed because under index-based retrieval (D-001) an
  unindexed note effectively does not exist; silently dropping valid notes is the
  quiet knowledge loss the vault exists to prevent, and the charter gap is a lint
  problem, not a reason to hide content.
- Rejected: directory presence as the test (a half-made directory would report as
  a real project and assemble a bundle from nothing); `index.md` membership as the
  test (circular — the index is generated from what is found); skipping UNCHARTED
  directories in the index (writing a log, seeing it succeed, and finding it absent
  from the catalog is the worst available outcome).

## D-021 — 2026-08-17 — No stub files; recall omits empty sections silently
- Decision: a scaffolded project is exactly one file, `project.md`. `decisions.md`
  and `log/` are created on first write and their absence is never an error — no
  stubs, no placeholders. `zk_recall.py` omits absent sections from the bundle
  **entirely**: no empty headers, no "no decisions yet" commentary, no state
  narration of any kind. The bundle opens with one factual inventory comment
  listing only what it actually contains —
  `<!-- zk: game-x | charter, 4 decisions, 5 logs, 2 topics -->` — where absent
  categories simply do not appear. This is the acceptance-criteria-6 path: recall
  on a fresh project → scaffold → work → `/zk:log`.
- Why: an empty `decisions.md` still needs valid frontmatter, including a summary
  that D-009 requires to be a domain list — and no domain list truthfully
  describes zero decisions, so the stub would ship a lie into `index.md`, the
  exact surface D-001's retrieval depends on being dense. Empty `log/` is more
  benign but git does not track empty directories, so it would not survive a
  clone regardless. In the bundle, placeholder headers and absence commentary
  spend context tokens to convey nothing; omission conveys the same fact for free.
- Note on the asymmetry with D-020: a missing `project.md` is an error, a missing
  `decisions.md` is not. The charter *declares* what a project is; decisions and
  logs *accumulate*. Declared things must exist; accumulated things must not be
  faked.
- Note on counts: the inventory comment uses counts, which D-009 bans for
  `decisions.md` summaries. Not a contradiction — the comment is regenerated on
  every run and cannot go stale, whereas a summary is written once and drifts.
- Rejected: scaffolding empty `decisions.md` and `log/` upfront (stub summary is
  unwritable truthfully, and it consumes an index line); printing empty section
  headers in the bundle (tokens for no information); narrating absence in prose
  ("this project has no decisions yet" — commentary, not content).

## D-022 — 2026-08-17 — Unrecognized top-level dirs warn; `zk.toml` gains an ignore list
- Decision: unrecognized top-level directories are **warned**, not silently
  ignored, in two flavors — ZK025 plain (`'.obsidian/' is not in the vault
  schema`) and ZK026 near-miss (`'project/' is not in the vault schema — did you
  mean 'projects/'?`), matched with stdlib `difflib.get_close_matches`. The
  near-miss message leads with the correction, never with the silence option.
  Both messages name the remedy per D-016. To make the warnings survivable,
  `zk.toml` gains an `ignore` list — which fires D-017's binding rule, so the
  file converts to a `[zk]` table now and **E-011 graduates**:
  `[zk]` / `vault = "..."` / `ignore = [".obsidian", "attachments"]`.
- Semantics of `ignore`, deliberately narrow: exact top-level directory names
  only, no globs or paths; it silences warnings and grants nothing — an ignored
  directory is still never indexed, linted, or recalled; listing `private` or
  `archive` is a hard error, not a no-op, so nobody believes it did something.
- Prompting belongs to the skill, not the script: scripts are non-interactive and
  a blocking question would hang a batch run. The script states the remedy
  (`[script]`); `zk-log` may offer to perform the edit conversationally
  (`[skill]`) — the D-013 rung split.
- Why: silence is the failure mode this schema keeps producing. A typo'd
  `project/` makes every note inside invisible — unindexed, therefore
  nonexistent under D-001's retrieval model — and weeks of logs could accumulate
  there unnoticed. But a warning that fires forever with no way to silence it is
  worse than silence, because the user stops reading warnings entirely. Warning
  plus suppression is the only composition that survives daily use: `.obsidian/`
  gets silenced once, `project/` gets caught.
- Rejected: silent ignoring (the drafted behavior — loses the typo case);
  warning with no suppression (trains the user to ignore all warnings); erroring
  on unrecognized directories (Obsidian creates `.obsidian/` unprompted; failing
  because the user's notes app made a config folder makes the tool unusable);
  glob patterns in `ignore` (barebones first, same call as D-017's bare key).

## D-023 — 2026-08-17 — Enhancement entries get a `graduated-by:` marker
- Decision: `enhancements.md` stays append-only, with one permitted amendment —
  appending `graduated-by: D-NNN (YYYY-MM-DD)` to an entry whose work has been
  built. Exactly mirrors D-002's `superseded-by:` rule for decisions: a pointer,
  never a gate; the entry is not deleted, not rewritten, and its original text
  including the trigger stays readable. An entry consciously re-parked instead of
  graduated gets no marker — D-005 already covers that path, and the absence of a
  marker is what "still open" means. Applied retroactively to E-011, graduated by
  D-022.
- Why: the same rot D-002 documented for decisions applies here. An enhancement
  that has shipped still reads as live, so a future session re-proposes work that
  already exists, or worse, treats a fired trigger as unfired. Enhancements are
  reviewed in bulk at the 20-log checkpoint, which is exactly the moment stale
  entries cost the most. The marker is written at the moment of graduation, when
  the connection is fresh — the same reason D-002 automated its marker into the
  log flow.
- Rejected: deleting graduated entries (loses the trigger and the reasoning, which
  are the parts worth keeping — the enhancement records *why* it was deferred, and
  that context explains the decision that graduated it); a separate "shipped" file
  (second source of truth, and the cross-reference rots); status field per entry
  (the marker is a pointer to a dated decision, which is strictly more useful).

## D-024 — 2026-08-17 — Warnings never enter the bundle; the bundle is retrieval surface
- Decision: stray files are skipped silently by `zk_index.py` and `zk_recall.py`
  and reported by `zk_lint.py` — and the asymmetry is ratified on this reason:
  **the bundle is retrieval surface, not a report.** Everything in it is consumed
  as knowledge by the reading model. Diagnostics belong to lint (auto-run by
  `/zk:log`, so they are seen in practice) and MAY additionally go to
  `zk_recall.py`'s **stderr**. They MUST NOT appear on stdout in the bundle,
  in any form — not as comments, not as headers, not as prose.
- Why: a warning inside the bundle is indistinguishable from content to the model
  reading it. At best it spends context tokens conveying nothing about the
  project; at worst it is treated as a fact about the domain. The same
  stdout/stderr split already governs D-014's vault banner and D-021's omission of
  absent sections — this generalizes it into a rule rather than three coincidences.
  Lint being invoked automatically by `/zk:log` is what makes silence in the read
  path affordable: the diagnostics still surface, on the write path, where acting
  on them is the current task.
- Why the asymmetry is defensible against D-022's opposite call: a stray directory
  can hide an entire project's worth of invisible work and is caught once, at the
  vault level; a stray file is one note, and the type/location coherence family
  now catches the dangerous subset of those with a directional error.
- Rejected: warnings in the bundle (pollutes retrieval surface); recall failing on
  stray files (a malformed note elsewhere must never block loading context for the
  project at hand); silence in lint too (the drafted asymmetry's weaker half —
  lint exists to say the vault is malformed).

## D-025 — 2026-08-17 — One slug format everywhere; the reason is join consistency
- Decision: `^[a-z0-9]+(-[a-z0-9]+)*$` governs project slugs, topic slugs, and log
  topic slugs — directory names and filenames alike, not just tag values. Invalid
  slugs are a hard lint error (ZK031) with a **directional** message naming the
  kebab form. `--fix` never corrects it: renaming is a file move, prohibited under
  D-024. `[skill]` The skills normalize conversationally *upstream* — a user who
  types `game_x` is offered `game-x` before anything is created, so the error is
  the backstop, not the primary interface.
- Why (primary): tags are lowercase-kebab by problem.md, and topic→project joins
  are exact string matches on tags. If a directory may be `save_system` while its
  tag must be `save-system`, every join becomes a normalization question and every
  script needs a canonicalization step that must agree everywhere. One format
  everywhere means no normalization anywhere — that is the load-bearing reason.
- Why (secondary): case-insensitive filesystems make `Game-X` and `game-x` collide.
  Real, since the vault lives on Windows while the scripts must run on POSIX too —
  but it explains only the case rule, not the underscore ban. The drafted
  rationale gave this reason alone, which under-argued the actual constraint.
- Gaps closed: the log topic slug obeys the same regex; the date prefix is
  fixed-width, so parsing is positional — `stem[:10]` is the date, `stem[10]` MUST
  be `-`, `stem[11:]` is the topic slug. Slugs are capped at 60 characters (ZK032,
  error). Absolute resolved path over 240 characters is a warning (ZK033) — 20
  characters of headroom under Windows' 260-character limit, warning rather than
  error because the overflow depends on where the user's vault lives, which is not
  the note's fault.
- Rejected: normalizing invalid slugs automatically (a file move, prohibited by
  D-024, and a wrong guess relocates real content); permitting underscores (breaks
  the tag join); a warning rather than an error (an invalid slug propagates into
  every path and tag referencing it — cheap to fix at creation, expensive later);
  path length as an error (machine-dependent, and the user cannot fix it by
  editing the note).

## D-026 — 2026-08-17 — A log's `updated` is its tamper detector, not a duplicate date
- Decision: a log's filename date is **immutable identity** — when the work
  happened, fixed at creation, never moved. `updated` MUST equal it **always**,
  not merely at creation. `updated` is retained on logs specifically because that
  equality is what makes an edit detectable. ZK020 becomes bidirectional:
  `updated` **earlier** than the filename date is an **error** (malformed — one of
  the two is simply wrong); `updated` **later** is a **warning** worded as an
  immutability violation, naming the remedy (record a new log, do not edit this
  one). `index.md` sorting is unchanged — still `updated` descending, which for
  logs is by construction the same order as filename date.
- Why: problem.md put the date in a log twice — in the filename and in
  frontmatter — and never related them, so the pair looked redundant. It is not.
  D-021 made logs immutable, and an immutability rule with no detector is an
  instruction nobody can audit. Equality-always turns `updated` into exactly that
  detector: the only way the two can disagree is if someone edited a note that was
  not supposed to change. The redundancy reading would have deleted the one signal
  that D-021 is being honored.
- Why the asymmetric severity: `updated` earlier than the filename is
  incoherent — no sequence of legitimate operations produces it, so it is
  malformed data. `updated` later is coherent and merely disallowed; the file
  records something real that happened, and the right response is to redirect the
  author to a new log rather than reject the content.
- Rejected: agreement only at creation with drift permitted afterward (drift is
  precisely the signal worth catching); dropping `updated` from logs as derived
  (it is derived only while the immutability rule holds — its value is detecting
  when it does not); a one-directional warning (the drafted rule, which ignored
  the direction that indicates tampering); sorting the index by filename date for
  logs (a second sort key for one type, buying nothing while the dates agree).

## D-027 — 2026-08-17 — Log name collisions take a counter suffix; writes are create-only
- Decision: a second log with the same date and topic slug becomes
  `<topic>-2`, then `-3`. The suffix is chosen as **highest existing plus one**,
  never by filling a gap left by a deleted file — filenames are identity, and
  identities are not reissued (the same principle as D-002's never-reassigned
  `D-NNN`). Separately and independently: **log writes are create-only.** If the
  resolved filename exists at the moment of writing, exit 2 (D-019 — the script
  could not do its job). Never-overwrite is its own contract and does not depend
  on the naming scheme being correct.
- The suffix is unrecoverable by design: `save-system-2` is a legal slug under
  D-025 and is indistinguishable from a topic genuinely named `save-system-2`.
  **Nothing may parse it.** No script may infer collision order, count, or
  sequence from a filename. The counter exists to produce a free name, and its
  meaning ends there.
- Why a counter and not a timestamp: `2026-08-14T1430-save-system.md` is
  self-describing and never collides, but it breaks D-025's fixed-width positional
  parse (`stem[:10]` date, `stem[10]` separator, `stem[11:]` topic), lengthens
  every filename against ZK033's 240-character path budget, and drags time-format
  questions into a schema that has needed only dates.
- Why highest-plus-one: gap-reuse would let a new log inherit the name of a
  deleted one, so any external reference — a wikilink, a `## Next` bullet, a note
  in another project — silently resolves to different content than it did before.
  Skipping the gap costs one integer and nothing else.
- Why create-only is separate: the collision rule is the *expected* path and the
  create-only check is the *backstop*. A bug in suffix selection, a race between
  two writes, or a hand-created file all produce the same danger — silent
  destruction of an earlier log — and D-004's read-before-write does not cover
  log creation. This is that gap closed.
- Rejected: timestamp filenames (above); gap-reuse (above); overwrite-with-backup
  (a backup nothing indexes is not recoverable in any practical sense); prompting
  on collision (scripts are non-interactive per D-022).

## D-028 — 2026-08-17 — Encoding invariants are enforced by a meta-test, not by memory
- Decision, three parts. (1) `zk_read.py` opens with `utf-8-sig` — tolerant, and
  **only at the chokepoint**, so BOM handling exists in exactly one place. (2) Lint
  flags a BOM anyway (ZK034, warning, `--fix` strips it) with a directional message
  naming the likely source: Notepad and Windows PowerShell 5.1 `Out-File`/`>`.
  Tolerating it in our reader does not make it harmless — the vault must stay
  readable by any agent, per the LLM-agnostic requirement, and a BOM breaks naive
  `startswith("---")` frontmatter checks elsewhere. (3) Standing `[script]` rule,
  paired with D-018's `newline="\n"`: **no bare `open()`** anywhere in `scripts/` —
  `encoding="utf-8"` explicitly on every call, `newline="\n"` on every write.
- Enforcement: a **meta-test** that scans `scripts/*.py` source for violations —
  `open(` without an `encoding=` argument, write modes without `newline=`. Not a
  code-review convention, not a note in CLAUDE.md. The invariant is enforced by a
  test that fails, because the failure it prevents is silent.
- Why: on Windows, `open()` without an explicit encoding uses the system ANSI
  codepage, not UTF-8. A single forgotten parameter reads and writes cp1252 and
  mangles every non-ASCII character in a note — quietly, on one platform only,
  in a vault whose whole purpose is durable storage. That is more likely than the
  BOM case and worse when it happens. Both failures share a shape: correct-looking
  code, no exception, corrupted data, discovered late.
- Precedent set: **invariants whose violation is silent get a meta-test, not a
  convention.** Applies to any future rule of this shape — the test is the only
  mechanism that survives a contributor who has not read the decision log.
- Rejected: strict `utf-8` at the chokepoint with a hard error on BOM (rejects a
  file that is otherwise perfectly valid, when we can simply read it); tolerating
  BOMs without flagging (the vault degrades for every other reader); relying on
  discipline or review for the bare-`open()` rule (this exact class of bug is what
  discipline reliably misses); a lint rule over `zk`'s own source (lint validates
  the vault, not the repo — that is pytest's job, per D-013's rungs).

## D-029 — 2026-08-17 — Unknown frontmatter keys are cargo: preserved, allowed, inert
- Decision, four parts.
  (1) **Preserved.** `--fix` rewrites frontmatter wholesale, so preservation is an
  explicit contract, not a side effect: every unrecognized key survives with its
  value intact. Guaranteed by a **round-trip fixture** in `--fix`'s test contract —
  a note carrying assorted unknown keys, asserted equal after a fix pass.
  Preservation is **semantic**, not byte-level: values must round-trip equal;
  quoting, flow style, and whitespace may normalize.
  (2) **Key order on write** is canonical-then-original: `type`, `project`, `tags`,
  `status`, `updated`, `summary`, followed by unknown keys in their original
  relative order.
  (3) **Allowed.** The vault is co-tenanted — Obsidian and its plugins legitimately
  write `aliases`, `cssclasses`, `publish`, and plugin keys. Unknown keys are valid
  and, on their own, silent.
  (4) **Inert — unknown keys are cargo.** No script may read, interpret, index,
  join on, sort by, or branch on an unknown key. They are carried, never consumed.
- Near-miss detection (ZK035, warning) fires **only when the lookalike known key is
  absent**: `sumary:` with no `summary:` warns and points at the typo; `sumary:`
  alongside a valid `summary:` is silent, because the failure it would predict does
  not exist. Message is directional at the typo, not at the absence.
- Deliberate asymmetry with D-022, recorded so it does not read as inconsistency:
  an unrecognized *directory* warns plainly, an unrecognized *key* does not. A
  stray directory is always the user's own doing and can hide an entire project's
  work; a stray key is routinely written by other tools that share the vault.
  Warning on every plugin key would train the user to ignore all warnings — the
  exact failure D-022 was trying to prevent, arrived at from the other direction.
- Why preservation is the load-bearing half: the default behavior of
  parse-modify-reserialize is that anything not in the known-keys list vanishes
  silently. Running `--fix` to correct tag casing would delete a plugin's metadata
  with no message and leave a file that looks correct. Same silent-loss shape as
  D-004's clobber and D-021's stub summary.
- Rejected: rejecting unknown keys outright (breaks co-tenancy with Obsidian);
  warning on all unknown keys (noise that devalues every warning); byte-level
  preservation (forces a hand-rolled YAML serializer to keep formatting — large
  cost for no benefit, since the values are what matter); allowing scripts to read
  unknown keys opportunistically (creates undeclared schema that lint cannot
  validate and no one can discover).

## D-030 — 2026-08-17 — Every constraint has exactly one normative home
- Decision: each rule is stated normatively in exactly one place in SPEC.md. Other
  sections that need it **point** to that home; they do not restate it. Where a
  constraint has a lint code, the code's section is the home. A restatement that
  drifts from its home is a defect, and the fix is deletion of the copy, never
  reconciliation of the two.
- Why: SPEC.md stated type/location coherence twice — once in §4 as prose, once in
  §10 as the ZK027–ZK030 family — and the two could disagree while both looked
  authoritative. Duplicated constraints also produce duplicate lint reports for one
  defect, which makes an error count meaningless. This is the same failure D-002
  documented for superseded decisions and D-009 for count-based summaries: two
  sources of truth, one of which silently rots.
- Rejected: allowing informative restatements marked "see §N" (the marking erodes
  on edit and the copy is what gets read); a single flat rules section with no
  topical organization (unreadable for a document that must be usable by a skill
  mid-session).

## D-031 — 2026-08-17 — Type/location is one check; location wins for rule application
- Decision: `type`-declares-X and location-implies-Y are a **single comparison**,
  not two rules. Reported once, under the ZK027–ZK030 coherence family, keyed by
  the **declared** type. The message states both facts and does not guess which
  side is wrong:
  `location implies 'type: log'; frontmatter declares 'type: topic'. Either move
  the file to topics/, or correct the type to log.` `--fix` never resolves it —
  moving is prohibited by D-024, and rewriting `type` would silently pick one of
  two plausible intentions. SPEC §4's clause becomes a pointer to §10 per D-030.
- Decision (rule application): for **applying every other rule**, location is
  authoritative. A note at `projects/game-x/log/x.md` declaring `type: topic` is
  validated as a **log** — fixed sections, filename-date/`updated` equality, the
  lot — while the mismatch is reported. A note cannot escape its location's
  ruleset by mislabeling itself.
- Why error-grade, and the fail-open/fail-closed asymmetry: a *misfiled* note
  (right type, wrong place) fails closed — it is invisible, and the damage is
  bounded to that note. A *mistyped* note fails open — it is found, then
  miscategorized: a log declaring `type: topic` lands in the Topics group of
  `index.md` and gets pulled by tag intersection into the bundles of **unrelated
  projects**, where it presents one project's session notes as cross-project
  knowledge. Damage crosses project boundaries, which is why the family is error
  and not warning.
- Rejected: two independent checks (duplicate reports for one defect, and they can
  disagree); frontmatter as authoritative for rule application (lets a note opt out
  of its location's requirements by editing one line — the log-section rules would
  be trivially evadable); `--fix` rewriting `type` to match location (guesses
  intent; the author may have filed it wrong rather than typed it wrong).

## D-032 — 2026-08-17 — `status` is type-scoped lifecycle, surfaced and automated
- Decision, four parts. Applies P-12's method: ask what job the field actually does
  before deciding whether it earns its place.
  (1) **Restrict.** `status` is lifecycle, and only two types have a lifecycle.
  Required on `project` and `topic`; **MUST be absent** on `log` and `decision` —
  present there is a lint error (ZK004). Logs are immutable (D-021) and a decision
  log only accumulates; neither has states to move between.
  (2) **Split the enum by type.** `project: active | completed | abandoned`.
  `topic: active | deprecated`. One shared enum forced both types through
  vocabulary that fit neither — a project is not "deprecated," a topic is not
  "completed."
  (3) **Surface.** `index.md` marks **non-active states only**, as
  `- projects/game-x/project.md (completed) — <summary> [tags]`. Parentheses, not
  brackets, so it cannot be confused with the tag list. Active notes are unmarked,
  so the common case costs nothing. Bundles include non-active notes with status
  visible and **never filter them** — hiding content is how knowledge dies quietly
  (D-020, D-021, D-024).
  (4) **Automate.** `[skill]` `/zk:log` offers transitions conversationally when
  the session suggests one, per D-002's precedent: a status field nobody is
  prompted to update is a status field that rots. This is the same reasoning that
  put the `superseded-by` marker into the log flow.
- **Supersedes D-009's status clause only.** D-009 gave `decisions.md` a
  `status: active` that "never changes" — a field that never changes carries no
  information, which is the argument for removing it rather than keeping it. The
  rest of D-009 (container typing, domain-list summary, refresh on append) stands
  unchanged.
- Why the field survived the challenge: `deprecated` had no stated effect, nothing
  set it, and it was invisible in the index — three symptoms of a field doing no
  work. But the job is real for projects and topics: a completed or abandoned
  project must stay readable (its `## Current state` and decisions are exactly what
  prevents re-doing abandoned work) while being distinguishable from live work at a
  glance. The defect was scope and plumbing, not the concept.
- Interlock: `completed` is the natural trigger condition for a distillation pass
  over a finished project. See the open question recorded alongside this entry —
  no such enhancement is currently parked.
- Rejected: keeping one shared enum (fits neither type); excluding non-active notes
  from index or bundles (soft delete by another name); leaving the field inert as
  drafted (a signal nothing acts on and nothing displays is dead weight); dropping
  `status` entirely (would lose the only lifecycle marker projects have).

## D-033 — 2026-08-18 — Summary floor drops to 20; each layer gets one failure class
- Decision: `summary` minimum length is **20 characters**, down from the drafted 40.
  The floor's job is reassigned: it detects **non-attempts** (`WIP`, `Fixed it`,
  `notes`), nothing more.
- Three layers, each with exactly one failure class it is competent to detect:
  **length** → non-attempts; **banned patterns** (ZK011) → lazy *shapes*
  (`worked on`, `session notes`, summary equals filename); **semantic quality** →
  E-001's parked job, and no other layer's. This is D-003's enforcement split held
  to: the LLM author is the contextual linter, the script catches detectable
  laziness, and neither reaches into the other's territory.
- Why 40 was wrong in a specific direction: it rejected honest terse summaries —
  `Save format moved to versioned JSON` (35) and
  `Plaid sync dedupes on transaction_id` (36) both name subsystem and change and
  would match a future question well — while accepting
  `Session notes and updates on various items` (41). The length test had both
  cases backwards. Worse, a floor that high trains padding: appending "for the
  project" clears the bar and produces a longer, less useful summary, so the check
  filters only honest brevity while rewarding the failure it exists to catch.
- Audience note: the floor governs **manual writes**. Skill-drafted summaries clear
  20 characters structurally — the write-time rules in §5 produce far longer lines
  as a matter of course. The floor is a backstop for hand-editing, not a target.
- Binding rule for future thresholds: **name the failure class before naming the
  number.** A threshold that cannot say which failure it detects is a guess wearing
  a decimal point, and its number will be wrong in a direction nobody notices. Any
  new numeric limit in SPEC.md states its failure class in the same sentence.
- Rejected: word-count or specificity heuristics (semantic judgment re-entering
  lint through the back door, against D-003's split — a script cannot tell a
  specific noun from a vague one, and pretending otherwise produces confident
  wrong verdicts); keeping 40 (rejects good summaries, rewards padding); dropping
  the floor entirely (loses the one thing length genuinely detects — the summary
  nobody attempted).

## D-034 — 2026-08-18 — Catalog bloat is vault-level; the 200-char ceiling detects packing
- Decision: two checks, split by the layer that can actually measure the failure.
  Method is D-033's — name the failure class before the number. Second consecutive
  entry where that rule changed the answer.
  (1) **Vault-level — index size.** `zk_index.py` measures `index.md` on every run
  including `--check`, and warns on stderr without affecting exit status.
  Failure class: *the flat catalog no longer fits comfortably alongside a working
  session's own content.* Thresholds, stated with their basis rather than asserted:
  **200,000 characters (~50k tokens)** cites E-008; **400,000 (~100k)** cites E-004.
  Basis is ~4 characters per token, and the judgment that a catalog consuming a
  large fraction of a working context has stopped being cheap to load. Honest
  caveat: these are estimates against D-001's "measure, don't count" — they are
  deliberately expressed in characters, not note count, so the measurement tracks
  the actual constraint.
  (2) **Per-note — the 200-character ceiling survives**, re-jobbed. Failure class:
  *multi-topic packing* — a summary that long is usually two summaries, and the
  note behind it is usually two notes. ZK017 stays a warning with a directional
  message offering split-or-tighten. It is the mechanical shadow of a judgment
  E-001 would make properly; lint can see the length, not the seam.
- Self-announcing graduation: the index-size warning names the specific parked
  enhancement whose trigger has fired and points at `docs/enhancements.md`. D-005
  requires fired triggers to graduate via a decision or be consciously re-parked —
  this makes the firing impossible to miss rather than dependent on someone
  remembering to check at the 20-log review.
- Rejected, and recorded because the reasoning is reusable: **the per-note ceiling
  as bloat enforcement — wrong unit.** Catalog bloat is a whole-vault property. One
  250-character summary costs nothing; five hundred 150-character ones cost
  everything, and every one of them passes a per-note check. A per-note limit
  cannot detect a vault-level failure, and dressing it as though it can hides the
  real measurement. Also rejected: dropping the ceiling (loses the packing signal);
  making index size an error (nothing is broken — the vault works, it is just
  approaching a design boundary, and D-019's test puts that at warning, not exit 1).

## D-035 — 2026-08-18 — Banned patterns detect grammatical shape, not vocabulary
- Decision: the ZK011 list shrinks to **shapes** — phrases whose grammatical form
  announces they describe the *act of working* rather than its *result*.
  Start-anchored, case-insensitive: `worked on`, `session notes`, `notes on`.
  D-003's third named check (summary equals filename) stays where it is, a
  separate rule. Demoted to **complete-line anchors only**: `misc`, `various`,
  `wip` — matching only when the entire summary is that word, which is the
  non-attempt class, the floor's cousin. Dropped entirely: `progress`, `stuff`,
  `updates?$`.
- Why those three were wrong: they are vague *words*, not lazy *shapes*, and a
  word list cannot tell vagueness from subject matter. `Progress bar stalls at 99%
  when the download completes early` is a real gotcha rejected for its first word.
  `Rollover math now runs on every ledger update` was rejected by an end-anchored
  pattern. That end-anchor exception — the lone `$` in a start-anchored list, and
  the reason SPEC needed an "unless noted" clause — was the symptom that the list
  had drifted from shape-matching into vocabulary policing.
- Third consecutive confirmation of D-033's method: lint detects grammatical
  shape; vocabulary judgment belongs to E-001. Each time the failure class was
  named first, the rule got smaller and the false-positive class disappeared.
- Binding rule — **the list is data with a single home** (D-030: SPEC §5). It grows
  only from **observed** lazy summaries in the real vault, each addition recorded
  as a decision entry naming the summary that motivated it. Never speculatively:
  every speculative entry in the drafted list was a false positive, which is the
  whole evidence base needed for this rule.
- Observation for the record: the complete-line anchors are **already caught by
  ZK010's 20-character floor** — `misc` is 4 characters, `various` 7, `wip` 3, and
  no single-word summary reaches 20. They fire only in principle. Retained as
  explicit statements of intent rather than active checks; if that redundancy is
  unwanted, the floor alone is sufficient.
- Rejected: keeping the nine-item list (rejects honest summaries on their first
  word, and rewording defeats it without improving anything); expanding the list
  speculatively (the source of every defect found here); moving vague-word
  detection into lint under a different name (D-003's split, three times over).
- superseded-by: D-036 (2026-08-18) — complete-line anchors only

## D-036 — 2026-08-18 — Rules that cannot fire are not listed
- Decision: drop `misc`, `various`, and `wip` from ZK011 entirely. The ZK011 list
  is now exactly D-003's three shapes — `worked on`, `session notes`, `notes on` —
  and nothing else. The intent those words carried moves into the **floor's**
  why-line, where it was already being enforced: the non-attempt class includes
  single vague words, and ZK010's 20-character minimum covers them.
- **Supersedes only D-035's complete-line-anchor clause.** D-035's shape/vocabulary
  distinction, its "list is data with a single home" rule, and its
  grow-only-from-observed-summaries rule all stand unchanged.
- Why: the anchors could never fire. `misc` is 4 characters, `various` 7, `wip` 3,
  and no single-word summary reaches ZK010's 20-character floor — so every input
  they would have caught was already rejected one check earlier. D-035 retained
  them as "statements of intent," which is the defect this entry closes.
- General rule: **SPEC.md has no statements-of-intent category. A rule that cannot
  fire is not listed.** An inert rule is indistinguishable from an active one to a
  reader and to an implementer, so it produces dead code, a dead test, and a false
  impression of coverage. Where the intent is worth recording, it belongs in the
  why-line of the rule that actually enforces it — which is also what D-030's
  one-normative-home principle requires: the enforcement lives in exactly one
  place, and so does the explanation of what it is for.
- Rejected: retaining them as documentation (the reason D-035 got this wrong —
  documentation that looks like a rule will be implemented as a rule); lowering the
  floor so the anchors could fire (inventing a gap to justify filling it).

## D-037 — 2026-08-18 — Drop summary-vs-heading; keep summary-vs-filename; route intent
- Decision: the "summary MUST NOT equal the note's first heading" rule is dropped
  entirely, and its sentence deleted from SPEC §5. D-003's cited
  summary-equals-**filename** check survives untouched.
- The asymmetry, recorded so a future consistency sweep does not collapse the two:
  **filename comparison is slug-vs-prose and genuinely mechanical** — a de-kebabbed
  slug is a shape no honest summary produces by accident, so the check is exact and
  its false-positive rate is zero. **Heading comparison is prose-vs-prose**, where
  exact string equality stands in for "does this summary add anything," which is a
  semantic question. One is a mechanical test; the other is semantic judgment in
  mechanical clothing. They look alike and are not.
- Fourth consecutive confirmation of D-033's method.
- Why dropping beats narrowing: the rule fires only on verbatim copy-paste, and
  only in `topics/` — the first `##` is `## Done` in logs, `## Stack` in charters,
  and a decision title in decision logs, none of which a summary would ever equal.
  A retyped near-duplicate, which is the common case, passes. **A check that
  catches a small fraction of a failure class claims coverage it does not have**,
  and that false impression is worse than the gap, because it stops anyone looking
  for the real mechanism.
- Standing disposal route for this class, going forward: when a mechanical check is
  dropped as semantic, its **intent routes to the relevant SKILL.md as a drafting
  rule**, with E-001 as the eventual backstop. Here: `zk-log` instructs that a
  summary must add retrieval information beyond what the heading and filename
  already carry. The requirement survives at the rung that can actually judge it.
- Housekeeping: the deleted sentence referenced "first H1/H2 heading," but §6
  prohibits H1 entirely — the rule contradicted the document it lived in.
- Rejected: narrowing the check to `topics/` (still prose-vs-prose, still 5%
  coverage, now with a special case); keeping it as cheap insurance (it is not
  free — it is a code path, a test, and a claim of coverage).

## D-038 — 2026-08-18 — Block structure follows CommonMark; the sentence cap covers bullets too
- Decision, three parts.
  (1) **The bullet exemption is the design, not a hole.** Bullets are the goal
  form; paragraphs are the capped exception. ZK012 governing only prose is correct.
  (2) **The cap gains its constitutional other half**: a per-bullet sentence cap of
  2, **warning** grade (ZK036), sharing ZK012's counter. CLAUDE.md's style law
  already said terse bullets; this is the check catching up to the law rather than
  a new requirement. Warning rather than error because a slightly long bullet is
  the desired form done imperfectly, while a paragraph is the wrong form entirely.
  (3) **Block structure follows CommonMark.** Indented continuation lines belong to
  the block above — a wrapped bullet is bullet content, not prose. Fenced code
  blocks are **opaque at any nesting depth**; everything else inherits its
  container's kind.
- Why CommonMark specifically: the vault is opened in Obsidian, which renders
  CommonMark. A linter whose block model disagrees with the renderer reports errors
  the user cannot see by looking at the file — the misdirected-failure class D-016
  bans. It also fixed a live defect: SPEC's own §13 example wraps a bullet, and
  under the drafted definition the spec's sample note failed the spec's own rule.
- Open, deliberately not decided here: ZK012 is **error** grade while its counter
  is admittedly crude (see D-039). A miscount on `e.g.` would produce a hard
  failure on correct prose, and `/zk:log` would then rewrite good text to satisfy
  it. Either ZK012 drops to warning, or the counter needs a bounded
  abbreviation guard. Raised at P-25.
- Rejected: treating continuation lines as prose (disagrees with every markdown
  renderer, and fails the spec's own examples); a flat exclusion list with no
  containment model (undefined behavior for a fence inside a list item, which is a
  shape this vault actively encourages); leaving bullets uncapped (the style law
  applies to them and nothing checked it).

## D-039 — 2026-08-18 — Error grade requires an exact predicate; skills amplify false positives
- Decision, four parts.
  (1) **Sentence boundary**: `.`, `!`, or `?` followed by whitespace or end of line,
  with a **bounded abbreviation guard** — `e.g.`, `i.e.`, `etc.`, `vs.`, `cf.`,
  `al.` are not boundaries. Six entries. It is data, so D-035's rule governs: it
  grows only from **observed** miscounts in the real vault, never speculatively.
  The counter is deliberately crude — it detects multi-sentence *runs*, not English.
  (2) **ZK012 demoted to warning.**
  (3) **Severity law, at full generality: error grade requires an exact predicate.
  Approximate detectors cap at warning.** An error asserts a fact about the file;
  a detector that admits it approximates cannot assert one. Sweep the existing
  table for other violations at audit close — ZK023's count-phrase regex is the
  known suspect.
  (4) `[skill]` **SKILL.md drafting rule: skills act on errors, mention warnings.**
- New hazard class named: **skill-amplified false positives.** A human seeing a
  spurious warning shrugs and moves on. A skill instructed to resolve complaints
  *obeys* — it rewrites correct prose to satisfy a miscount, and the vault degrades
  in the exact direction the rule was meant to prevent. Tolerance for approximate
  checks is a property of the *consumer*, and an LLM consumer has none. Every
  approximate detector must therefore be paired with an instruction not to act on
  it automatically.
- Confirmed in source, not hypothetical: problem.md line 173 specifies
  `Run zk_lint.py --fix on everything written; fix any residual complaints.`
  **"Any" is unscoped and includes warnings.** That line is superseded by part (4)
  of this decision; `zk-log`'s SKILL.md must scope it to errors, with warnings
  surfaced to the user rather than acted on.
- Rejected: relying on the guard alone with ZK012 left at error (a bounded list
  cannot cover every abbreviation, and one miss produces a hard failure on correct
  prose); demoting ZK012 without the guard (leaves a counter that is wrong more
  often than it needs to be); a general abbreviation detector or NLP tokenizer
  (semantic judgment re-entering lint, and a runtime dependency against CLAUDE.md).

## D-040 — 2026-08-18 — Superseding a behavior requires amending the text that specifies it
- Decision: when a decision entry supersedes behavior that is specified in prose
  somewhere else in the repo, **that prose is amended in the same change**. A
  supersession recorded only in `decisions.md` is not sufficient when the original
  text still reads as a live instruction. Applied immediately: problem.md line 173
  amended from `fix any residual complaints` to `fix residual **errors**; warnings
  are reported, not acted on (per D-039)`.
- The seam, named: `decisions.md` is append-only and authoritative, but it is not
  the only thing anyone reads. problem.md is the spec, and a spec that still
  instructs the unsafe thing is an **instruction trap** — a future session
  implementing `/zk:log` from problem.md would build exactly the behavior D-039
  banned, and would be right to, because that is what the spec said. The decision
  log records *why*; the spec records *what to build*. Only one of them gets
  implemented from.
- Distinction from the append-only rule: `decisions.md` and `enhancements.md` are
  append-only and are amended only by markers (D-002, D-023). Every other document —
  problem.md, architecture.md, SPEC.md, CLAUDE.md — is **living text** and is
  corrected in place. Append-only is a property of the *log*, not of the repo.
- Rejected: leaving problem.md superseded-but-unamended (the trap above);
  amendment-section-only notes at the bottom of problem.md (the reader of line 173
  never reaches them — the correction must be where the instruction is).

## D-041 — 2026-08-18 — Heading levels: `##`/`###` only, both bans error grade
- Decision: vault notes use `##` and `###`. **H1 banned** (ZK037, error) and
  **`####` or deeper banned** (ZK038, error). Both are error grade legitimately
  under D-039's law — heading level is a character count at line start, an exact
  predicate with no approximation.
- Two distinct failure classes, hence two codes. **H1 → structural redundancy**: a
  title inside the file duplicates the filename, which is already the note's
  identity. This is D-037's asymmetry from the other side — the summary-vs-filename
  check survived because slug-vs-prose is mechanical, and heading *level* is more
  mechanical still. Co-tenancy why: Obsidian treats the filename as the document
  title, so an H1 renders as a peer of the `##` sections and breaks outline view
  for the tool sharing this vault. **`####`+ → taxonomy growth**: four levels of
  nesting means the note has grown an internal hierarchy, which in a machine-first
  vault signals it should be two notes.
- `###` **permitted.** The schema locks section *vocabulary* (D-011's charter
  sections, §7.2's log sections), not section *interiors*. Restricting interiors
  requires observed abuse — the accretion ladder this review has applied to every
  list and guard (D-035, D-039): rules grow from what the vault actually does,
  never from what it might do. The renderer handles folding, and the depth cap
  already contains the sprawl worry that would motivate the restriction.
- **Scope convention, ratified as standing:** SPEC.md binds **vault notes** unless
  a rule is explicitly marked otherwise. Repo document style is CLAUDE.md's
  jurisdiction. The two overlap in exactly one place, deliberately: CLAUDE.md's
  directive-style rule is dual-scoped by its own text — *"in vault notes and in
  repo docs alike"* — but only the vault half is lint-enforced, since `zk_lint.py`
  runs on the vault. Repo docs keep the norm without the check.
- Housekeeping this closes: SPEC's heading sentence read as a universal style rule
  while every document in the repo, SPEC included, opens with an H1. Scoped now.
- Rejected: banning `###` (no observed abuse, and the depth cap already bounds the
  concern); warning grade for either ban (the predicate is exact, so D-039's law
  permits error and nothing argues for less); allowing H1 in `topics/` where
  headings are free-form (the filename-redundancy and Obsidian-outline reasons
  apply to every type equally).

## D-042 — 2026-08-18 — Rules declare their layer; fence opacity exempts one of them
- Decision: delete SPEC §6's *"code block contents are exempt from every style
  rule."* Its intent moves into the why-line of D-038's fence-opacity rule, which
  is where the behavior actually comes from. In its place, ratify the **layer
  taxonomy** — every lint rule declares which layer it binds, at the moment it is
  written:
  **file** — bytes and paths: encoding, BOM, newlines, filename shape, path length.
  **frontmatter** — the parsed YAML mapping: required fields, enums, summary rules.
  **structure** — the parsed markdown body: headings, paragraphs, list items,
  section vocabulary.
  A rule may declare more than one — ZK027–ZK030 compare frontmatter against file
  path by design.
- **Fence opacity exempts the structure layer by construction**, and only that
  layer. Contents of a fence never become headings, paragraphs, or list items, so
  no structure rule can reach them without a separate exemption. File-layer checks
  are unaffected and must stay unaffected: a note containing a fence still has an
  encoding, a path length, and possibly a BOM.
- Why the sentence had to go rather than be narrowed: it was **redundant where it
  was true** — opacity already makes structural exemption unstatable, and D-036
  bans rules that cannot fire — and **false where it was not**, since "every style
  rule" would exempt a fenced file from file-layer checks that must reach it. It
  was the only false claim in SPEC.md. A sentence that is simultaneously dead and
  wrong cannot be repaired by adjustment.
- Consequence: the layer declaration is the second thing a new rule must state,
  after D-033's failure class. Between them, a rule that cannot name its failure
  class or its layer is not ready to be written.
- Rejected: narrowing the sentence to enumerate exempted rules (a list that must be
  maintained in parallel with the rule table — D-030's duplicate-home defect);
  keeping it as intent (D-036); making file-layer checks skip fenced content (they
  bind bytes, and bytes inside a fence are still bytes in the file).

## D-043 — 2026-08-18 — Validate the wikilink form we write; severity capped by remediation
- Decision: ZK039, **warning**, layer `structure`, failure class **reference rot**.
  Only the simple `[[name]]` form is validated. Alias `[[name|text]]`, heading
  `[[name#section]]`, and block `[[name^id]]` forms are ignored — accretion trigger
  if abuse is observed. **Resolution is exact slug match** against `topics/` slugs
  and project slugs, nothing else: no log filenames, no shortest-unique-path, no
  alias table. Fences are opaque per D-042's layer taxonomy, so a `[[name]]` inside
  a code block is not a link.
- **Write-side mirror of D-029**, and the pairing is the point. D-029 tolerates
  unknown frontmatter keys because *co-tenant tools* write them. Here the simple
  form is what **our** tools write, so we validate it; the alias/heading/block
  forms are Obsidian's dialect, written by the human half of the co-tenancy, and
  we tolerate them. The rule is: validate what we emit, tolerate what they emit.
- **Severity capped by remediation, not by predicate.** The predicate is exact once
  resolution is defined, so D-039's law would permit error grade. It stays a
  warning because **every remediation is a content decision** — write the missing
  topic, fix the link, or delete it — and the one an automated fix-pass would
  naturally take, creating a stub note, is banned outright by D-021. A check whose
  only mechanical remedy is prohibited must not be error grade, because D-039's
  consumer chain means a skill would act on it. This extends D-039: severity is
  bounded by the *exactness of the predicate* **and** by the *legitimacy of the
  available remediation*, whichever is lower.
- Why it earns its place at all: a dangling link is the **only detector for
  promised-but-absent notes**. D-021 bans stubs, so a topic that was meant to exist
  and does not leaves no trace anywhere in the vault — no empty file, no index
  line, no error. The link that points at it is the single surviving evidence that
  it was ever intended.
- Rejected: silence (the drafted rule — discards the only signal for an otherwise
  invisible failure class); full Obsidian link resolution (alias tables, shortest
  unique path, heading and block anchors — large parser for a decorative feature);
  error grade (the remediation cap above); resolving against log filenames (logs
  are dated and immutable; nothing should link to one by name).

## D-044 — 2026-08-18 — Log sections split into three checks; `--fix` restructuring boundary
- Decision: SPEC §7.2's single bundled rule becomes three, one per failure class.
  All layer `structure`.
  **ZK009 — unknown section name, error.** Closed vocabulary, exact match. Adopted
  on D-011's asymmetry: that decision made the *project* equivalent a warning
  because `project.md` is hand-edited, and logs are skill-written, so the argument
  does not carry over. `## Gotcha` beside `## Gotchas` is the failure.
  **ZK040 — sections out of order, warning.** Failure class reframed as **emitter
  conformance**. The order `Done → Decisions → Gotchas → Next` is `zk-log`'s
  drafting contract and belongs in its SKILL.md. A reader is unharmed — parsing is
  by name, never positional — and the primary violator will be the skill itself, so
  the *note* must not be blocked for the *tool's* drift. Warning, and the fix is
  upstream.
  **ZK041 — duplicate section name, error.** Gap the drafted rule missed entirely.
  This is the one malformation that genuinely breaks name-based parsing: with two
  `## Gotchas`, "the Gotchas section" stops being a well-defined thing. Remediation
  is a human merge; `--fix` never touches it, and the skill surfaces it rather than
  silently concatenating, because ordering and context between the two blocks is a
  content decision.
- **`--fix` restructuring boundary, named and precedent-setting:** `--fix` is
  mechanical-only, and **mechanical means provably meaning-preserving.** Reordering
  log sections fails that proof — cross-section references (`## Next` saying "the
  above", `## Gotchas` referring to a decision by position) are meaning-bearing and
  invisible to a block mover. Recorded as the **first rejected restructuring
  candidate**; successors cite this test rather than relitigating it.
- Rejected: keeping order at error grade (a preference wearing an error's grade —
  nothing parses positionally, so there is no failure, only inconsistency);
  `--fix` reordering (the boundary above); leaving unknown sections unchecked
  (D-011's reasoning applies with more force here, not less).

## D-045 — 2026-08-18 — Restatement duplicates, citation indexes; Decisions bullets cite
- Decision: the two-place structure is ratified — a decision appears as a pointer
  in the session log and as the durable `D-NNN` entry in `decisions.md`. The
  distinction that makes this compatible with D-030: **restatement duplicates,
  citation indexes.** A second copy of a rule is a second source of truth that can
  drift; a citation is a pointer into the one home, and pointers are what D-030
  explicitly permits. The two files answer different questions — the log answers
  *what happened this session*, `decisions.md` answers *what is true about this
  project* — and a session where a decision was made is incomplete without it.
- Check: **ZK042, warning, layer `structure`, failure class record displacement** —
  every bullet under a log's `## Decisions` carries a `D-NNN` reference. The
  displacement failure is real and silent: a full decision written into the log and
  never promoted is still indexed, so nothing is lost, but it is found as *session
  history* rather than as *a standing decision*, and D-002's supersession machinery
  cannot reach it because it has no ID.
- **Second emitter-conformance rule** (after D-044's ZK040). `[skill]` `zk-log`'s
  SKILL.md contract sequences the `decisions.md` append **before** log finalization,
  so the `D-NNN` exists by the time the log's pointer is written. That sequencing
  turns the obvious false positive — "the decision was not written yet" — into a
  true positive: it is a skill sequencing bug, and the check should catch it.
- Warning grade on both counts: D-044's emitter logic (the violator is our own
  tooling, so fix the skill rather than block the note) and D-043's remediation
  clause (promotion is a content act — deciding what is durable is exactly the
  judgment `/zk:log` exists to make, and no mechanical pass can perform it).
- Placement per P-18/D-030: the durable-record rule's normative home is §7.4; §7.2
  carries a visible pointer to it.
- Rejected: a length proxy for "pointer vs record" (prose judgment in mechanical
  clothing — the fourth explicit instance, after D-033, D-037, and D-039);
  error grade (both caps apply); no check at all (leaves the one failure class here
  entirely undetected); recording decisions only in the log (loses `D-NNN`,
  supersession, and the every-recall read of `decisions.md`).

## D-046 — 2026-08-18 — Immutability binds testimony, not representation
- Decision: log immutability is ratified, with its **object named**. It binds
  **testimony** — the asserted content, what the session claimed was true — and not
  **representation** — encoding, tag casing, whitespace, frontmatter key order.
  `--fix` on an old log is therefore legal **by construction**: D-044 already
  defines mechanical as provably meaning-preserving, and an operation that
  preserves meaning cannot alter testimony. No exception is needed; the two rules
  were never actually in conflict once the object was named.
- New clause: **mechanical fixes do not touch `updated`.** The field is the
  tamper detector for testimony (D-026), and repairing representation is not
  tampering — so ZK020 now fires only on real violations rather than on the
  vault's own maintenance. Resolves a live contradiction: ZK016's `--fix` sets a
  missing `updated` to today, which on a log would immediately trip ZK020's
  later-than-filename warning. Corrected: ZK016 fills a **missing** `updated` with
  today for `project` and `topic`, and with the **filename date** for logs, per
  D-026's equality requirement. No other mechanical fix modifies the field.
- Filename typos: **no exception.** `2026-08-14-save-sytem.md` stays misspelled.
  The filename is identity (D-025, D-027), renaming is a file move (D-024), and
  identity is not reissued. The remedy is detection, not repair — ZK043 warns when
  a log's topic slug near-misses another log's topic slug in the same project.
  Honest limit recorded: it cannot fire on the first log about a subject, since
  there is nothing to near-miss against. **The harshness is accepted**, not
  mitigated: a misspelled slug costs a near-miss warning and nothing else, because
  retrieval resolves by frontmatter and index line, never by filename spelling.
- **Mutation policy gets its own SPEC section** (§7.0), one row per note type, with
  the testimony/representation distinction as its governing header. The vault has
  four different mutation policies — read-modify-write, immutable, append-only,
  generated — and they were stated in four places with no way to see them together.
  Existing rules become pointers into it per D-030.
- Rejected: a rename exception for typos (identity is not reissued, and "small
  enough to be safe" has no definition that survives contact); suspending `--fix`
  on logs (would leave old logs permanently unrepairable as the schema evolves —
  a BOM or a tag-casing drift would be frozen in); treating `updated` as
  representation (it is the detector; exempting it from the distinction is what
  makes the distinction work).

## D-047 — 2026-08-18 — Sequential means contiguous; the gap is the tamper detector
- Decision, three parts.
  (1) **Zero-padding at 3 digits**, with the ceiling reasoned rather than
  engineered around: `D-999` exceeds the design life of a single decisions file
  under D-002's one-read premise, and D-001's context trigger fires long before
  then — a file with a thousand decisions has already forced E-008 or E-004.
  Overflow is another rule's problem. Recorded so a successor knows it was seen
  and deliberately not solved.
  (2) **Newest appended at the bottom.** Keeps the write path a pure file append,
  which keeps content restructuring out of it entirely — the class D-044 drew a
  boundary around. Chronological one-read order is D-002's own stated reason for
  choosing a single file over MADR. Position costs nothing to a whole-read
  consumer (D-001), so the "newest is last" objection is a human concern in a
  machine-first vault.
  (3) **Sequential means contiguous, and ZK013 errors on gaps.** A missing `D-003`
  between `D-002` and `D-004` is an error, not merely a style deviation.
- Why contiguity: it is **the decisions file's tamper detector**. The file is
  append-only, so a hand-deletion leaves no other trace anywhere — no marker, no
  timestamp change, no index line, nothing. The gap in the sequence is the only
  surviving evidence that an entry existed. Exact predicate, so error grade is
  legitimate under D-039; no mechanical remediation exists **or is wanted**, since
  the correct response is a human accounting for what was removed and why.
- Third instance of a pattern, now named: **every immutability or no-stub rule
  needs a paired detector.** D-026 gave log immutability its detector (`updated`
  equality). D-043 gave D-021's no-stub rule its detector (the dangling link, the
  only trace a promised-but-absent note leaves). This gives append-only its
  detector (the ID gap). The shape recurs because each of those rules *permits a
  failure that leaves no trace* — that is precisely what makes them cheap, and
  precisely why they cannot stand alone.
- Rejected: unpadded IDs (string and numeric order disagree, so a lint check
  reading file order cannot distinguish sequence from noise without converting);
  4-digit padding (solves a problem that arrives after the file has already failed
  for a different reason); newest-at-top (every append rewrites the file, dragging
  restructuring into the write path); "sequential" meaning only never-reused
  (leaves deletion undetectable, which is the entire failure this closes).

## D-048 — 2026-08-18 — Drop ZK023; guards may be upstream obligations, not only detectors
- Decision: **ZK023 is deleted**, regex and all. The intent routes to `zk-log`'s
  SKILL.md drafting rules with E-001 as backstop — the **second full instance** of
  D-037's delete-and-route disposal, which is now the standing pattern for a
  mechanical check that turns out to be semantic.
- Why the "it catches the most common form" defence fails: **the emitter is a skill
  explicitly instructed against count phrasing** (D-009). The population the check
  would police is near-empty by construction, so "most common form of the failure"
  is a ratio over almost nothing. A check earns its place against the failures that
  actually occur, not against the ones a hypothetical unguided author would write.
- It failed three tests at once. D-039: error grade with an inexact predicate —
  `Decisions on 3 subsystems` is a false positive, `Decisions numbering eight` a
  false negative. D-043: the only remediation is rewriting the summary, a content
  act `--fix` may not perform, so the consumer cap applies. D-037: partial coverage
  claiming coverage — the real class is **accrual staleness**, and
  `Decisions from the early architecture phase` is equally stale-prone and equally
  invisible to the regex.
- The real class was already guarded, upstream: D-009's **refresh-on-append**
  clause, which requires `/zk:log` to rewrite the summary in the same step it
  appends an entry. The regex was redundant exactly where it mattered and wrong
  everywhere else.
- **Traceless-failure principle, formally ratified.** Every rule that permits a
  failure leaving no trace must be paired with a guard. Exposure citation: D-021
  created the no-stub exposure, and it stood unguarded until D-043 supplied a
  detector twenty-two decisions later — discovered by accident, while reviewing
  wikilinks. The principle exists so the next such rule does not ship bare.
- **A guard may be a lint detector or an upstream obligation.** §0's table admits
  both: ZK020, ZK039, and ZK013 detect after the fact; D-009's refresh-on-append
  prevents before it. Preventing at the emitter is the stronger form where the
  emitter is ours — which is the same reasoning as D-044's emitter conformance and
  D-045's sequencing contract.
- Rejected: demoting ZK023 to warning (a warning that is wrong in both directions
  still costs a code path, a test, and reader attention); keeping it for
  hand-written summaries (the vault's decision files are skill-written by design,
  and D-036 bans rules that cannot fire against the real population).

## D-049 — 2026-08-18 — Conventional choices are labelled; the index declares its own gaps
- Decision, four parts.
  (1) **Group order is arbitrary-but-fixed**, and SPEC says so in those words. Only
  *fixedness* is normative — it belongs to D-012's determinism family, because
  iteration-order emission would produce phantom diffs with no content change. The
  particular order Projects → Decisions → Logs → Topics has no failure class behind
  it and must not be presented as though it does.
  (2) **New category: conventional vs. reasoned choices.** A reasoned choice has a
  named failure class (D-033). A conventional choice has none — any consistent
  answer works and consistency is the whole point — and it MUST be labelled
  conventional, so no successor reverse-engineers a rationale that was never there
  and then "improves" the order to serve it. Apply retroactively at audit close to
  D-044's log section order, which is the same kind of choice.
  (3) **The orphan asymmetry is intended**, stated in §8 and cited to D-020: an
  UNCHARTED project's logs are indexed, so `index.md` can carry Logs entries for a
  project with no Projects line. Its mirror from D-021 — a charter-only project
  that appears in Projects and nowhere else — is stated alongside it, so neither
  reads as a bug to someone encountering one first.
  (4) **The index declares its own gaps.** The header gains `skipped: N`, emitted
  only when nonzero. `notes:` and `skipped:` are both content-derived and therefore
  deterministic, so `--check` compares them like any other content.
- Why (4) closes a traceless failure: §8 skips unparseable notes and reports them to
  stderr. Stderr is transient — a vault whose entire `topics/` directory fails to
  parse produces an index with **no Topics group at all**, which reads as "this
  vault has no topics." The absence is indistinguishable from a fact. Writing the
  count into the header makes the artifact **declare its own incompleteness at the
  point of consumption**: the surface that is distorted is the surface that says so.
- No new lint code. The header field **is** the detector — a guard need not be a ZK
  code, as D-048 already established for upstream obligations. Stderr remains
  transient diagnosis, lint remains the per-note detail, and no empty group is ever
  emitted to imply a gap.
- Rejected: emitting an empty group to signal skipped notes (a group header with no
  entries is a stub — D-021); a lint code for "notes were skipped" (lint already
  reports each unparseable note individually; a second aggregate check is
  duplicate coverage); leaving the skip count on stderr only (the failure and the
  distorted surface would live in different places, and only one of them persists).

## D-050 — 2026-08-18 — Index lines are a rendering, not a serialization
- Decision, labelled per D-049.
  **Conventional:** the comma-space join inside the tag brackets, and the bracket
  characters themselves. Any consistent choice works.
  **Reasoned:** the em dash separator. Failure class is **generation-side separator
  distinctness** — index lines are slug-dense, and paths, dates, and kebab-case tags
  are all hyphen-rich, so a plain hyphen separator would be visually
  indistinguishable from a dozen others on the same line. The em dash appears
  nowhere else in a generated line. This is about the line being *legible as
  emitted*, explicitly **not** about it being parseable.
  **Empty tag lists are omitted entirely** — an empty `[]` is a stub, D-021's
  family, and it costs density on the one surface D-001 requires to be dense.
- **Normative non-goal, ratified: `index.md` lines are a rendering, not a
  serialization.** Nothing parses them back. Any consumer needing structure goes
  through `zk_read.py`, which reads frontmatter from the source notes — the same
  chokepoint that enforces exclusion. The index is a catalog for a reader, and its
  reader is a language model.
- Therefore **no constraints are placed on summary characters.** A summary may
  contain em dashes, square brackets, or anything else. Constraining prose to
  protect a parser that does not exist and is not wanted would be policing the
  content to serve a hypothetical consumer — and the summary is the retrieval
  surface (D-003), so any constraint on it costs real retrieval quality against an
  imaginary benefit.
- **First latency defused pre-activation.** D-040's lesson came from a trap that was
  already live: problem.md:173 instructed unsafe behavior and would have been
  implemented. This one is the opposite timing — an under-specified format that
  *invites* a future parser, disarmed by declaring the non-goal before anyone
  builds one. The general move: when a format could invite a use it does not
  support, state the non-goal normatively rather than constraining the data to
  support the hypothetical use.
- Rejected: forbidding em dashes or trailing brackets in summaries (policing prose
  for a non-existent parser); a machine-readable index sidecar (a second source of
  truth derived from the same frontmatter `zk_read.py` already exposes); leaving
  the parseability question open (an open question about a format is an invitation,
  and the next person to need structure would have written a fragile splitter
  rather than calling `zk_read.py`).

## D-051 — 2026-08-18 — `notes:` is diagnostic; header fields describe this file
- Decision: `notes:` stays, labelled **diagnostic**. Its job is context for D-034's
  index-size warnings — 2,000 small notes and 200 bloated summaries produce the same
  character count and need different remedies, and the note count is what separates
  them. It is **bound by nothing**: no threshold, no check, no exit code. D-001's
  "measure, don't count" rejects note count as a *threshold*, not as *context
  alongside* one.
- **Third D-049 label ratified: `diagnostic`.** Alongside *reasoned* (has a named
  failure class) and *conventional* (any consistent answer works), a diagnostic
  element exists to be **read by a human or a model and acted on by neither**. The
  label matters for a specific reason: D-036 removes rules that cannot fire, and a
  diagnostic field fires nothing by design. Without the label the inert-rule sweep
  would delete it as dead. **Designed-unread-by-machines is distinct from dead**,
  and only the label carries that distinction.
- Ambiguity settled by D-050's rendering principle: **header fields describe the
  contents of this file.** `notes:` counts what is **indexed**; `skipped:` is the
  **sole** reference to anything absent; totals are derivable and never stated. The
  index renders itself, not the vault — the same reason it is not a serialization.
- Rejected: dropping `notes:` (loses the only signal separating many-small from
  few-bloated when D-034 fires); making `notes:` count indexed plus skipped (states
  a fact about the vault in a file that describes itself, and makes both fields
  ambiguous — the exact defect this closes); emitting a `total:` field (derivable,
  and a third field to keep consistent); binding a threshold to `notes:` (D-001
  forecloses it, and D-034 already measures the thing that actually constrains).

## D-052 — 2026-08-18 — Fail-soft on unparseable notes; overloaded codes disambiguate in the message
- Decision, four parts.
  (1) **Fail-soft ratified**, with D-049 recorded as a **load-bearing dependency**:
  skipping is only acceptable because `skipped: N` declares the omission on the
  artifact. Rule and detector are mutually referential and **removable only
  together** — deleting the header field would silently restore a
  content-discarding rule. Before D-049 this rule was genuinely wrong; after it,
  right.
  (2) **`--check`'s overloaded exit code is resolved by message, not by code.**
  D-019's buckets are unchanged — "index is stale" and "vault has broken notes" are
  both *did its job, answer negative*, so both are exit 1. The diff report names
  **which header fields moved and why**. **Standing pattern for exit-code
  overload:** disambiguate in the message; never multiply codes to encode
  conditions, because the code is the caller's control flow and the message is the
  human's diagnosis, and conflating them degrades both.
  (3) **Jurisdiction split on parse failure.** The index's question is **binary —
  renderable or not**; it does not grade. `zk_lint.py` owns severity
  discrimination across the three cases (no frontmatter, malformed YAML, valid YAML
  of the wrong shape). No-frontmatter strays are counted and skipped like any other
  unrenderable file — **no exempt category**, consistent with D-022's posture that
  unrecognized things are surfaced rather than quietly excused.
  (4) **`zk_recall.py` is fail-soft too, with the strongest guard form.** D-021's
  inventory comment becomes **mandatory on any skip**, naming the skipped file and
  the lint remedy. A bundle silently missing a note from the project under
  discussion is the highest-stakes omission in the system, so it is declared on the
  surface the model actually reads.
- **Reconciliation with D-024, stated because it reads as a conflict.** D-024 bans
  diagnostics from the bundle "in any form — not as comments." That ban is about
  **vault diagnostics** — complaints concerning other notes, which a model would
  consume as facts about the domain. A skip notice is **bundle self-description**:
  it reports the completeness of the thing being handed over, exactly as D-021's
  inventory comment already does and as D-049's `skipped:` field does for the index.
  D-051's field-scope rule is the same principle — an artifact may describe itself.
  This refines D-024's category rather than superseding it: vault diagnostics stay
  out; bundle self-description was never what D-024 was aimed at.
- Rejected: aborting the rebuild (one malformed note freezes `index.md`, and a
  stale index is worse than an incomplete one because everything downstream reads
  it); separate exit codes for stale-vs-broken (see the standing pattern above);
  grading parse failures inside `zk_index.py` (duplicates lint's jurisdiction, and
  the index has no use for the distinction); silent skipping in recall (the
  omission the user is least able to detect and most likely to be harmed by).

## D-053 — 2026-08-18 — Exclusion errs toward excluding; enforced structurally
- **Governing asymmetry, ratified first because it decides every sub-question:
  exclusion errs toward excluding. An ambiguous path is private.** Every other rule
  in this spec trades retrieval quality; this one trades privacy. Over-excluding
  costs a note the user must move. Under-excluding puts private content into a
  context window and, per CLAUDE.md non-negotiable 5, sends it to Anthropic. The
  costs are not comparable, so ties do not get split.
- Mechanism, upgraded from the drafted first-component test:
  **any-component matching**, **casefolded**, tested **after vault-relativization**.
  Catches nested `projects/game-x/private/`, cased `Private/`, and any depth.
  Casefolding is required because the check cannot depend on D-025's lint rule
  having passed — `zk_read.py` decides what to read before lint ever runs.
- **Symlinks: exclude on either the walked path or its resolved target.** Testing
  only the walked path misses a link into `private/`; testing only the resolved
  target misses a link *from* `private/` outward. Either match excludes.
- Accepted cost: **slug shadowing.** A project or topic legitimately named
  `private` or `archive` is now invisible. It gets its own warning (ZK044) — and
  the warning **must be emitted by the chokepoint itself**, because nothing
  downstream can see an excluded path. This is the traceless-failure principle
  (D-047/D-048) applied to exclusion: the rule permits a project to vanish without
  a trace, so the guard has to live in the only component that knows it happened.
  `projects/private/` is distinguishable from `projects/game-x/private/` by
  position — one is a project slug, the other a subdirectory inside a project.
- **Enforcement is structural, at full strength** (D-028's class, strongest
  instance): a **behavioral fixture vault** built from this item's own adversarial
  table — every row, every flag, `--deep` included — asserting **zero excluded
  paths** appear in reads, in `index.md`, or in any bundle. Plus a **grep companion**
  enforcing the sole-walker chokepoint: no `os.walk`, `iterdir`, `glob`, `rglob`,
  `scandir`, or `listdir` anywhere in `scripts/` outside `zk_read.py`. One rule, one
  function, one fixture suite.
- Rejected: first-component matching (the drafted rule — indexes
  `projects/game-x/private/`, which is an unmistakable statement of intent);
  case-sensitive comparison (depends on a lint rule that runs too late);
  substring matching (`projects/private-api/` is not private, and over-exclusion
  has a floor too); a frontmatter flag (problem.md design decision 5 replaced
  `llm_safe` with location for exactly this reason — a flag can be forgotten, a
  directory cannot); testing only resolved paths (misses outward links); trusting
  review or convention for the sole-walker rule (D-028's finding: this class of
  bug is what discipline reliably misses).

## D-054 — 2026-08-18 — ZK codes are permanent identity; everything under them may change
- Decision: the `ZK###` scheme is adopted. **Flat numbering, ratified as
  conventional** per D-049 — only *stability* is normative. Layer is carried by
  D-042's declaration, not encoded in the number, so adjacency between codes is an
  **accident of when they were written** and carries no meaning. Stated explicitly
  so nobody reads ZK027–ZK030's contiguity as a reserved range or renumbers to
  create one.
- **Identity property, three clauses.**
  (1) A code is **permanent identity**. It names the rule, not the rule's current
  wording.
  (2) **Message, severity, and detection logic may all change under a stable code**,
  by decision entry. This is what lets the severity sweep demote a code without
  raising an identity question — ZK012 went error → warning under D-039 and remained
  ZK012, and every test asserting ZK012 stayed correct.
  (3) **Retirement is forever.** A deleted code's number is never reissued; gaps are
  history, not tamper evidence (contrast `D-NNN`, §7.4). ZK023 is retired.
- **Growth clause — a new code requires all four, by decision entry only:** a named
  failure class (D-033), a declared layer (D-042), a grade that passes D-039's
  severity law, and — if it guards a rule permitting traceless failure — a row in
  §0's guard table. A code that cannot supply all four is not ready to exist.
- **Opacity conceded and routed.** `ZK027` is not self-describing, and that is
  accepted rather than fixed: **messages self-describe** per D-016, the §10 table
  is the **sole** code→rule mapping, and no parallel slug-name scheme is introduced.
  A second naming system would be a second source of truth (D-030) that drifts the
  moment a rule is reworded.
- **Third instance of the control-flow/diagnosis split.** D-019 separated exit code
  from error message; D-052 resolved overloaded exit codes in the message rather
  than by adding codes; this separates a rule's stable identity from its mutable
  description. The recurring principle: **machine-facing identifiers are stable and
  opaque, human-facing text is descriptive and free to change**, and merging the
  two degrades both.
- Rejected: grouped numbering by layer (100s/200s/300s — duplicates D-042's explicit
  declaration, and renumbering would break every citation in decisions.md);
  self-describing slug codes (a second naming system to keep in sync); reusing
  retired numbers (a test or commit referencing an old code would silently resolve
  to a different rule — D-027's identity non-reissue).

## D-055 — 2026-08-18 — Severity is one bit: automation's licence to act
- Decision, with the closing clause first: **severity encodes exactly one bit —
  whether automation may act.** Error means act; warning means mention (D-039).
  That is the whole job, and it is why two tiers is the right number rather than an
  accident of drafting. Finer discrimination between warnings is **presentation** —
  lint output may sort and group by layer (D-042) and failure class (D-033), both
  already carried in the table — and is **never a third grade.** A third tier would
  need a third rule for what skills do with the middle, and D-039's clean
  act/mention split is exactly what makes it unambiguous to an LLM consumer.
- Accumulation gap closed by reusing D-034's pattern rather than inventing
  machinery: a **warning-count threshold**, failure class **reckoning-avoidance**,
  announced in `zk_lint.py`'s summary with the remedy split — `--fix` the
  mechanical ones, review the rest. Threshold ~20, and per D-033 the class is named
  while the **number is honestly a guess**; it should move once real vault data
  exists.
- **Exit status stays 0** at the threshold, per D-019: nothing failed, lint did its
  job and the answer was affirmative-with-notes. The threshold is **diagnosis, not
  control flow** — the **fourth instance** of that split, after D-019's exit
  codes, D-052's overload resolution, and D-054's code identity.
- `[skill]` The reckoning arrives through the skill: `/zk:log` surfaces the
  announcement conversationally on the **mention rung**. No new component, no new
  exit code, no new severity — the existing consumer chain carries it.
- Meta, recorded for the review log: this was the **first citation-survey item**.
  Its substance had already been ratified by earlier decisions — D-013 bound grades
  to the enforcement rungs, D-039 set the severity law, D-043 added the remediation
  cap, D-039 again fixed the skill consumption rule — so only the residue needed
  judging: tier count and the accumulation gap. Expect more of these as the review
  closes; the useful move is to state what is already settled and adjudicate only
  what is left.
- Rejected: a third tier (needs a third automation rule, and the discrimination it
  buys is available as presentation); nonzero exit on warnings (D-019's test says
  otherwise, and it would make every vault with a long paragraph "failing");
  leaving accumulation ungated (the same slow-drift failure D-034 closed for index
  size — warnings pile up, nothing forces a reckoning, and the pile is invisible
  because each individual warning was correctly ignored).

## D-056 — 2026-08-18 — ZK015 error grade; the remediation cap only binds where automation could act
- **Completing clause for D-043's severity cap**, ratified generally: the
  remediation cap applies where **automation could act wrongly**. Where **no
  remediation exists at all**, there is nothing for automation to do wrongly, and
  **exactness alone grades.** D-043 capped ZK039 because a mechanical fix existed
  and was prohibited (stub creation). ZK015 has no mechanical fix in any direction,
  so error grade stands — and error grade here means *stop and tell a human*, which
  is the correct automation behaviour, not a mis-remediation.
- ZK015: **error**, layer `structure`, failure class **dangling supersession**.
  A `superseded-by:` pointing at an ID absent from the file marks a decision dead
  with no successor. It is **tamper-adjacent** and strictly worse than a plain stale
  decision: the record discounts its own testimony in favour of nothing, and the
  marker suppresses scrutiny while the pointer goes nowhere. Under D-001 that entry
  still enters every recall bundle, now wearing a false resolution. Blocking the
  vault on it is correct.
- **Self-supersession folded in**: the target MUST differ from the carrying entry.
  Same code, same class — an entry superseding itself is a pointer to nothing by
  another route.
- **Scope: same-file stands, with the routing recorded.** `D-NNN` is unique per
  file (D-002), so a bare cross-file reference is ambiguous by construction.
  Cross-project supersession **composes** out of parts that already exist: record a
  local supersession in the affected project and cite a `topics/` note carrying the
  cross-project reasoning. No cross-file syntax, no new marker form, and **no
  E-entry** — the capability is already reachable, so parking it would imply a gap
  that does not exist.
- **Marker grammar stated once, in §7.4**, so the predicate has exact syntax to
  bind: `superseded-by: D-NNN (YYYY-MM-DD)` with an optional ` — <scope>` tail for
  **partial** supersession. The tail closes a gap this review hit three times —
  D-032 superseded only D-009's status clause, D-036 only D-035's anchor clause,
  and the format had no way to say so, forcing the scope into the superseding
  entry's prose where the reader of the *old* entry never sees it.
- Rejected: warning grade (no automation risk to cap, and the failure is
  tamper-adjacent); allowing cross-file targets (ambiguous IDs by D-002's own
  scoping); a separate code for self-supersession (same class, same remedy — D-054's
  growth clause would reject it for failing to name a distinct failure class);
  parking cross-project supersession as an enhancement (it composes today).

## D-057 — 2026-08-18 — Mutation taxonomy; grammar completion is the third amendment species
- Decision: the full mutation taxonomy for this repo, in one place. **Append-only is
  a property of the log, not the repo** (D-040) — `decisions.md` and
  `enhancements.md` are append-only; problem.md, architecture.md, SPEC.md, and
  CLAUDE.md are living text corrected in place.
- **Three amendment species are permitted on append-only files, and no others:**
  (1) **Supersession** (D-002) — `superseded-by: D-NNN (YYYY-MM-DD)[ — scope]`
  appended to a decision entry.
  (2) **Graduation** (D-023) — `graduated-by: D-NNN (YYYY-MM-DD)` appended to an
  enhancement entry whose work has been built.
  (3) **Grammar completion** — retrofitting an existing marker to a grammar
  ratified after it was written. **Licensed only when the information being added
  is already ratified elsewhere**, so the amendment records nothing new; it makes an
  existing record conform. It is **seamed** in D-040's sense: the grammar changed
  and the old text still reads as complete, which is the same instruction-trap shape
  as a superseded spec line.
- Applied immediately under (3): D-009's and D-035's markers gain their scope tails
  — `— status clause only` and `— complete-line anchors only`. Both scopes were
  already stated in D-032 and D-036 respectively; the completion moves that fact to
  where the reader of the *superseded* entry will actually encounter it, which is
  the entire point of D-056's tail.
- Boundary: grammar completion may **not** introduce a judgement. If the scope of a
  partial supersession were not already recorded in the superseding entry, deciding
  it now would be a new decision wearing an amendment's clothes, and it needs its
  own `D-NNN`.
- Rejected: leaving the bare markers (they conform to the old grammar and mislead
  under the new one — exactly D-040's seam); rewriting the marker lines wholesale
  (an amendment is an append, not an edit); a fourth species for corrections
  (a correction changes what the record says, which is what supersession is for).

## D-058 — 2026-08-18 — ZK017–ZK019 gate completion; files get near-miss, not an ignore list
- Decision: the three pre-growth-clause codes are retrofitted to D-054's gate.
  **ZK017** — layer `frontmatter`, class *multi-topic packing* (D-034).
  **ZK018** — layer `structure`, class *vocabulary drift*, the
  `## Tech Stack`-beside-`## Stack` failure D-011 exists to prevent.
  **ZK019** — layer `file`, class *unreachable content*: the file is real,
  valid-looking, and invisible to retrieval. ZK020 already passed the gate via
  D-026 and D-046.
- **ZK019 inherits D-022's near-miss detection** as ZK045 — the almost-right
  filename is precisely the case the ZK027–ZK030 coherence family **cannot see**,
  because that family keys on a declared `type`, and a file with no recognizable
  type or shape has nothing for it to compare.
- **ZK019 does not inherit the ignore list**, and the directory/file asymmetry is
  recorded with its **population reasoning**:
  **Directories persist.** `.obsidian/` is permanent, recreated by the co-tenant,
  and cannot be fixed — so its warning recurs forever and needs suppression, or the
  user learns to ignore all warnings (D-022's stated failure).
  **Stray files are transient.** Every one has a terminating remedy — fix it, type
  it, or move it to `private/` — so the warning ends when the file is dealt with.
  A file ignore list would be **config for an empty room**.
- Second reason, and the stronger one: a file-level ignore list reintroduces
  **config-driven invisibility**, which is the `llm_safe` pattern problem.md design
  decision 5 deliberately replaced with location. D-053 ratified location-only
  exclusion and errs toward excluding; a config key that makes specific files
  unmentionable is that principle's backdoor.
- Note on the citation: this was raised as "the D-023 backdoor." D-023 is the
  `graduated-by` marker and does not bear on this; the reasoning above assumes
  **D-053** was meant. Recorded rather than silently reinterpreted.
- Rejected: a file ignore list (both reasons above); folding near-miss into ZK019
  itself (D-022 set the precedent that plain and near-miss are distinct classes and
  therefore distinct codes, and D-054's growth clause requires exactly that test);
  leaving the three codes ungated (D-054's clause exists to stop precisely this
  kind of grandfathering).

## D-059 — 2026-08-18 — `--fix`'s body guarantee is testimony, not bytes
- Decision: `--fix` preserves **testimony** and may repair **representation**
  (D-046's distinction). The drafted "preserves body bytes outside the frontmatter
  block" is **rewritten, because two already-ratified operations falsify it** —
  `newline="\n"` normalization (D-018, D-028) and BOM stripping (ZK034) both change
  body bytes on conforming input. A guarantee contradicted by shipped behaviour is
  worse than none: it would be read as a contract, tested as one, and fail.
- **Block fencing clause**, closing the last unstated seam: fence **delimiters** are
  representation and `--fix` may normalize them; fence **contents** are testimony and
  are never touched. D-042 made fences opaque to *structure rules*; nothing had said
  whether `--fix` could touch the fence markers themselves.
- Frontmatter's representation contract stands unchanged per D-029 — semantic
  round-trip, key order canonical-then-original, unknown keys preserved by value.
  The body now speaks the same vocabulary, so `--fix` has one guarantee rather than
  two dialects of one.
- Added to the duplication sweep: **grep `byte` across SPEC.md.** D-012's
  generated-file determinism is the **only** legitimate byte-level claim in the
  document — `index.md` is machine-written and byte-comparable by design. Every
  claim about **user content** must speak testimony instead. Any other `byte`
  occurrence is either that determinism rule or a defect.
- Rejected: byte-preservation for the body (contradicted by two ratified
  operations); exempting logs from `--fix` to make byte-preservation true
  (D-046 already rejected this — it freezes old logs against schema evolution);
  leaving fence delimiters unstated (an unstated seam is what D-050 called a
  latency, and this one would activate the first time a fix pass met a `~~~` fence).

## D-060 — 2026-08-18 — The graph outranks its authors
- Decision: when a citation in a directive does not resolve against the decision
  record, **verify against the graph, substitute the citation the reasoning actually
  requires, and record the substitution in the entry** — rather than implementing
  the stated citation, silently reinterpreting it, or blocking on confirmation.
  Ratified as standing practice from its first use: D-058 was directed citing "the
  D-023 backdoor"; D-023 is the `graduated-by` marker and bears on nothing here, so
  the entry was written on D-053's location-only exclusion and problem.md design
  decision 5's `llm_safe` rejection, with the substitution stated in the entry.
- Why: the decision record is checkable and memory is not. Fifty-eight entries in,
  no participant reliably holds the whole graph — and the record exists precisely so
  none has to. Implementing a mis-citation propagates the error into a file that is
  append-only; silently reinterpreting hides a judgement call in a document whose
  value is that judgements are visible; blocking on every mis-citation would make
  the record's size a tax on using it.
- The recorded substitution is the load-bearing half. It makes the correction
  reviewable — the author sees what was assumed and can reverse it — which is what
  distinguishes this from an agent quietly deciding it knows better.
- Applies symmetrically: a citation *I* wrote that fails to resolve gets the same
  treatment, and the same visible note.
- Rejected: implementing the stated citation (writes a known-wrong lineage into an
  append-only file); silent reinterpretation (an invisible judgement); blocking
  every time (turns the graph's size into friction against consulting it).

## D-061 — 2026-08-18 — Scaffold writes territory only; vault init is explicit script work
- Decision: a fresh vault is `projects/`, `topics/`, and `index.md`. **Nothing
  else.** `private/` and `archive/` are **not** pre-created — they self-create on
  first use.
- **Territory/reserved asymmetry, recorded as reasoned.** `projects/` and `topics/`
  are *territory*: places content must have a home in, created because the schema
  routes writes there. `private/` and `archive/` are *reserved names*: a rule about
  what is excluded (D-053 matches any component, casefolded), and **a name rule
  needs no directory to exist.** Pre-creating one materializes a container for a
  purpose that may never arise — a **stub of a purpose**, D-021's failure in
  D-049's vocabulary. `archive/` is the sharper case: its documented purpose is
  holding a legacy vault, and a fresh vault has none. Git does not track empty
  directories either, so neither would survive a clone — the same argument D-021
  used against pre-creating `log/`.
- **Ownership ratified: vault init is explicit script work**, not a skill's and not
  a side effect. Per D-013's rungs it is zero-judgment and maximal-consequence,
  which is exactly the `[script]` rung's profile. It is **create-only**, **refuses a
  nonempty target**, and **prints the config next-step** on success. D-006's
  no-vault error names it, closing the loop from "no vault configured" to the
  command that makes one.
- **Named `zk_config.py --init`, not a sixth script.** D-007 fixes the v1 surface at
  five scripts plus two SKILL.md files, and CLAUDE.md already requires every script
  to be CLI-invocable — so `zk_config.py` being library-only was the anomaly, and
  giving it the CLI it was supposed to have costs nothing. Recorded because both
  forms were offered; a `zk_init.py` would have broken D-007's stated surface for
  no capability gain. architecture.md's script table gains the row.
- Confirmed clean: the empty-vault `index.md` is a header and zero groups, which is
  truthful self-description under D-051 (`notes: 0`). D-012's no-op behaviour **is**
  stated — render, compare ignoring `generated:`, write only on difference — so it
  is not invitation-shaped in D-050's sense.
- Rejected: pre-creating `private/` and `archive/` (stub of a purpose; also does not
  survive a clone); scaffolding on first write implicitly (D-006 forbids silent
  vault creation, and an implicit init is exactly the misroute it exists to stop);
  giving init to `zk-recall` (D-020 gives it *project* scaffolding, which is an
  interview — vault init has no judgement in it at all); a sixth script (D-007).

## D-062 — 2026-08-18 — `index.md` has one author; the ground state is the base fixture
- Decision, three parts.
  (1) **Message split** per D-052's pattern — one condition, two meanings, resolved
  in the message and never by a new exit code. An empty vault says what is actually
  true and points at the remedy, rather than trailing off after `Known projects:`
  and implying a lookup failed against a populated set:
  `zk: this vault has no projects yet. / Run /zk:recall <slug> to create the first
  one.` The zero-slug vault joins the **message-test fixtures** as a boundary
  population the template had never been run against.
  (2) **The determinism contradiction dissolves by ownership, not by a rule.**
  `zk_index.py`'s render path is the **sole author** of `index.md`; `--init` is a
  **caller**, not a second writer. Byte-identity between the file init writes and
  the file the next `zk_index.py` run renders then holds **by construction** —
  there is no second implementation to drift. This is D-030's one-normative-home
  principle applied at the code level, and the same dissolve-by-definition move as
  D-046: the conflict was an artifact of an unnamed relationship, and naming it
  removed the need to adjudicate.
  (3) **Ground state ratified**, serving double duty as `--init`'s test expectation
  and the **base fixture every other test vault extends**: territory present and
  empty (`projects/`, `topics/`), header-only `index.md` with `notes: 0` and no
  groups, and **no reserved-name directories** (D-061).
- Generalizable from the fixture point: **any message template that interpolates a
  collection needs an empty-collection fixture.** The zero case is where a template
  degrades into something ungrammatical or misleading, and it is exactly the case a
  developer writing the template never has in front of them.
- Rejected: a distinct exit code for the empty-vault case (D-052 — the code is the
  caller's control flow, the message is the human's diagnosis); letting `--init`
  write `index.md` itself (a second author for a file whose determinism is a
  ratified contract — the drift would surface as a phantom diff on the user's very
  first `zk_index.py` run); leaving the ground state implicit (it is the base every
  fixture extends, so an unstated version means each fixture invents its own).

## D-063 — 2026-08-18 — Examples are fixture-coupled renderings, not prose
- Decision: SPEC §13's examples become **lint-verified fixture files** — the D-062
  ground state plus deltas — **rendered into** the spec rather than typed into it.
  A **conformance test asserts them lint-clean forever**, which is the **resident
  detector** the staleness class requires: an example is instruction-shaped (D-040),
  so a stale one is an instruction trap living inside the document that bans
  instruction traps. This review found exactly that — the drafted log example
  carried `status: active`, which D-032 later made a ZK004 error, and nothing would
  have caught it.
- **Section licence**, stated in §13: examples are **non-normative renderings**,
  fixture-coupled, and **conflicts resolve toward the rules**. Annotations that
  describe the example itself are legal (D-051's self-description principle);
  comments that **explain a rule** are banned, because that is restatement and the
  rule has one normative home (D-030).
- Population, with the **criterion recorded rather than the census**: a shape earns
  a rendering when **multiple conventions interact** and their interaction is not
  derivable from any one rule. `decisions.md` is added — container frontmatter,
  contiguous zero-padded IDs, newest-at-bottom, the marker grammar, and a partial
  scope tail are five conventions meeting in one file. `project.md` is skipped:
  a closed section vocabulary is a **single-rule shape**, and single-rule shapes are
  their own example. The criterion outlives any list of which files to show.
- The log example's wrapped `## Gotchas` bullet is **kept deliberately and labelled**
  — it exercises D-038's CommonMark continuation rule and sits exactly at the
  two-sentence cap, so it is load-bearing test surface rather than incidental
  formatting.
- Rejected: hand-maintained examples (the defect this closes — six months of schema
  change with no detector); dropping examples entirely (they are the fastest way to
  convey an interacting shape, and the criterion above is exactly where prose is
  weakest); explanatory comments inside examples (D-030 restatement, and the copy
  drifts while looking authoritative).

## D-064 — 2026-08-18 — Fourth layer `content`; layer = the surface the predicate reads
- **Definitional rule, ratified: a rule's layer is the surface its predicate
  reads.** Not what it is about, not what it protects — what it reads. This is what
  makes assignment mechanical rather than a taste question, and it is why ZK011
  (a regex over a frontmatter value that happens to hold prose) is `frontmatter`
  while ZK012 (which reads the body) is not.
- **`content` ratified as a seamed refinement of D-042**, which named three layers
  and stopped. Defined as **reads body prose**. Members: ZK012 and ZK036, the two
  sentence-cap codes. They parse blocks to find the unit — that half is
  `structure` — and then read the text inside it, which D-042's taxonomy had no name
  for.
- Two properties, both born with the layer rather than added per rule.
  **Warning-capped by construction**: no `content` rule may be error grade, because
  a predicate that reads prose is approximate by nature. This makes D-039's severity
  law **structural** at the layer level instead of an argument repeated at each
  code.
  **Fence-opaque**: sentences inside a fenced block do not count, the same exemption
  D-042 gave `structure`.
- **Derivation rule, stated in §0 beside the layer table**, so assignment is a
  lookup: path-only → `file`; **declared-vs-path → `structure`**, per D-031's
  location-is-authoritative principle; field values → `frontmatter`; body prose →
  `content`.
- The declared-vs-path clause is a **principle, not family-scoped**. It was
  discovered on ZK027–ZK030 but it governs every check of that shape — ZK006
  (`project` vs. directory) and ZK020 (log `updated` vs. filename date) follow it
  too. Scoping it to the family it was found in would have made two identically
  shaped checks land in different layers for no reason.
- **ZK001 is a dual-layer code (`file` + `frontmatter`) and a capped singleton.** It
  is the only check that runs before frontmatter exists as a concept: locating `---`
  on line 1 is byte-level, parsing what follows is not. A dual assignment requires
  the **two-codes-rejected argument** — here, splitting would produce two codes for
  one defect, which D-054's growth clause rejects for failing to name two distinct
  failure classes. Duals are expected to remain unique; a second one is a signal
  that the taxonomy is wrong, not that duals are normal.
- Housekeeping: ZK015, ZK039, and ZK042 declared their layers in section body text
  rather than the table. All three move into the table — **one normative home**
  (D-030). The table is now the sole layer declaration for all 44 codes.
- Rejected: folding ZK012/ZK036 into `structure` (they read a different surface, and
  the layer's job is to say which surface); a per-rule warning cap for content codes
  (the cap is a property of reading prose, so it belongs to the layer); scoping the
  declared-vs-path rule to ZK027–ZK030 (arbitrary split across identical shapes);
  splitting ZK001 into two codes (one defect, one failure class).

## D-065 — 2026-08-18 — The three unclassed thresholds get their failure classes
- Decision: the D-033 sweep found three numbers with no named failure class. All
  three are now named, closing the last violations of D-033's own rule.
  **60-character slug cap (ZK032) — *path-budget contribution*.** A slug appears in
  every path containing it, so the cap is **derived** from ZK033's 240-character path
  warning: 60 is what keeps a four-level vault path inside it. **Coupling clause:
  revisit the two together if 240 moves.** A derived number that outlives its source
  is a number nobody can re-derive.
  **4-line decision entry body (ZK014) — *record bloat*.** An entry needing more than
  four lines is a document, and `decisions.md` is read whole on every recall (D-001),
  so entry length is charged to every future session rather than to its author.
  **2-sentence cap (ZK012, ZK036) — *narrative creep*.** D-038 reasoned from this and
  never wrote it into SPEC; the vault is machine-first and directive-style, and
  paragraphs are where explanation displaces fact.
- Why the coupling clause matters beyond this case: ZK032 is the first **derived**
  threshold in the spec. Without the clause, moving ZK033's 240 would leave 60
  looking independently chosen, and a successor would either preserve it for no
  reason or change it without knowing what it was protecting.
- Rejected: leaving any of the three unclassed (D-033 exists precisely because an
  unclassed number is wrong in a direction nobody notices); treating 60 as
  independently reasoned (it is arithmetic on 240, and saying so is what makes it
  checkable).

## D-066 — 2026-08-18 — The four unlabelled elements get their labels
- Decision: the D-049/D-051 sweep found four unlabelled elements. All four labelled.
  **Conventional** — fixedness-only, no rationale to serve: the log section order
  `Done → Decisions → Gotchas → Next` (D-044), and the frontmatter key order
  `type, project, tags, status, updated, summary` (D-029). Both are arbitrary; both
  must not move; neither has a failure class behind the particular arrangement.
  **Diagnostic** — read by a human or model, acted on by neither: `index.md`'s
  `generated:` timestamp, and `zk_recall.py`'s bundle inventory comment.
- The bundle inventory comment carries **both facts**, and the entry records both
  because either alone would mislead. It is **diagnostic by category** — nothing
  branches on it — **and load-bearing by obligation**, since D-052 makes it mandatory
  on any skip and it is the only surface declaring that a bundle is incomplete.
  It is therefore **exempt from unread-deletion on two independent grounds**: D-051's
  diagnostic label protects it from the inert-rule sweep, and D-052's mandatory skip
  declaration means removing it would silently restore a content-discarding rule.
  A future reader finding "nothing consumes this" must satisfy both objections, not
  one.
- Rejected: labelling the inventory comment diagnostic alone (true but incomplete —
  the category exempts it from a sweep while the obligation is what actually forbids
  removing it); leaving the two orders unlabelled (D-049's stated failure — a
  successor reverse-engineers a rationale and "improves" the order to serve it).

## D-067 — 2026-08-18 — `zk_read.py` gains a minimal CLI
- Decision: `zk_read.py` gets a CLI exposing **existing library functions only** —
  `zk_read.py <slug>` prints the paths and frontmatter of a project's notes,
  `zk_read.py --list` prints the known project slugs. Both to stdout. No new
  behaviour, no new file, **the five-script count is unmoved** (D-007).
- Why: CLAUDE.md requires that *"every script runs standalone from the CLI so a
  non-Claude agent can drive the vault with zero changes,"* while problem.md called
  `zk_read.py` a *"shared library, not user-facing."* The two have contradicted each
  other since before this review. The chokepoint is the one component that **must**
  be drivable without reimplementation — any agent that cannot call it is forced to
  walk the vault itself, which is exactly the exclusion bypass D-053's grep companion
  exists to prevent. A library-only chokepoint makes bypass the path of least
  resistance.
- D-061's own reasoning already committed us: it gave `zk_config.py` a CLI on the
  grounds that *"CLAUDE.md already requires every script to be CLI-invocable — so
  `zk_config.py` being library-only was the anomaly."* That argument indicts
  `zk_read.py` identically, and D-061 did not notice.
- **How the conflict surfaced, recorded because the mechanism is reusable:** it was
  caught by the architecture.md rewrite, where every claim had to trace to a
  citation. Rendering forces tracing, and tracing surfaces contradictions that
  reading does not. Neither document was wrong in isolation; the conflict only
  existed between them, and only became visible when one was rebuilt from the other.
- problem.md's "library, not user-facing" line gets a dated seam citing this entry,
  per D-040 — a superseded behaviour whose original text still reads as live is an
  instruction trap.
- Rejected: leaving the contradiction (an implementer follows whichever document
  they opened); resolving toward problem.md by exempting `zk_read.py` from CLAUDE.md's
  rule (the chokepoint is the worst possible exemption — see the bypass argument);
  a sixth script wrapping it (D-007's count, for no capability).

## D-068 — 2026-08-18 — The rendering contract; architecture.md declares its own currency
- **General contract, ratified.** A *rendering* is a document derived from ratified
  state. Three clauses:
  (1) **Derived** — every claim traces to a source; nothing originates in a
  rendering.
  (2) **Non-normative** — a conflict between a rendering and its source resolves
  **toward the source**, always.
  (3) **Self-declaring currency** — the artifact states how current it is, by the
  strongest means available to it.
- Four instances, previously solved one at a time and now recognized as one pattern:

  | Rendering | Source | Currency declared by |
  |---|---|---|
  | `architecture.md` | SPEC, decisions, problem.md | `rendered-against: D-NNN` header field |
  | SPEC §13 examples | fixture files | structural coupling — the example *is* the fixture (D-063) |
  | `index.md` | vault frontmatter | `generated:`, `notes:`, `skipped:` (D-049, D-051) |
  | recall bundle | vault notes | inventory comment + mandatory skip notice (D-021, D-052) |

- **architecture.md's guard: no frozen/live split.** One document, self-describing
  currency. The header carries `rendered-against: D-NNN`, labelled **diagnostic**
  (D-051) — read by a human, acted on by nothing.
- **Wrap discipline gains a clause** (CLAUDE.md): a decision touching rendered
  content **updates the rendering**; **every** decision bumps the field. The
  asymmetry is deliberate — bumping is free and unconditional, re-rendering is
  conditional on the decision actually changing what the rendering claims.
- **Staleness becomes self-declaring.** The gap between the header's `D-NNN` and the
  tail of `decisions.md` is a **visible bound on the drift** — not proof of
  staleness, but an upper limit on how much could have accumulated, readable on the
  artifact without consulting anything else. A rendering that cannot say how stale
  it might be is the traceless-failure shape §0 warns about; this converts it into a
  bounded, visible one.
- Mechanized comparison — a check asserting the header matches the ledger tail — is
  **deferred per the accretion ladder** until a slip is actually observed
  (enhancements.md E-017). The field is the guard; automation is what the field
  earns if discipline proves insufficient.
- Rejected: a frozen/live split (two documents, and the frozen one rots invisibly
  while looking authoritative — the exact failure D-040 named); no currency field
  (the drift bound is the whole guard, and without it architecture.md is the one
  artifact in the set relying purely on memory); mechanizing now (nothing has
  slipped yet, and D-035/D-039/D-041's ladder says restrictions grow from observed
  failure, never anticipated failure).
