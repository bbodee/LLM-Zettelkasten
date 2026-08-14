# enhancements.md — zk rebuild (repo-level parking lot)

Out-of-scope discoveries worth keeping. `trigger:` present = deferral (revisit
when the condition fires); absent = open enhancement. Fired triggers graduate
via a decisions.md entry or get consciously re-parked. Review at the 20-log
checkpoint alongside problem.md's own revisit clause.

## E-001 — Semantic lint pass (`zk_lint --semantic`)
- What: a contextual-quality linter that reads note bodies and judges whether
  summaries actually convey content (vs. mechanical checks in D-003). Candidate
  backend per user intent: locally run LLM, keeping the vault LLM-agnostic and
  private. Would require a dependency decision (breaks stdlib+pyyaml rule).
- Source: item 6 walkthrough; user's local-LLM request.

## E-002 — Promote read-before-write from instruction to hook
- What: PreToolUse hook blocking writes to existing vault notes unless read
  this session; needs read-state tracking.
- trigger: a clobbered topic/project note is observed in the wild (instruction
  rung demonstrably failed).
- Source: item 7 walkthrough; user's hook question.

## E-003 — Retrieval-eval at the checkpoint
- What: recall@k / MRR on natural-language questions against the vault, as the
  measurement replacing guessed token/count thresholds (per item 5 discussion:
  measure, don't count). Pattern from obsidian-second-brain's retrieval-eval.
- trigger: 20-log checkpoint.
- Source: research.md #1; items 1 and 5 walkthroughs.

## E-004 — Semantic search / embeddings
- What: vector or hybrid retrieval layer.
- trigger: index.md no longer fits comfortably in context (D-001's condition;
  ~2,000 notes is the proxy figure only). Cross-project discovery degrading is
  the expected first symptom — per-project index sections delay the ceiling for
  project recall but not for cross-cutting recall.
- Source: D-001; item 2 walkthrough (user's sub-index question).

## E-005 — Tiered context loading (L0–L3 style)
- What: graduated bundles — tiny always-loaded core, progressively deeper
  pulls. Architecture-compatible today: presets over existing zk_recall flags.
- trigger: bundle bloat observed — decisions/logs crowding out task-relevant
  content in real sessions (soft pressure, not context overflow; see item 5).
- Source: research.md #1/#3; item 8 walkthrough (replaces dropped draft D-005).

## E-006 — Generated "active decisions" header for vault decisions.md
- What: regenerate a current-decisions summary from superseded-by markers —
  generated like index.md, never hand-maintained.
- Source: item 2 walkthrough (user's sub-index-header idea; the marker is the
  primitive that makes this generatable).
