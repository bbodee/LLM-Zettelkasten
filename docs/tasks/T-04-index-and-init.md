# T-04 — Index + vault init

**Size:** L · **Depends on:** T-02, T-03 · **Status:** todo
**Binds:** SPEC §8, §12 · D-012, D-019, D-020, D-021, D-032, D-034, D-049, D-050, D-051,
D-052, D-061, D-062

`zk_index.py` and `zk_config.py --init` ship together because D-062 makes them one
mechanism: `index.md` has **exactly one author**, and `--init` is a caller, never a second
writer. Splitting them would create the drift the decision exists to prevent.

## Interface contract

`scripts/zk_index.py`

```python
class IndexRender(NamedTuple):
    body: str                           # everything but the generated: line
    notes: int
    skipped: list[tuple[PurePosixPath, str]]   # (path, parse-failure reason)

def render(ignore: Sequence[str] = ()) -> IndexRender: ...
def stamp(render: IndexRender, when: datetime) -> str: ...      # full file text
def differs(existing: str | None, render: IndexRender) -> bool: ...  # ignores generated:
def write_index(*, check: bool = False) -> int: ...             # returns exit code
def size_warning(text: str) -> str | None: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

Vault is ambient (T-01). `init_vault` below keeps its argument — it **creates** a vault
rather than reading one, so there is nothing ambient to read yet.

`render` / `stamp` / `differs` are separate so D-012's ignore-the-timestamp comparison is
one function rather than a carve-out repeated at each call site.

`scripts/zk_config.py`

```python
def init_vault(target: Path) -> None: ...   # create-only; raises ZkError(exit_code=2)
def main(argv) -> int: ...                  # gains --init <path>
```

## Behaviour that must be exact

- **Byte-determinism** (D-012): identical vault content renders byte-identical output.
  Pinned sort — `updated` **descending**, then path **ascending** as a **mandatory**
  tiebreak. Explicit `\n`. Forward slashes on every platform. No dict or walk iteration
  order may leak.
- **Timestamp tracks content, not runs.** Render, compare against disk **ignoring the
  `generated:` line**, write only on difference. A no-op run leaves the file completely
  untouched — same bytes, same mtime, no OneDrive sync churn.
- **`--check`** performs the same comparison, writes nothing, exits 1 on difference. It
  is legitimately overloaded — "index is stale" and "vault has broken notes" are both
  *did its job, answer negative*. **Disambiguate in the message, never by adding a code**
  (D-052): the report names which header fields moved and why.
- **Line format**:
  `- <vault-relative-path>[ (<status>)] — <summary> [<comma-space tags>]`.
  Parenthesized status **only for non-active states** (D-032). Empty tag list → brackets
  **omitted entirely**, never emitted empty (D-021's family).
- **Em dash separator is reasoned** (D-050) — index lines are slug-dense and hyphen-rich,
  and the em dash appears nowhere else in a generated line. The comma-space join and the
  bracket characters are **conventional**; do not "improve" them.
- **No constraints on summary characters.** A summary may contain em dashes or brackets.
  Index lines are a **rendering, not a serialization** — nothing parses them back, and any
  consumer needing structure goes through `zk_read.py`.
- **Group order** Projects → Decisions → Logs → Topics is **arbitrary-but-fixed**
  (D-049). Only fixedness is normative. Empty groups omitted — a header with no entries
  is a stub.
- **Both asymmetries are intended and must be exercised**: an UNCHARTED project's logs
  are indexed, so a project can appear in **Logs but not Projects**; a freshly scaffolded
  project appears in **Projects and nowhere else**.
- **Header fields describe this file** (D-051). `notes:` counts what is **indexed** —
  never indexed-plus-skipped. `skipped:` is the sole reference to anything absent, emitted
  only when nonzero. Totals are derivable and never stated. Both are content-derived, so
  `--check` compares them like any other content.
- **Fail-soft** (D-052): an unparseable note is skipped and reported on stderr; it never
  aborts the rebuild. A stale index is worse than an incomplete one. **This is only
  acceptable because `skipped:` declares it — the two are removable only together.**
- **Index-size check** (D-034) on every invocation **including `--check`**. Warns on
  stderr, **never affects exit status**. 200,000 chars cites E-008; 400,000 cites E-004.
  The warning **names the parked enhancement whose trigger has fired** and points at
  `docs/enhancements.md`.
- **`--init`** (§12, D-061): creates `projects/` and `topics/`, then calls
  `zk_index.py`'s render path for `index.md`. **Nothing else** — no sample project, no
  placeholder notes, and **`private/` and `archive/` are not created**. They are reserved
  names, not territory; a name rule needs no directory. Create-only: **refuses a nonempty
  target**. On success it prints the config next-step, closing D-006's loop from "no vault
  configured" to the command that makes one.

## Definition of done

- `pytest` green; standing DoD applies.
- **AC-4**: `zk_index.py --check` on an unchanged vault exits 0 on the second run and
  every run after. Asserted by running the real script twice, not by unit-testing
  `differs`.
- A no-op run leaves mtime unchanged.
- Determinism asserted by rendering the same vault twice from **shuffled** directory
  listings and comparing bytes.
- Both index asymmetries asserted against `populated/`.
- `skipped:` asserted present-and-correct against `malformed/` (built at T-06; until then
  a two-note inline fixture with one broken note suffices).
- **`--init` output is byte-identical to what the next `zk_index.py` run renders.**
  Asserted directly — this is D-062's construction claim and it must be observed, not
  assumed.
- `--init` refuses a nonempty target with exit 2 and an actionable message.
- The ground-state fixture factory in `conftest.py` now calls the render path, closing
  T-01's seam.
- `tests/test_exclusion.py`'s **index arm** is live: zero excluded paths in `index.md`
  built from `exclusion/`.
- Size warning fires at both thresholds and names the right enhancement, with exit status
  still 0.

## Contract deviations

*(record here during execution — none yet)*
