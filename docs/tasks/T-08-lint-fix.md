# T-08 — Lint `--fix`

**Size:** M · **Depends on:** T-06 (T-07 soft, DoD strength only) · **Status:** todo
**Binds:** SPEC §7.0, §10 · D-018, D-024, D-028, D-029, D-044, D-046, D-055, D-059, D-066

The write half of lint. Its whole contract is one distinction: **`--fix` preserves
testimony and may repair representation.** Everything below follows from that.

*Dependency corrected 2026-08-18 by the plan audit.* This file previously depended on
T-07. It does not: all three fixable codes — ZK007, ZK016, ZK034 — are `frontmatter` and
`file` layer and ship in T-06. T-07 is needed only for the DoD lines asserting the
unfixable set is unchanged and that clean vaults are a fixed point. **T-08 runs parallel
with T-07.**

## Interface contract

```python
def fix_note(note: Note, findings: Sequence[Finding]) -> str | None: ...
    # returns new file text, or None if nothing changed

def serialize_frontmatter(fm: Mapping[str, Any]) -> str: ...
    # canonical-then-original key order; unknown keys preserved by value

def lint(target=None, *, fix: bool = False) -> list[Finding]: ...   # fix arm live
```

`fix_note` takes findings rather than re-detecting — one detection pass, so a fix can
never disagree with the report that motivated it.

## What may be repaired — representation

| Repair | Code | Source |
|---|---|---|
| Line endings → `\n` | — | D-018, D-028 |
| BOM stripped | ZK034 | D-028 |
| Tags lowercased, kebabbed, deduped | ZK007 | §4 |
| Missing `updated` filled | ZK016 | §7.0 |
| Frontmatter key order, quoting, flow style | — | D-029 |
| Fence **delimiters** — style and length | — | D-059 |

## What is never touched — testimony

- Any word of body content.
- Frontmatter **values**.
- Fence **contents**. D-042 made fences opaque to *structure rules*; D-059 settles that
  `--fix` may normalize the delimiters and never what they enclose.
- Files: **`--fix` never moves, renames, or deletes.** Standing prohibition (D-024), not
  an unimplemented feature.
- **`updated`, except when missing.** It is the tamper detector for testimony, and
  repairing representation is not tampering — so ZK020 fires only on real violations
  rather than on the vault's own maintenance.

## Behaviour that must be exact

- **ZK016 fills a missing `updated` with today for `project` and `topic`, and with the
  **filename date** for logs** (§7.0, D-046). Today's date on a log would immediately
  trip ZK020's later-than-filename warning — the fix would create the defect.
- **Mechanical means provably meaning-preserving** (D-044). Reordering log sections is
  the **first rejected restructuring candidate** and later proposals cite that test rather
  than relitigating it: cross-section references (`## Next` saying "the above", a gotcha
  referring to a decision by position) are meaning-bearing and invisible to a block mover.
- **The body guarantee is testimony, not bytes** (D-059). "Preserves body bytes" is
  **false** — newline normalization and BOM stripping both change body bytes on
  conforming input. A guarantee contradicted by shipped behaviour would be read as a
  contract, tested as one, and fail.
- **Preservation is semantic, not byte-level** (D-029): values round-trip equal; quoting,
  flow style, and whitespace may normalize.
- **Key order on write** is canonical-then-original: `type`, `project`, `tags`, `status`,
  `updated`, `summary`, then unknown keys in their original relative order.
  **Conventional** (D-066) — fixedness only; there is no rationale to improve toward.
- **`--fix` never rewrites prose.** ZK010–ZK012 are reported for the author.
- **`--fix` on an old log is legal by construction** (D-046) — an operation that
  preserves meaning cannot alter testimony, so no exception is needed. Suspending `--fix`
  on logs would freeze them against schema evolution.
- **Every `never` code stays never.** ZK013, ZK015, ZK027–ZK030, ZK031, ZK032,
  ZK039–ZK045 acquire no fix in this chunk or any later one.
- **Warning-accumulation announcement** goes live end to end (D-055): the summary names
  the count, splits the remedy — mechanical to `--fix`, the rest to review — and exit
  stays **0**.

## Definition of done

- `pytest` green; standing DoD applies.
- **The `--fix` round-trip fixture, which is part of the contract and not an optional
  test** (§10, D-029): a note carrying `aliases`, `cssclasses`, a nested mapping, a list,
  and a quoted string is asserted **semantically equal** after a fix pass — every key
  present, every value equal. Formatting is explicitly not guaranteed.
- **Idempotence**: a second `--fix` pass changes nothing. Asserted on bytes.
- **`--fix` then re-lint** leaves zero fixable findings and the same set of unfixable
  ones — a fix that resolves a finding it was not given is out of contract.
- A log with a missing `updated` gets the **filename date** and does not subsequently
  trip ZK020. Asserted as one sequence, since the two rules only conflict in composition.
- A note whose only defect is a BOM is repaired without any other byte changing beyond
  newline normalization.
- Fence delimiters normalize; fence contents are asserted byte-identical.
- No file was moved, renamed, or deleted by any fix path. Asserted by comparing the
  vault's path set before and after.
- `minimal/`, `populated/`, `examples/` unchanged by a `--fix` pass — a clean vault is a
  fixed point.
- **AC-3 completes**: `--fix` resolves the mechanical cases and reports the rest.
- **Scripts are green here.** This is the last chunk of D-008's script phase before the
  conformance pass at T-09.

## Contract deviations

*(record here during execution — none yet)*
