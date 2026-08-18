# plan.md — build plan (`zk` v1)

Execution order and chunk boundaries. Rules → [CLAUDE.md](../CLAUDE.md). Structure →
[architecture.md](../architecture.md). Vault contract → [SPEC.md](SPEC.md).

This file is **living text** (D-040, D-057) — status is edited in place. Task files live
in [tasks/](tasks/), one per chunk, and carry the interface contract and
definition-of-done. Contract deviations are recorded in the task file, not here.

**Status legend:** `todo` · `in-progress` · `done` · `blocked`

## Sequencing

Fixed by D-008: five scripts verified green → two SKILL.md files iterated live → demo
vault. Within the script phase the order is dependency-driven, not surface-driven —
chunk one is the thinnest end-to-end slice, and each later chunk closes a seam the
skeleton left open by name.

| ID | Chunk | Touches | Size | Depends on | Status |
|---|---|---|---|---|---|
| T-00 | Ratify planning-input decisions | `decisions.md` `architecture.md` | S | — | **done** |
| T-01 | Walking skeleton | `zk_config` `zk_read` `zk_recall` | M | T-00 | **done** |
| T-02 | Config completion | `zk_config` | M | T-01 | **done** |
| T-03 | Read hardening + exclusion suite | `zk_read` | L | T-01 | todo |
| T-04 | Index + vault init | `zk_index` `zk_config` | L | T-02, T-03 | todo |
| T-05 | Recall completion | `zk_recall` | M | T-04 | todo |
| T-06 | Lint harness + `file`/`frontmatter` | `zk_lint` | L | T-03 | todo |
| T-07 | Lint `structure` + `content` | `zk_lint` | L | T-06 | todo |
| T-08 | Lint `--fix` | `zk_lint` | M | T-06 | todo |
| T-09 | SPEC §13 example fixtures | tests, SPEC | S | T-07 | todo |
| T-10 | Skill: `zk-recall` | `skills/zk-recall/` | M | T-05, T-07 | todo |
| T-11 | Skill: `zk-log` | `skills/zk-log/` | L | T-08, T-10 | todo |
| T-12 | Packaging + demo vault | README, `.claude/`, demo | M | T-11 | todo |

T-00 gates everything: T-01 creates `tests/` and the first fixture vault, so the layout
must be ratified before the first commit encodes it. Scripts are green at T-09. Skills
begin at T-10 — the D-008 boundary.

**Dependencies are code-level, not thematic.** Corrected by the plan audit, 2026-08-18:

- **T-08 depends on T-06, not T-07.** All three fixable codes — ZK007, ZK016, ZK034 —
  are `frontmatter` and `file` layer, so `--fix` needs no structure detector. T-07 is a
  soft edge for DoD strength only ("same set of unfixable findings").
- **T-10 depends on T-07.** Undeclared until the audit: the scaffold lints its charter,
  and charter section codes (ZK018, ZK021, ZK022) are `structure` layer.
- **T-00 is a commit-time gate, not a code gate.** No script code depends on it.

Three lanes run parallel after T-01: `T-02` alone · `T-03 → T-06 → {T-07, T-08}` ·
`T-04 → T-05`. Critical path is T-01 → T-03 → T-06 → T-07 → T-10 → T-11 → T-12.

## Planning-jurisdiction register

Choices with no SPEC section or decision entry behind them, surfaced by the plan audit
and **ratified as plan state 2026-08-18**. They bind the task files and nothing beyond
them. A choice here that later needs to bind vault or script *contract* is promoted to a
decision entry; until then this is its only home.

| Rows | Substance |
|---|---|
| P-01, P-02 | Record types (`NamedTuple` / `dataclass`) throughout; `main(argv) -> int` as the CLI seam |
| P-03, P-04 | `cwd` / `env` injection on resolution; `ZkError` carrying `exit_code` |
| P-06 | `iter_note_paths(..., subtree=)` |
| P-08, P-16, P-25, P-37 | Fixture scale and naming: `minimal/` frozen at two notes, `populated/` contents, `malformed/` notes named for the code they trip, demo vault scale |
| P-09, P-11, P-13, P-15, P-19, P-20 | Test method: `PurePosixPath` comparison, `tmp_path` config trees, drive-letter and UNC cases, visible symlink skips, shuffled-listing determinism, the interim broken-note fixture |
| P-10, P-14, P-18, P-27, P-28 | Internal seam names: config lookup, stray production, `render`/`stamp`/`differs`, block and decision parsing, `fix_note(note, findings)` |
| P-12 | `zk.toml.example` carries a commented `ignore` line |
| P-22, P-23 | `Rule` rejects incomplete rows at construction; a test parses §10's table to assert `RULES` parity |
| P-24, P-26 | Positive and negative case per code; assertions keyed to code + path, never "vault is clean" |
| P-29–P-32 | `--fix` test contract: idempotence, re-lint delta, clean-vault fixed point, path-set no-move check |
| P-34 | `test_examples.py` self-tests its own detector |
| P-36 | Warning-inaction proven by inducing ZK012 on correct prose |

P-23 is E-017's *shape* applied to a different pair — §10 against `RULES`, not
`rendered-against:` against the ledger tail. Ratified deliberately here; it does **not**
graduate E-017, which stays parked and unmarked.

### Conformed to the graph

Rows verdicted against the plan and toward the decision record (D-060 — the graph
outranks its authors), plus the scope rulings that settled the rest. All applied.

- **P-05 → `resolve_project(slug)`, verbatim from D-020.** Consequence, applied in full:
  **the vault is ambient**, resolved once per process by `zk_config.current()` and
  dropped from every read-path signature in all four consuming scripts. A one-argument
  resolver beside a two-argument reader is the incoherence that invites reversal, and
  D-050's law says close an invitation while it is cheap — a parameter threaded
  everywhere but one function is a standing invitation for a later session to normalize
  it in whichever direction it guesses. `zk_config.init_vault(target)` keeps its
  argument: it creates a vault rather than reading one. Tests set `ZK_VAULT` (D-006) and
  call `reset_cache()`.
- **Side effect worth recording: conforming to D-020 strengthened D-014.** The banner's
  once-per-process semantics now **falls out of memoizing `current()`** instead of
  depending on each script calling `announce` exactly once. A discipline obligation
  became a structural one, unplanned. Conforming to one decision can strengthen another;
  when it does, say so, because the next reader will otherwise attribute the property to
  care rather than construction.
- **P-17 → the unknown-key round-trip lives only in T-08.** D-029 places the guarantee in
  `--fix`'s test contract and §10 states it there. No coverage lost: T-08's fixture
  round-trips through `read_note` by construction. D-029's separate **inert** clause
  stays in T-03 — preservation and inertness are different obligations.
- **P-07 → D-053's one-suite clause is scoped: it binds the behavioral fixture suite.**
  That suite lives solely in T-03, as one findable unit, which is what the clause is for.
  **T-01 unit-testing the `is_excluded` it writes does not fragment it** — a chunk
  testing the function it authors is ordinary layering, not a staged rollout of the
  suite. Recorded here so the next reader of D-053 inherits the scope rather than
  re-deriving it and concluding the plan violates it.
- **P-33 → byte-equality is adopted as the operationalization, and it *implements*
  D-068's "structural coupling" rather than deviating from it.** Two guarantees, stated
  separately because they answer different questions: **lint-clean** (D-063) says the
  examples are valid; **byte-equal** says SPEC's rendered fences *are* the fixture
  files, so what is shown and what is tested cannot drift.
- **P-35 → lints clean on the first pass is the bar.** A scaffold emitting notes that
  need fixing is the system failing its own schema at birth. The verdict is trivial; its
  payload is the **T-10 → T-07 edge**, now written down. Both edge corrections are
  applied: T-10 gained T-07, T-08 lost its false T-07 dependency.

### Promoted out of the register

**P-21 is a decision, not a plan choice** — either answer adds a sentence to SPEC §8.1.
Drafted as **D-070** in [tasks/T-00-ratify.md](tasks/T-00-ratify.md) and appended there,
because `decisions.md` is contiguous (D-047) and D-069 must land first.

The register produced exactly one new decision, and it surfaced because a task contract
**refused to guess** at an under-specified flag. That is the invitation-shaped gap of
D-050 caught at the last moment where the answer was still free.

## Deferral seams

The skeleton is thin by design, and every gap it opens is closed by a named chunk. A
seam not listed here is a defect, not a deferral.

| Opened in | Seam | Closed by |
|---|---|---|
| T-01 | `zk.toml` resolution — `ZK_VAULT` branch only | T-02 |
| T-01 | Bundle section 1 (index section) — no `index.md` exists yet | T-05 |
| T-01 | `--logs` / `--deep` / `--topics` flags | T-05 |
| T-01 | Exclusion is implemented and unit-tested; the behavioral suite is not built | T-03 |
| T-01 | The no-vault message names `zk_config.py --init`, which is not a flag yet | T-04 |
| T-01 | `ground_vault` writes territory only — no `index.md` to render against | T-04 |

The `--init` row is the seam the T-01 contract asked for deliberately: §1 and D-006
require the no-vault error to name the command that makes a vault, and D-061 names that
command `zk_config.py --init`. Writing the message now and the flag at T-04 keeps the
message final rather than provisional; the alternative was a stub, which this chunk bans.
| T-03 | Suite asserts reads only — index and bundle arms have no target yet | T-04, T-05 |
| T-04 | `--init` prints the config next-step; `zk.toml` writing is never automated | — (by design, D-022) |
| T-06 | `--fix` is not implemented; fixable codes detect only | T-08 |

## Acceptance criteria → chunks

problem.md §"Acceptance criteria", mapped so no criterion is orphaned.

| AC | Criterion | Chunk |
|---|---|---|
| 1 | Fresh vault scaffolds from empty | T-04 |
| 2 | Bundle well-formed; `private/` absent even with `--deep` | T-05 (read arm T-03) |
| 3 | Lint catches the four named classes; `--fix` resolves mechanical ones | T-06, T-07, T-08 |
| 4 | `zk_index.py --check` stable on second run | T-04 |
| 5 | Both skills install and trigger from their slash commands | T-10, T-11, T-12 |
| 6 | End-to-end: recall → scaffold → work → `/zk:log` → recall reflects it | T-11 |
| 7 | Identical behaviour on Windows and POSIX | **every chunk** — standing DoD line |

AC-7 is not a chunk. It is a line in every task file's definition-of-done, because a
platform defect introduced in one chunk is invisible until another chunk trips it.

## Standing definition-of-done

Applies to every chunk; task files add to it, never replace it.

- pytest green before any commit to `zk/` (CLAUDE.md).
- No bare `open()` in `scripts/` — `encoding="utf-8"` on every call, `newline="\n"` on
  every write (D-028, §3). The meta-test lands in T-01 and guards from then on.
- `pathlib` throughout. No `os.path` string joins, no hardcoded separators.
- Python 3.11+, stdlib + `pyyaml` at runtime. A new runtime dependency needs a decision
  entry; pytest is exempt.
- Every new failure path is classified against D-019's test in the same change, and the
  classification is stated where the error is specified (§11).
- Every nonzero exit prints an actionable message to stderr naming the resolution
  (D-016). Where a near-match exists, the message names it.
- No vault walking outside `zk_read.py` (D-053, §9).

## Environment — verified 2026-08-18

Global `CLAUDE.md` names an Anaconda interpreter that does not exist on this machine and
states Python is not on PATH. Both are stale. Actual, confirmed at T-00 close:

| | Value |
|---|---|
| Interpreter | `C:\Users\bbodee\AppData\Local\Programs\Python\Python314\python.exe` |
| Version | CPython 3.14.6 — clears the 3.11+ floor; `tomllib` imports, so D-017 adds no dependency |
| On PATH | **yes**, as `python` |
| `pyyaml` | **6.0.3** — installed at T-01 |
| `pytest` | **9.1.1** — installed at T-01 |

Recorded here rather than acted on: global `CLAUDE.md` is the user's private file and
outside this repo's jurisdiction. T-01 installed the two packages as its first step.

## Rendering obligations (D-068)

Every decision arising from this build bumps `architecture.md`'s `rendered-against:`
field — unconditional and free. A decision that changes what architecture.md *claims*
also re-renders that section in the same change. Bumping is not re-rendering.

Task files record which sections they touch. At T-09 the script-layer sections of
architecture.md are re-read against shipped behaviour, since a rendering that describes
unbuilt code and a rendering that describes built code are checked differently.

## Planning-input decisions — **ratified as D-069 (2026-08-18)**

Three choices the ledger left to the planning phase, now binding repo state. The entry
also records the second sanctioned byte-level claim and supersedes D-006's fixture-path
clause and D-059's sweep scope. `--topics` semantics went out separately as D-070, and
line-ending policy as D-071.

**(1) Test-suite layout.** One test module per script; `zk_lint.py` splits by the
D-042/D-064 layer taxonomy so a code's tests are findable from its §10 table row.
Cross-cutting invariants get their own modules — D-053 requires its enforcement to be
findable as one unit ("one rule, one function, one fixture suite"), which a scatter
across five modules defeats.

```
tests/
├── conftest.py                  # vault factories; sets ZK_VAULT; copies to tmp_path
├── fixtures/vaults/<name>/      # see (2)
├── test_config.py
├── test_read.py
├── test_recall.py
├── test_index.py
├── test_lint_file.py
├── test_lint_frontmatter.py
├── test_lint_structure.py
├── test_lint_content.py
├── test_lint_fix.py
├── test_exclusion.py            # D-053 behavioral suite — read, index, and bundle arms
├── test_examples.py             # D-063 conformance
└── meta/
    ├── test_encoding.py         # D-028 — no bare open(), no write without newline=
    └── test_sole_walker.py      # D-053 grep companion
```

**(2) Fixture organization.** Fixture vaults are named directories under
`tests/fixtures/vaults/`, each a complete vault, each an extension of D-062's ground
state. The ground state itself is **built by a conftest factory** — two `mkdir` calls
plus `zk_index.py`'s render path — because git does not track empty directories, and a
`.gitkeep` inside `projects/` would be a stray file tripping ZK019 in the one fixture
that must be pristine. D-006 rejected *purely programmatic* fixtures on the grounds that
they get unwieldy "once tests need real bodies"; two `mkdir`s carry no bodies, so the
rejection does not reach this case. Content-bearing fixtures stay committed files.

| Vault | Job | Frozen? |
|---|---|---|
| *(programmatic)* | D-062 ground state — `--init` expectation, empty-collection messages | ground state is normative, §12 |
| `minimal/` | exactly two notes: `project.md` + one log. T-01's skeleton surface | **yes** — never grows, or T-01's assertions rot |
| `populated/` | happy path: charter, `decisions.md`, 3 logs, 2 topics, one UNCHARTED dir with a log | no |
| `exclusion/` | every row of §9's adversarial table, symlinks and slug shadowing included | no |
| `malformed/` | one note per negative failure class, named for the code it trips | no |
| `examples/` | the §13 renderings, lint-clean forever | see (3) |

`populated/` carries the UNCHARTED directory deliberately: D-020's orphan-logs rule and
D-049's two index asymmetries have no other test surface.

**(3) Example-fixture path.** `tests/fixtures/vaults/examples/`, notes at their real
vault-relative paths — `projects/game-x/log/2026-08-14-save-system.md`,
`projects/game-x/decisions.md`, `topics/serialization.md`. The vault **also carries a
`projects/game-x/project.md`** that §13 does not render, because without a charter the
directory is UNCHARTED and trips ZK024, which would make "lint-clean forever"
unsatisfiable. §13's own criterion already explains the omission from the *spec* — a
closed section vocabulary is a single-rule shape — and D-063's licence couples the
example to the fixture, never the fixture to the example set.

Coupling is verified, not generated: `tests/test_examples.py` asserts (a) every note in
the fixture vault lints clean, and (b) each fenced block in SPEC §13 is byte-equal to the
fixture file it names. Regeneration stays a manual copy. **No sixth script** — D-007
fixes the surface, and a renderer that only tests can invoke is a test.
