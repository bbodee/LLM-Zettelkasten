# enhancements.md — zk rebuild (repo-level parking lot)

Out-of-scope discoveries worth keeping. `trigger:` present = deferral (revisit
when the condition fires); absent = open enhancement. Fired triggers graduate
via a decisions.md entry or get consciously re-parked. Review at the 20-log
checkpoint alongside problem.md's own revisit clause.

Append-only. The one permitted amendment is appending
`graduated-by: D-NNN (YYYY-MM-DD)` to an entry whose work has been built (D-023).
No marker = still open; a re-parked entry stays unmarked.

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

## E-007 — Marketplace-style plugin packaging
- What: ship zk as an installable Claude Code plugin (manifest + marketplace
  listing) instead of the manual symlink/copy into `.claude/skills/` set by
  D-007.
- trigger: v1 working end to end (problem.md acceptance criteria 1–7 met).
- Source: CLAUDE.md open question 2; D-007.

## E-008 — Two-tier pointer index (concrete design for E-004's first half)
- What: root `index.md` becomes a table of contents — one line per project
  (reusing `project.md`'s summary, so no new hand-maintained string) plus the
  full topic list, each project line pointing at `projects/<slug>/index.md`
  rather than the bare directory. Each project gets a generated
  `projects/<slug>/index.md` with `## Charter`, `## Decisions`, `## Logs`,
  `## Related topics` (tag-matched). Root scales with project count, not note
  count, pushing D-001's context ceiling out by roughly an order of magnitude.
  Costs cross-project scanning: root shows no logs, so "have I hit this before?"
  means opening every project index. Mitigations if adopted: `topics/` is already
  the cross-project layer and stays listed in full at root; add a bounded
  `## Recent` group (last ~15 logs vault-wide, fixed size, generated).
  Implementation: `zk_index.py` writes N+1 files, `--check` verifies all.
  Matches research.md #4's pointer-index pattern (Claude Code's own memory).
- trigger: same as E-004 — flat `index.md` no longer fits comfortably in context.
  This is the cheaper first move at that trigger; embeddings stay the later one.
- Source: designed and reverted 2026-08-17 during SPEC.md review; rejected in
  D-010. Recorded so the design is not re-derived from scratch at the trigger.

## E-009 — `--vault` flag to complete the config cascade
- What: a per-invocation `--vault <path>` on every script, outranking `ZK_VAULT`
  and `zk.toml`. Completes the standard cascade — file for durable, env for
  session, flag for one command — and makes an env var left set in a shell
  profile harmless rather than silently shadowing.
- Why parked: new CLI surface no prior doc calls for, and D-014's stderr banner
  already converts the silent-shadow failure into a visible one, which was the
  actual problem. Also sits near problem.md's "multi-vault support" fence.
- Source: P-02 review 2026-08-17; named and deferred in D-014.

## E-010 — Worktree fallback: follow `gitdir:` before erroring
- What: when the D-015 fence is hit with no `zk.toml` found and `.git` is a file
  (git worktree or submodule), parse its `gitdir:` pointer, derive the main
  repository's working directory, and check there before raising D-006's error.
  Removes the "fresh worktree always errors" case for anyone relying on
  `zk.toml` without `ZK_VAULT`.
- Why parked: crosses from a filesystem check into parsing git's internal
  layout — the git integration D-015's fence deliberately is not. It also
  reaches outside the fence erected one decision earlier. The failure it
  prevents is already loud, already names both mechanisms, and is fixed by
  setting `ZK_VAULT`, which is inherited by child processes anyway.
- trigger: worktree-based agent runs become routine AND the `ZK_VAULT` step is
  repeatedly forgotten in practice.
- Source: P-03 review 2026-08-17; rejected in D-015.

## E-011 — Convert `zk.toml` to a `[zk]` table
- What: restructure `zk.toml` from D-017's single bare key to a `[zk]` table, so
  settings are namespaced and further additions are additive.
- trigger: a second setting is added to `zk.toml`. D-017 makes this mandatory
  rather than optional at that moment — a second bare key is not permitted.
- Source: P-04 review 2026-08-17; deferred in D-017.
- graduated-by: D-022 (2026-08-17)

## E-012 — Relative vault paths in `zk.toml`
- What: allow `vault = "../vault"`, resolved against the `zk.toml` file's own
  directory. Lets a vault travel with a cloned repo without editing config.
- Why parked: needs a specified and tested resolution base (file vs cwd), and
  D-014's banner would print a path the user must mentally resolve. v1 takes the
  barebones absolute form and enhances from there.
- trigger: a vault needs to travel with a clone — e.g. the demo vault shipping
  inside the repo (D-008's third deliverable).
- Source: P-04 review 2026-08-17; deferred in D-017.

## E-013 — Environment variable expansion inside the vault path
- What: allow `$HOME/vault` or `%USERPROFILE%/vault` as the `zk.toml` value or
  `ZK_VAULT` contents, expanded before normalization. Makes one config file
  portable across machines with different user names.
- Why parked: `expandvars()` leaves unknown variables as literal text, so a typo
  (`$HOEM/vault`) fails as "directory not found" instead of "unknown variable" —
  the undirected failure D-016 bans. Adopting it means writing explicit
  unknown-variable detection first, which is more than v1 needs when `~` already
  covers the common case.
- trigger: a single `zk.toml` needs to work across machines with differing home
  paths — e.g. the same repo cloned on Windows and POSIX.
- Source: P-05 review 2026-08-17; deferred in D-018.

## E-014 — Vault-level effort specs (a `problem.md` per project)
- What: extend the vault project schema with a spec document per project — the
  equivalent of this repo's `docs/problem.md`: problem statement, scope fence,
  acceptance criteria, out-of-scope list. Distinct from `project.md`, which is a
  charter (stack, conventions, current state) rather than a bounded effort spec.
  Would need its own `type`, frontmatter, section vocabulary, and a place in the
  recall bundle order.
- Why parked: v1's note types are fixed at project/topic/log/decision, and one
  doctrine-driven project does not establish the pattern. Adding a fifth type
  before the shape is known risks specifying the wrong thing.
- trigger: 2+ doctrine-driven projects are logging to the vault — enough to see
  what the shared spec structure actually is rather than generalizing from one.
- Source: P-08 review 2026-08-17.

## E-015 — `read` list in `zk.toml`: grant access to non-schema directories
- What: a second list alongside D-022's `ignore`, which *does* grant access —
  named directories outside the schema become readable by `zk_read.py` and enter
  the index and recall bundles. `ignore` silences; `read` admits.
- Open questions to settle before building: what `type` do notes in an admitted
  directory get, and does frontmatter become optional there? Does an admitted
  directory participate in the project/topic split or sit outside it? Does it
  appear in `index.md` as its own group?
- Hard constraint: `read` MUST NOT be able to admit `private/` or `archive/`.
  Those are excluded by location under §9 and D-006, and a config key that can
  un-exclude them defeats the only privacy mechanism the design has.
- Source: P-09 review 2026-08-17.

## E-016 — Close-out distillation pass
- What: when a project transitions to `completed` or `abandoned` (D-032's enum),
  sweep its logs and decisions for insights with cross-project durability and
  promote them upward — new or updated `topics/` notes, plus a final-state section
  appended to the project's charter recording outcome, why it ended, and where its
  knowledge went.
- Distillation **copies upward, never collapses or deletes**. Logs remain
  immutable, in place, and indexed (D-020, D-021). Explicitly **not** archiving:
  `archive/` stays reserved for the legacy vault and is out of bounds for live
  content.
- Scope note: this is the mechanism that makes a finished project's gotchas
  reachable. Without it, project-scoped recall never surfaces them again — the
  project is closed, so nothing loads its bundle, and its hard-won knowledge
  becomes unreachable while remaining perfectly intact on disk.
- trigger: the first project reaches a non-active status.
- Source: P-19 review 2026-08-17; interlock named in D-032.

## E-017 — Mechanize the `rendered-against:` currency check
- What: a test asserting `architecture.md`'s `rendered-against: D-NNN` header
  matches the tail of `docs/decisions.md` — turning D-068's visible drift bound into
  an enforced one. Same shape as D-028's meta-tests and D-053's grep companion.
- Why parked: nothing has slipped. The accretion ladder (D-035, D-039, D-041)
  requires restrictions to grow from observed failure, not anticipated failure, and
  the header field already makes drift visible on the artifact.
- trigger: a `rendered-against:` value is observed lagging the ledger after a
  decision that touched rendered content — i.e. the discipline clause failed once.
- Source: D-068.
