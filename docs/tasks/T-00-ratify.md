# T-00 — Ratify the planning-input decisions

**Size:** S · **Depends on:** — · **Status:** blocked on user approval
**Binds:** D-002, D-006, D-040, D-056, D-057, D-060, D-062, D-063, D-068

Gate on every other chunk. T-01 creates `tests/` and the first fixture vault, so the
layout must be ratified before it lands or the first commit encodes an unratified choice.

## Scope

- Append `D-069` to `docs/decisions.md` — the three planning inputs, the home of planning
  artifacts, and the second sanctioned byte-level claim.
- Append `D-070` immediately after it — `--topics` override semantics.
- Append `D-071` immediately after that — line endings pinned in transport, with
  `.gitattributes` landing in the **same commit** per D-040.
- Append `superseded-by: D-069 (2026-08-18) — fixture path only` to **D-006**. Partial
  supersession with a scope tail, per D-056's grammar — D-006's hard-error posture,
  `ZK_VAULT`-per-test rule, copy-to-`tmp_path` rule, gitignore split, and
  fixtures-≠-demo reasoning all stand untouched.
- Append `superseded-by: D-069 (2026-08-18) — sweep scope only` to **D-059**. Its `byte`
  sweep names D-012's determinism as *the only* legitimate claim; §13's fixture coupling
  is a second. Everything else in D-059 — the testimony/representation guarantee, the
  fence-delimiter clause — stands.
- Add one sentence to **SPEC §8.1** stating `--topics` semantics, with a dated seam
  citing D-070. Same change as the entry, per D-040.
- Bump `architecture.md`'s `rendered-against:` to `D-070` and **re-render** its
  repository-layout block: `docs/plan.md`, `docs/tasks/`, and the `tests/` subtree.

Order matters: `D-NNN` is contiguous and newest-at-bottom (D-047), so D-069 lands before
D-070 and neither may be written before the other is settled.

## Why an entry is required rather than a plan note

D-006 names `tests/fixtures/vault/`, singular. Three later decisions each require a
distinct fixture vault — D-053 an adversarial one, D-062 a ground state others extend,
D-063 the §13 examples — so one path cannot serve, and the plural is what the graph
requires. Per D-060 the substitution is recorded rather than silently reinterpreted; per
D-040 the text that specifies the superseded behaviour is amended in the same change.

Planning-artifact location needs a source of its own: CLAUDE.md's task discipline already
instructs "update `plan.md` status" and "note contract deviations in the task file"
without saying where either lives, and architecture.md may not originate the answer —
D-068 clause 1 forbids anything originating in a rendering.

## Proposed entry text

```markdown
## D-069 — 2026-08-18 — Non-shipping artifacts get their homes; fixtures are plural
- Decision, four parts. (1) **Planning artifacts live in `docs/`**: `docs/plan.md` for
  build state, `docs/tasks/T-NN-<slug>.md` one per chunk. Both are living text, edited
  in place (D-040). CLAUDE.md's task discipline already instructs updating them and
  never said where they were. (2) **Test layout: one module per script**, with
  `zk_lint.py` split by the D-042/D-064 layer taxonomy so a code's tests are findable
  from its §10 table row, and cross-cutting invariants in their own modules —
  `test_exclusion.py`, `meta/test_encoding.py`, `meta/test_sole_walker.py`.
  (3) **Fixture vaults are plural**, named directories under `tests/fixtures/vaults/`,
  each extending D-062's ground state; the ground state itself is built by a conftest
  factory rather than committed. (4) **SPEC §13's examples are the `examples/` fixture
  vault**, verified by `tests/test_examples.py` — lint-clean, and each §13 fence
  byte-equal to the file it names.
- **Supersedes D-006's fixture-path clause only.** Everything else in D-006 stands: hard
  error on absent config, `ZK_VAULT` set per test, copy to `tmp_path` before mutation,
  `zk.toml` gitignored with `.example` committed, fixtures ≠ demo, and the deliberate
  synthetic `private/` note.
- Why plural: D-053 needs an adversarial vault, D-062 needs a pristine base others
  extend, and D-063 needs a lint-clean example set asserted clean forever. Those three
  pull in incompatible directions inside one directory — the adversarial vault must
  contain the exclusion cases that the example vault must not — so a single path forces
  every suite to filter, and a filter is where an assertion silently stops covering
  what it claims. Per D-060 the substitution is recorded rather than reinterpreted.
- Why the ground state is programmatic while the rest is committed: git does not track
  empty directories (D-021, D-061), so `projects/` and `topics/` would need a
  `.gitkeep`, and a `.gitkeep` inside `projects/` is a stray file tripping ZK019 in the
  one fixture that must be pristine. D-006 rejected *purely programmatic* fixtures
  because they get unwieldy "once tests need real bodies" — two `mkdir` calls carry no
  bodies, so that reasoning does not reach the territory-only case.
- Why `examples/` carries an unrendered `project.md`: without a charter the directory is
  UNCHARTED and trips ZK024, making D-063's "lint-clean forever" unsatisfiable. D-063
  couples the example to the fixture, never the fixture to the example set, and §13's
  own criterion already explains why a charter earns no rendering.
- **Second sanctioned byte-level claim.** D-059's sweep names D-012's generated-file
  determinism as *the only* legitimate `byte` claim in SPEC.md. §13's fixture coupling is
  the second, and the category is stated rather than enumerated so a third does not need
  another entry: **byte claims are legitimate for generated or coupled artifacts and
  never for user testimony.** `index.md` is machine-written; §13's fences are
  machine-compared against the files they render. Byte-equality is how D-068's
  "structural coupling" is implemented, not an exception to it. Any other `byte`
  occurrence in SPEC.md remains a defect.
- No sixth script (D-007): the §13 coupling is asserted by a test, not generated by a
  renderer. A renderer only tests can invoke is a test.
- Rejected: keeping the singular path and filtering per suite (the filter is where
  coverage silently narrows); committing the ground state with a `.gitkeep` (a stray
  file in the pristine fixture); `tests/` layout left to convention (D-053's suite would
  scatter across five modules and stop being findable as one unit); planning artifacts
  at the repo root (architecture.md fences root to tooling-convention files); a separate
  entry per part (all four answer one question — where non-shipping artifacts live).
```

## Proposed entry text — D-070

```markdown
## D-070 — 2026-08-18 — `--topics` overrides the tag join; a flag that cannot narrow is half a flag
- Decision: `zk_recall.py --topics a,b` **replaces** the computed tag join rather than
  unioning with it — only the named topics are pulled. SPEC §8.1 gains one sentence
  stating it. problem.md's "(or explicit `--topics`)" already reads as an alternative
  rather than an addition, so it needs no seam under D-040.
- Why: the tag join is D-010's **computed default judgment** — index lines whose tags
  intersect the project's. An explicit flag is the user overruling that judgment, and a
  union can only ever add. **A flag that cannot narrow is half a flag**, and narrowing is
  the only reason to reach for it: the union outcome is already reachable by not passing
  the flag at all.
- Why it was recorded rather than left to the implementer: the gap was
  **invitation-shaped** in D-050's sense — under-specified in a way that invites a use it
  does not support. It surfaced because a task contract refused to guess, at the last
  moment where the answer was still free. The alternative was an implementer picking one
  silently and the other becoming a behaviour change nobody could date.
- Rejected: union (the flag becomes additive-only and cannot express "just these", which
  is the only reason to type it); erroring when `--topics` names a tag the project does
  not carry (reaching outside the join is the point of an override); leaving it undefined
  (D-050's latency — the format invites a use, and the first consumer to need it builds
  the wrong thing).
```

## Proposed entry text — D-071

```markdown
## D-071 — 2026-08-18 — Line endings are pinned in transport; `core.autocrlf` falsifies byte claims
- Decision: a repo-root `.gitattributes` pins `* text eol=lf` — **broad, not
  per-extension**. It lands in the same commit as this entry (D-040). Binary escape
  hatches are added when the first binary file arrives, never speculatively.
- Why: **three ratified rules assert byte-level properties that `core.autocrlf=true`
  silently falsifies on checkout.** D-012 requires `index.md` to render byte-identically;
  D-018 and D-028 require `newline="\n"` on every write in `scripts/`; D-068's structural
  coupling is asserted as byte-equality between SPEC §13's fences and the fixture files
  (D-069). A fresh clone on a Windows machine fails all three for reasons that have
  nothing to do with the code, and the cause is invisible in every diff.
- **Lineage: this is D-028's explicit-over-platform-default rule applied to git's
  transport layer.** D-028 banned bare `open()` because Windows silently substitutes the
  system ANSI codepage. `core.autocrlf` is the same shape one layer out — a platform
  default, silently applied, corrupting bytes in a repo whose tests assert them. Same
  failure signature too: correct-looking code, no exception, wrong bytes, discovered late.
- Why broad rather than per-extension: a narrow pin leaves **every future file class as a
  rediscovery**, and the rediscovery arrives as a failing test whose cause is not in the
  diff. CRLF churn in prose would also pollute every future seam diff, which is the
  surface D-040's amendments are read on.
- Guard: `zk` cannot enforce a checkout it does not perform, so the guard is **resident in
  the suite** — T-01 asserts a committed fixture reads with no `\r` in binary mode.
  Sibling to D-028's meta-test, and it catches a stripped `.gitattributes` or a
  misconfigured clone forever.
- Rejected: per-extension pinning (rediscovery per file class); `core.autocrlf=input` as a
  documented setup step (a setting the repo cannot verify, and D-006's posture is hard
  failure over relying on the user having configured something); the D-028 meta-test alone
  (it reads `scripts/` source for `newline=` arguments and cannot see what the checkout did
  to fixture bytes); binary escape hatches now (no binary exists — rules grow from observed
  need, D-035).
```

## Definition of done

- `D-069`, `D-070`, `D-071` appended at the bottom of `docs/decisions.md` in that order —
  IDs contiguous, newest last (D-047).
- D-006 and D-059 each carry one scope-tailed `superseded-by:` line, and nothing else in
  either entry is touched — an amendment is an append, not an edit (D-057).
- SPEC §8.1 carries the `--topics` sentence with its dated seam citing D-070.
- `.gitattributes` committed **with** D-071, then `git add --renormalize .` run
  immediately and its diff confirmed empty or line-ending-only — so the fixture vault is
  born under the pinned regime rather than migrated into it.
- `architecture.md`: `rendered-against: D-071`, layout block and the `zk_recall.py`
  section re-rendered, no claim introduced that does not trace to a decision or the plan.
- `docs/plan.md`'s "pending ratification" heading is retitled and the disclaimer removed.
- **No `enhancements.md` change.** Nothing here was deferred, and E-017 stays unmarked —
  P-23's §10↔`RULES` parity test is the same *shape* against a different pair and does
  not graduate it (D-023: no marker means still open).

## Audit rows — all verdicted

Thirty-seven rows surfaced by the plan audit, closed 2026-08-18. Thirty-five ratified
into [plan.md](../plan.md) §"Planning-jurisdiction register"; P-05 and P-17 conformed to
the graph; **P-21 promoted out of the register into D-070 above** — the audit's single
new decision. Rulings are recorded in plan.md §"Conformed to the graph" so the next
reader of D-053 and D-059 inherits their scope rather than re-deriving it.

## Note

If the entry is split or reworded, `docs/plan.md` §"Planning-input decisions" and every
task file citing D-069 are updated in the same change. Nothing else in the plan depends
on the entry's shape, only on its content.
