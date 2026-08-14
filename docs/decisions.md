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
