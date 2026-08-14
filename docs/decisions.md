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
