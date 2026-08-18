# T-06 — Lint harness + `file` and `frontmatter` layers

**Size:** L · **Depends on:** T-03 · **Status:** todo
**Binds:** SPEC §2, §3, §4, §5, §10, §11 · D-013, D-016, D-019, D-022, D-029, D-033,
D-034, D-035, D-036, D-039, D-042, D-052, D-054, D-055, D-058, D-064, D-065

The harness plus the two layers whose predicates read bytes, paths, and parsed YAML.
Detection only — `--fix` is T-08. Codes that will gain a fix are implemented as detectors
here and their `--fix` column is honoured, not stubbed.

## Interface contract

```python
Severity = Literal["error", "warning"]
Layer = Literal["file", "frontmatter", "structure", "content"]

@dataclass(frozen=True)
class Rule:
    code: str                           # "ZK001" — permanent identity
    severity: Severity
    layers: tuple[Layer, ...]           # tuple: ZK001 is dual
    failure_class: str
    fixable: Literal["yes", "no", "never"]

@dataclass(frozen=True)
class Finding:
    rule: Rule
    rel: PurePosixPath
    line: int | None
    message: str                        # self-describing, names the remedy

RULES: dict[str, Rule]                  # the code table, one row per §10 row

def lint(target: Path | None = None, *, fix: bool = False) -> list[Finding]: ...
def report(findings: Sequence[Finding], *, stream: TextIO = sys.stdout) -> str: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

Vault is ambient (T-01); `target` narrows the pass to one path within it.

`RULES` mirrors §10 exactly and is the **sole** code→metadata source in code, as §10 is
in prose. A rule without all four growth-clause fields cannot be constructed.

## Codes delivered

`file`: ZK008, ZK019, ZK024, ZK025, ZK026, ZK031, ZK032, ZK033, ZK034 (detect), ZK043,
ZK045.
`file` + `frontmatter`: ZK001.
`frontmatter`: ZK002, ZK003, ZK004, ZK005, ZK007 (detect), ZK010, ZK011, ZK016 (detect),
ZK017, ZK035.

ZK044 shipped at T-03 from the chokepoint. ZK023 is **retired forever** and its number is
never reissued (D-054).

## Behaviour that must be exact

- **Severity encodes exactly one bit: whether automation may act** (D-055). Error → act;
  warning → mention. Two tiers, never three. Finer discrimination is **presentation** —
  output may sort and group by layer and failure class, both already in the table.
- **`--fix` never moves, renames, or deletes files.** The `never` column is a standing
  prohibition, not an unimplemented feature. Codes marked `never` must not acquire a fix
  at T-08 either.
- **ZK010 floor is 20 characters**, and its job is exactly one class — **non-attempts**.
  `WIP`, `misc`, `various`, `Fixed it` are rejected on length alone, which is why none
  appears in ZK011's list.
- **ZK011 is three shapes and nothing else**: `worked on`, `session notes`, `notes on` —
  case-insensitive, **start-anchored**. The list is **data with a single home** (§5) and
  **grows only from observed lazy summaries in the real vault**, each addition recorded as
  a decision entry naming the summary that motivated it. Never speculatively — every
  speculative entry in the original list was a false positive.
- **ZK017 detects multi-topic packing, not size** (D-034). Catalog bloat is a vault-level
  property measured by `zk_index.py`; a per-note limit cannot detect it.
- **ZK035 fires only when the lookalike known key is absent.** `sumary` beside a valid
  `summary` is **silent** — the failure it predicts does not exist. Deliberately unlike
  D-022's plain-warn rule for directories: a stray key is routinely written by co-tenant
  tools, and warning on every plugin key devalues every warning.
- **ZK025/ZK026 are distinct codes**, plain and near-miss, and the near-miss message
  **leads with the correction, not the silence option**. `ignore` from T-02 suppresses;
  it grants nothing.
- **ZK019 gets no ignore list** (D-058) — stray files are transient and each has a
  terminating remedy, so a file ignore list is config for an empty room, and it would
  reintroduce config-driven invisibility.
- **ZK045 catches what the coherence family cannot see**: that family keys on a declared
  `type`, and a file with no recognizable type gives it nothing to compare.
- **ZK043 cannot fire on the first log about a subject.** The harshness is **accepted,
  not mitigated** — retrieval resolves by frontmatter and index line, never by filename
  spelling.
- **Parse-failure jurisdiction** (D-052): lint owns severity across the three shapes —
  no frontmatter, malformed YAML, valid YAML of the wrong shape. It consumes
  `NoteParseError.reason` from T-03 and does not re-derive it.
- **Warning accumulation** (D-055): at ~20 warnings the summary says so and splits the
  remedy — mechanical ones to `--fix`, the rest to review. **Exit stays 0** — the
  threshold is diagnosis, not control flow. The number is honestly a guess and should
  move once real vault data exists; the failure class, *reckoning-avoidance*, is not.
- **Exit codes** (§11): 0 clean or warnings-only, 1 errors found (lint ran; the findings
  **are** the result), 2 could not run.
- **Linting `private/` or `archive/` is a no-op.** Lint consumes `zk_read.py`; it does
  not walk.
- Every message is self-describing and names the resolution (D-016). ZK031 is
  **directional**: `invalid slug 'game_x' — use 'game-x'`.

## Fixtures

`tests/fixtures/vaults/malformed/` — one note per negative failure class, each named for
the code it trips (`zk010-short-summary.md`, `zk035-near-miss-key.md`, …). Notes trip
other codes incidentally; tests assert **"code X present for path Y"**, never
"vault is clean", so incidental findings are signal rather than interference.

## Definition of done

- `pytest` green; standing DoD applies.
- Every code above has **at least one positive and one negative** case — a rule with no
  negative case has not been shown to discriminate.
- `RULES` matches §10 row for row: same codes, same severities, same layers, same
  `--fix` column. Asserted by a test that parses §10's table, so drift between the spec
  and the code fails a test rather than being noticed later.
- `minimal/`, `populated/`, and `examples/` all lint **clean** — zero errors, zero
  warnings.
- The ~20-warning announcement fires with exit status 0.
- Exit-1-on-errors and exit-0-on-warnings-only both asserted.
- **AC-3 (partial)**: missing frontmatter field, bad enum, and misnamed log file are all
  caught. Prose-heavy body is T-07.

## Contract deviations

*(record here during execution — none yet)*
