# research.md — Prior-Art Survey

- Scope agreed 2026-08-14: LLM memory systems (core) + ADR/devlog conventions (narrow slice).
- Excluded: MCP-as-protocol, RAG-as-architecture, human-first PKM. Markdown-on-disk designs
  behind MCP still counted; representation-agnostic selection findings still counted.
- Priority: recall/context-assembly pattern > schema audit (pitfalls only, schema is decided)
  > lint (minor). Skill-structure prior art dropped — scripts are testable directly.
- Stopped at 5 items: item 5 onward yielded pitfalls-for-existing-decisions, not new patterns.

## 1. obsidian-second-brain (eugeniughelbur) — closest system match

- Cross-CLI Obsidian skill, 44 commands, self-rewriting notes, scheduled agents, optional
  semantic search. Karpathy LLM-Wiki descendant. ~3.2k stars, active.
- **Applies:** "AI-first vault rule" = our design decision #3, independently derived.
  index.md read-first catalog; entities/projects/daily/logs/decisions folders; write-time
  validator ≈ our lint-at-write; per-project vault via env var in `.claude/settings.json`
  merged over global = our `ZK_VAULT` mechanism, proven.
- **Rejected elements:** synthesize/reconcile/challenge, scheduled agents, research toolkit,
  semantic search, kanban — all match our deferred/out-of-scope list. 44-command sprawl is
  evidence *for* our two-skill v1.
- **Steal:**
  - Tiny always-loaded core (`CRITICAL_FACTS.md`, ~120 tokens) + tiered context budgets
    (L0–L3). Our `--logs N` / `--deep` is the crude version.
  - Author names the failure mode: "append-only breaks at scale." Expect this pressure on
    `decisions.md` and `log/` by ~log 20. Their fix (self-rewriting) is rejected for v1.
  - `retrieval-eval` idea: recall@k on natural-language questions against the vault — cheap
    way to judge recall quality at the 20-log checkpoint.

## 2. claude-memory-compiler (coleam00) — closest recall-pattern match

- Hooks capture session transcripts → Agent SDK extracts decisions/lessons/gotchas into
  daily logs → compiled into cross-referenced articles. Karpathy LLM-KB architecture.
- **Applies:** retrieval = structured index.md, no vectors, no embeddings — our exact
  retrieval design.
- **Rejected elements:** hook-driven auto-capture (we log deliberately); dailies→articles
  compilation ≈ our deferred `synthesize`.
- **Steal — key empirical claim of the survey:** at 50–500 articles, LLM-reads-index
  outperforms vector similarity; RAG only becomes necessary at ~2,000+ articles when the
  index exceeds the context window.
  - Validates no-embeddings with a concrete ceiling.
  - Measurable failure trigger: "index.md no longer fits in context," not a vibe.
  - Consequence: `summary:` line is the retrieval engine → lint must be strict on it.

## 3. agentmemory (jayzeng) — closest layering match

- Local markdown store for Claude Code/Codex/Cursor/Agent: long-term facts, daily logs,
  topic notes, scratchpad. Skills on top; files are source of truth; no DB.
- **Applies:** near-identical taxonomy (facts≈project.md, daily logs≈log/, topics≈topics/).
  Explicit retrieval: base context at session start, search deeper when a task needs it.
  Multi-agent parity via plain CLI = our LLM-agnostic requirement, demonstrated.
- **Rejected elements:** optional qmd semantic search; global (not project-centric) store.
- **Steal:** two-phase recall shape — cheap base bundle at start, deeper pulls on demand.
  Needs no architecture change for us; it's `zk_recall.py` with different flags mid-session.

## 4. Claude Code internal memory — pointer-index pattern

- Layered: memory.md as pointer index → load specific file; CLAUDE.md as per-project
  constitution; agent maintains ("self-heals") its own memory files.
- **Applies:** our index.md → path resolution is the same pattern; our CLAUDE.md snippet
  plugs into the constitution layer as designed. Vendor-convergence signal.
- **Gap it exposes:** we have no update path for stale `project.md` in v1.
- **Steal:** read-before-write discipline — read current file before updating, to avoid
  clobbering valid info. One-line instruction in zk-log SKILL.md, near-zero cost.

## 5. ADR conventions (Nygard / MADR literature) — decisions.md audit

- Consensus: one decision per record, one page max, per-decision status
  (proposed/accepted/deprecated/superseded). Files-per-decision, not single log.
- **Applies:** our 4-line entry = legitimate Nygard compression. Strongest survival
  finding supports us: co-location with where work happens is the #1 determinant of ADR
  survival — our decisions live in the file Claude reads every session.
- **Rejected elements:** one-file-per-decision + numbering (ceremony not worth it at
  personal scale); governance/approval workflow.
- **Pitfalls for us:**
  - Supersession is the known weak point of markdown ADRs — status fields rot because
    nobody updates them. Our append-only decisions.md has *no* supersede mechanism and
    injects stale decisions into every bundle. → adopt marker (see decisions.md D-002).
  - Even the canonical ADR repo concedes strict immutability loses to date-stamped
    amendments in practice. Supports marker-line over never-touch.
  - Abandonment failure ("five ADRs then silence") stems from no trigger rule; our
    `/zk:log` step 2 automates the trigger. Design validated.

## Skipped (diminishing returns)

- EchoVault, RecallNest, memory MCP servers: value concentrated in SQLite/vector layers
  we excluded.
- Self-pruning context-graph plugin: pruning solves a scale we won't reach pre-checkpoint.
- lucasrosati claude-code-memory-setup: config guide, no new patterns.

## Actionable outputs

- Binding choices → decisions.md D-001..D-005 (marker + contradiction check,
  summary enforcement split, read-before-write, enhancements split).
- Parked items → enhancements.md E-001..E-006 (semantic lint, hook promotion,
  retrieval-eval, embeddings trigger, tiered loading, generated active-decisions
  header). Deferrals carry triggers; review at the 20-log checkpoint.
