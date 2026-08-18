# T-03 — Read hardening + exclusion suite

**Size:** L · **Depends on:** T-01 · **Status:** todo
**Binds:** SPEC §2, §4, §9 · D-016, D-022, D-024, D-028, D-029, D-052, D-053, D-058

The privacy chunk. This is the only rule in the system whose failure costs privacy rather
than retrieval quality, so it gets the strongest enforcement the repo has: a behavioral
fixture vault plus a grep companion (D-053).

## Scope

- The exclusion suite, built from §9's adversarial table — every row, symlinks included.
- ZK044 emitted **by the chokepoint itself**.
- Frontmatter parse hardening: three failure shapes, unknown-key preservation contract.
- Stray-file and unrecognized-directory classification, surfaced as data for T-06.
- The grep companion enforcing the sole-walker rule.
- `populated/` fixture vault.

## Interface contract

```python
class Stray(NamedTuple):
    rel: PurePosixPath
    kind: Literal["file", "directory"]
    near_miss: str | None               # schema name it near-matches, or None

def iter_note_paths(*, subtree=None) -> Iterator[Path]: ...     # unchanged from T-01
def iter_strays(ignore: Sequence[str] = ()) -> Iterator[Stray]: ...
def shadowed_slugs() -> list[PurePosixPath]: ...                # ZK044 population
def read_note(path) -> Note: ...                                # NoteParseError.reason exact
```

Vault is ambient per T-01 (`zk_config.current()`), not a parameter.

`iter_strays` is the sole producer of the ZK019/ZK025/ZK026/ZK045 population. Lint
consumes it at T-06 and never walks the vault itself — that is the whole point of the
chokepoint.

## Behaviour that must be exact

- **Governing asymmetry** (D-053): exclusion errs toward excluding; an ambiguous path is
  private. Over-excluding costs a note the user must move. Under-excluding puts private
  content into a context window and sends it to Anthropic. Ties are not split.
- **Matching**: `private` or `archive` as **any component** of the **vault-relative**
  path, **casefolded**, unconditionally, regardless of flags including `--deep`.
  Casefolding cannot depend on D-025's lint rule having passed — the chokepoint decides
  what to read before lint ever runs.
- **Symlinks**: exclude on the walked path **or** its resolved target. Walked-path-only
  misses a link *into* `private/`; target-only misses a link *from* it.
- **Component, not substring**: `projects/private-api/` is not private.
- **ZK044** is emitted by `zk_read.py`, not by a lint pass, because nothing downstream can
  see an excluded path (§9, traceless-failure principle). `projects/private/` is
  distinguishable from `projects/game-x/private/` by position — one is a project slug,
  the other a subdirectory.
- **Parse failure has three shapes** and `NoteParseError.reason` distinguishes them —
  no frontmatter, malformed YAML, valid YAML of the wrong shape. `zk_read.py` reports
  the shape; **`zk_lint.py` owns severity discrimination** (D-052 jurisdiction split).
  No exempt category: a stray `.md` with no frontmatter is counted like anything else.
- **Unknown frontmatter keys are cargo** (D-029): preserved, allowed, **inert**. No
  script may read, interpret, index, join on, sort by, or branch on one. Enforced here
  by never exposing them through a lookup path — `Note.frontmatter` carries them and
  nothing in `scripts/` reads a key not in the §4 table.
- **Unrecognized top-level directories** are classified, never silently dropped, in two
  flavours — plain and near-miss via `difflib.get_close_matches`. `ignore` from T-02
  suppresses the *warning* and grants nothing.
- **Stray files get no ignore list** (D-058). Directories persist and need suppression;
  a stray file always has a terminating remedy, so a file ignore list is config for an
  empty room — and it would reintroduce the config-driven invisibility that location-only
  exclusion exists to replace.

## Fixtures

`tests/fixtures/vaults/exclusion/` — every row of §9's table, plus:

| Path | Expected |
|---|---|
| `private/budgeting-y/accounts.md` | excluded |
| `archive/old-vault/notes.md` | excluded |
| `projects/game-x/private/secrets.md` | excluded — any-component |
| `projects/private/notes.md` | excluded; ZK044 warning |
| `Private/cased.md` | excluded — casefolded |
| `projects/private-api/project.md` | **not** excluded — component, not substring |
| symlink → `private/…` | excluded on target |
| symlink inside `private/` → outward | excluded on walked path |

Symlink rows are skipped with an explicit `pytest.skip` reason where the platform or the
CI user cannot create them — **skipped visibly, never silently dropped**, since a
silently-absent privacy test is the same failure class the suite exists to catch.

`tests/fixtures/vaults/populated/` — the happy path everything downstream reads:
charter, `decisions.md` with four entries including one partial `superseded-by:`, three
logs across two dates, two topics with intersecting and non-intersecting tags, and one
**UNCHARTED** directory carrying a log. The UNCHARTED directory is deliberate: D-020's
orphan-logs rule and D-049's two index asymmetries have no other test surface.

## Definition of done

- `pytest` green; standing DoD applies.
- `tests/test_exclusion.py` exists and asserts **zero excluded paths** in any read. Its
  index and bundle arms are stubbed with an explicit `xfail`/marker naming T-04 and
  T-05 — the suite is one module and one fixture vault, filled across three chunks, so
  D-053's "one rule, one function, one fixture suite" holds.
- `meta/test_sole_walker.py` green: no `os.walk`, `iterdir`, `glob`, `rglob`, `scandir`,
  or `listdir` anywhere in `scripts/` outside `zk_read.py`. Asserted over source text,
  not by import — a bypass added later must fail this test without anyone remembering it
  exists.
- ZK044 is emitted from the chokepoint and observable without a lint run.
- Windows and POSIX identical, including case-insensitive-filesystem behaviour on the
  `Private/` row.

*Unknown-key round-trip removed 2026-08-18 (audit row P-17, conformed to the graph).*
D-029 places that guarantee in **`--fix`'s** test contract, and §10 states it there. It
lives in T-08 only. No coverage is lost: T-08's fixture necessarily round-trips through
`read_note`, so a reader that dropped an unknown key would fail there. The **inert**
clause above is T-03's business and stays — preservation and inertness are different
obligations from the same decision.

## Contract deviations

*(record here during execution — none yet)*
