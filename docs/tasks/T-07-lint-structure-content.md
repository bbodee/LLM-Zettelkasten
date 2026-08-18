# T-07 — Lint `structure` and `content` layers

**Size:** L · **Depends on:** T-06 · **Status:** todo
**Binds:** SPEC §6, §7.1, §7.2, §7.4, §10 · D-002, D-009, D-011, D-013, D-026, D-030,
D-031, D-038, D-039, D-041, D-042, D-043, D-044, D-045, D-047, D-056, D-064, D-065

The markdown block model, the closed section vocabularies, the decision-log grammar, and
the two prose-reading codes. Detection only.

## Interface contract

```python
class Block(NamedTuple):
    kind: Literal["heading", "paragraph", "list_item", "fence", "table_row", "blockquote"]
    level: int | None                   # heading level
    text: str                           # continuation lines joined
    line: int

def parse_blocks(body: str) -> list[Block]: ...     # CommonMark containment
def count_sentences(text: str) -> int: ...
def parse_decisions(body: str) -> list[DecisionEntry]: ...

class DecisionEntry(NamedTuple):
    id: str                             # "D-007"
    number: int
    date: date
    title: str
    body_lines: list[str]
    superseded_by: tuple[str, date, str | None] | None    # id, date, optional scope tail
    line: int
```

## Codes delivered

`structure`: ZK006, ZK009, ZK013, ZK014, ZK015, ZK018, ZK020, ZK021, ZK022,
ZK027–ZK030, ZK037, ZK038, ZK039, ZK040, ZK041, ZK042.
`content`: ZK012, ZK036.

## Behaviour that must be exact

- **Block structure follows CommonMark** (D-038) — the model Obsidian renders. A linter
  disagreeing with the renderer reports errors the user cannot see in the file.
  - **Indented continuation lines belong to the block above.** A wrapped bullet is bullet
    content, not prose.
  - **Fenced blocks are opaque at any nesting depth**, list items included. A
    `#!/usr/bin/env python` line is not an H1; a paragraph of comments is not a paragraph.
  - Everything else inherits its container's kind.
- **`content` is warning-capped by construction** (D-064). No `content` code may be error
  grade — a predicate reading prose is approximate by nature, so the cap binds at the
  layer instead of being re-argued per code.
- **Sentence boundary**: `.`, `!`, `?` followed by whitespace or end of line, with a
  **bounded** abbreviation guard — exactly `e.g. i.e. etc. vs. cf. al.` The guard is data
  and **grows only from observed miscounts**, never speculatively. The counter is
  deliberately crude: it detects multi-sentence runs, not English.
- **Type/location is one comparison, reported once** (D-031), keyed by the **declared**
  type. The message states both facts and **does not guess** which side is wrong.
  `--fix` resolves neither — moving is prohibited, and rewriting `type` picks one of two
  intentions silently.
- **Location is authoritative for applying every other rule.** A note at
  `projects/game-x/log/x.md` declaring `type: topic` is validated as a **log** — fixed
  sections, `updated`/filename equality, all of it — while the mismatch is reported. A
  note cannot escape its location's ruleset by mislabeling itself.
- **ZK020 is bidirectional** (D-026): `updated` **earlier** than the filename date is an
  **error** — no legitimate sequence produces it. **Later** is a **warning** worded as an
  immutability violation naming the remedy: record a new log, do not edit this one.
  `updated` is retained on logs precisely because that equality is the tamper detector.
- **Log sections are three checks, one per failure class** (D-044): ZK009 unknown name
  (error), ZK040 out of order (**warning** — emitter conformance; the primary violator
  will be our own skill, and the note must not be blocked for the tool's drift), ZK041
  duplicate name (error — the one malformation that genuinely breaks name-based parsing).
- **Log section order is conventional** (D-066) — fixedness is normative, the particular
  sequence is not, and there is no rationale behind it to improve toward.
- **ZK021/ZK022 split by direction**: required section missing or empty vs. optional
  section present but empty. Unknown H2 in `project.md` is ZK018, **warning** — the file
  most likely to be hand-edited must not hard-fail over an idiosyncratic heading.
- **ZK013 — contiguity is the decisions file's tamper detector.** The file is
  append-only, so a hand-deletion leaves no other trace anywhere; the gap in the sequence
  is the only surviving evidence. Error grade, **`never` fixable** — the correct response
  is a human accounting for what was removed.
- **ZK015 — `superseded-by` target exists in the same file and differs from its
  carrier.** Error grade legitimately: no mechanical remedy exists **in any direction**,
  so the remediation cap does not bind and exactness alone grades (D-056). Error here
  means *stop and tell a human*, which is correct. Cross-file targets are **not**
  supported — `D-NNN` is unique per file, so a bare cross-file reference is ambiguous by
  construction. Marker grammar: `superseded-by: D-NNN (YYYY-MM-DD)` with an optional
  ` — <scope>` tail for partial supersession.
- **ZK014 — 4-line entry body.** Failure class *record bloat*: `decisions.md` is read
  whole on every recall, so entry length is charged to every future session.
- **ZK039 — only the simple `[[name]]` form is validated**, resolved by **exact slug
  match** against `topics/` slugs and project slugs, nothing else. Alias, heading, and
  block forms are Obsidian's dialect and are tolerated. Warning despite an exact
  predicate, because every remediation is a content decision and the one an automated
  pass would take — creating a stub — is banned. We validate what **we** emit and
  tolerate what the co-tenant emits.
- **ZK042 — every `## Decisions` bullet carries a `D-NNN`.** Warning, emitter
  conformance. `zk-log` sequences the `decisions.md` append **before** log finalization
  (T-11), which turns the obvious false positive into a true positive: it is a skill
  sequencing bug and the check should catch it.
- **ZK037/ZK038** are error grade legitimately — heading level is a character count at
  line start. `###` is permitted: the schema locks section **vocabulary**, not section
  **interiors**.

## Definition of done

- `pytest` green; standing DoD applies.
- Every code above has a positive and a negative case.
- **CommonMark containment asserted directly**: a wrapped bullet is one list item; a
  fence inside a list item is opaque; a fenced `# heading` does not trip ZK037.
- The abbreviation guard asserted on each of the six entries and on `3.5 MB`,
  `src/save/format.py`, `v1.2.3` — the technical cases the whitespace requirement
  already handles.
- The §13 log example's wrapped `## Gotchas` bullet counts as **one item at exactly the
  cap** — it is load-bearing test surface, not incidental formatting (D-063).
- Type/location coherence asserted in **both** directions: misfiled (fails closed) and
  mistyped (fails open). The mistyped case is why the family is error grade.
- ZK013 asserted on a real gap; ZK015 asserted on a dangling target **and** on
  self-supersession, which is the same code and the same class.
- Partial-supersession scope tails parse and do not trip ZK015.
- **AC-3 completes**: prose-heavy body now caught, joining T-06's three.
- `minimal/`, `populated/`, and `examples/` still lint clean.

## Contract deviations

*(record here during execution — none yet)*
