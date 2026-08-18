# T-12 — Packaging + demo vault

**Size:** M · **Depends on:** T-11 · **Status:** todo
**Binds:** SPEC §9, §12 · D-006, D-007, D-014, D-018, D-053, D-061 · E-007, E-012, E-016

D-008's third deliverable, last because it should showcase **finished** behaviour —
including private-note exclusion, which cannot be demonstrated before it works.

## Scope

- `README.md` — install and usage.
- `.claude/settings.json` — the deny-rule template.
- The demo vault.

## Deliverables

**`.claude/settings.json`** — a `Read` deny rule for `<vault>/private/**` and
`<vault>/archive/**`. It is a **template**: it does nothing until the user merges it into
their own project or user settings, and **the README must say so**. A template in the repo
that looks active is worse than no template.

**`README.md`** must cover, and each item exists because a decision made it necessary:

| Section | Why it is required |
|---|---|
| Install: symlink or copy `skills/zk-recall/` and `skills/zk-log/` into `.claude/skills/`, set `ZK_VAULT` | D-007 — install is manual in v1; plugin packaging is parked at E-007 |
| `zk_config.py --init <path>` to create a vault | D-061 — D-006's no-vault error names this command; the loop must close in the docs too |
| `zk.toml` vs `ZK_VAULT`, and that the env var wins | D-014 |
| That the banner may print a **different path than you typed** | D-018 — `resolve()` follows the junctions OneDrive uses; correct, and occasionally surprising |
| The deny-rule template must be **merged** to take effect | Above |
| Per-project `CLAUDE.md` snippet: `At session start, run /zk:recall <project-slug>.` | problem.md |
| That exclusion gates **what enters context, not what reaches Anthropic** | CLAUDE.md non-negotiable 5, §9 — anything Claude reads is sent, and the README is where a user could otherwise conclude otherwise |
| Python 3.11+, `pyyaml`, interpreter not on PATH on the author's machine | CLAUDE.md |

**Demo vault** — a **separate deliverable from the test fixtures** (D-006). Fixtures want
minimal and adversarial; demos want rich and legible, and one artifact cannot serve both.

- Rich enough that a bundle reads well: 2 projects, one with a real decision history
  including a partial supersession, several logs across dates, 3 topics with genuine
  cross-project joins.
- **Includes a `private/` note**, so exclusion is demonstrable rather than asserted. A
  demo that only claims privacy works is the weakest possible demonstration of the one
  rule whose failure costs privacy.
- Lint-clean and index-current, verified by running the real scripts.
- Not the vault the user's `zk.toml` points at, and shipped without a `zk.toml` —
  D-006 forbids a committed config that could silently absorb a real session's logs.

## Behaviour that must be exact

- The demo vault lives **inside the repo** while `zk.toml` requires an **absolute** path
  (D-017). This fires **E-012's trigger verbatim** — "a vault needs to travel with a
  clone — e.g. the demo vault shipping inside the repo (D-008's third deliverable)."
  **Do not implement relative paths inline.** Per D-005 a fired trigger graduates via a
  new decision entry or is consciously re-parked, and the honest v1 answer is documented
  `ZK_VAULT` for the demo. Record which it was.
- **E-007's trigger also fires here** — "v1 working end to end (acceptance criteria 1–7
  met)." Same treatment: graduate by decision or re-park consciously. Do not drift into
  plugin packaging because the trigger fired.
- No new script. No sixth entry point. Packaging is documentation and one JSON template.

## Definition of done

- **AC-1 through AC-7 all pass**, verified by executing them against the demo vault
  rather than by inspection.
- **AC-7 explicitly**: the full suite plus a manual end-to-end run on **both** Windows
  (PowerShell) and POSIX. This is the last chance to catch a platform defect, and every
  earlier chunk's AC-7 line was a promise this one collects on.
- A `private/` note in the demo vault is absent from `index.md`, from every bundle
  including `--deep`, and from every lint report.
- README's install steps followed literally, from a clean clone, produce working skills.
- Both fired triggers (E-007, E-012) are dispositioned — graduated by a decision entry or
  consciously re-parked, and **which one is recorded**. An unmarked entry means still
  open (D-023).
- E-016's trigger is **checked, not assumed**: if the demo vault contains a non-active
  project status, the close-out distillation trigger has fired too.
- `docs/plan.md` marked complete; `architecture.md` `rendered-against:` bumped and any
  section the packaging work changed is re-rendered (D-068).
- The ~20-log checkpoint is noted as the next review gate — problem.md's out-of-scope
  list and `enhancements.md` are reviewed together there, not before.

## Contract deviations

*(record here during execution — none yet)*
