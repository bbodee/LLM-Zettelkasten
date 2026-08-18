# T-01 — Walking skeleton

**Size:** M · **Depends on:** T-00 · **Status:** todo
**Binds:** SPEC §1 (partial), §2, §4, §8.1, §9, §11 · D-006, D-013, D-014, D-016, D-018,
D-019, D-020, D-021, D-024, D-028, D-052, D-053, D-062, D-067, D-069

Thinnest end-to-end slice: config resolves, read walks a two-note fixture vault, recall
emits a bundle. Every gap is named in [plan.md](../plan.md) §"Deferral seams" and closed
by a named chunk. Nothing here is a stub — what ships is finished, what is absent is
absent.

## Scope

- `zk_config.py`: `ZK_VAULT` branch only, full normalization, banner, exit-2 posture.
- `zk_read.py`: exclusion predicate, note walking, frontmatter parse, `resolve_project`,
  `known_slugs`, the D-067 CLI.
- `zk_recall.py`: bundle sections 2–5 in order, absent sections omitted, inventory
  comment, skip declaration.
- `tests/` skeleton per D-069, `conftest.py` factories, `minimal/` fixture vault,
  `meta/test_encoding.py`.

**Out:** `zk.toml` (T-02), the behavioral exclusion suite (T-03), index section and
recall flags (T-05), anything lint (T-06+).

## Interface contract

`scripts/zk_config.py`

```python
class ZkError(Exception):
    exit_code: int                      # 1 or 2, graded by D-019's test
    def __init__(self, message: str, *, exit_code: int) -> None: ...

class VaultConfig(NamedTuple):
    path: Path                          # absolute, resolved
    source: str                         # "ZK_VAULT" | str(path to zk.toml)
    ignore: tuple[str, ...]             # always () in T-01

def resolve_vault(*, cwd: Path | None = None,
                  env: Mapping[str, str] | None = None) -> VaultConfig: ...
def current() -> VaultConfig: ...       # memoized per process; announces on first call
def reset_cache() -> None: ...          # tests only
def announce(cfg: VaultConfig, *, stream: TextIO = sys.stderr) -> None: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

`resolve_vault` stays pure and injectable — `cwd` and `env` so tests never mutate process
state. `current()` is the **ambient** accessor every other script reads, memoized because
D-014 requires one banner per process, not one per call.

`scripts/zk_read.py`

```python
class ProjectState(enum.Enum):
    CHARTED = "CHARTED"; UNCHARTED = "UNCHARTED"; ABSENT = "ABSENT"

class Note(NamedTuple):
    path: Path                          # absolute
    rel: PurePosixPath                  # vault-relative, forward slashes
    frontmatter: dict[str, Any]
    body: str                           # everything after the closing ---

class NoteParseError(Exception):
    rel: PurePosixPath
    reason: str                         # "no frontmatter" | "malformed yaml" | "not a mapping"

def vault() -> Path: ...                                  # zk_config.current().path
def is_excluded(rel: PurePosixPath, resolved: Path) -> bool: ...
def iter_note_paths(*, subtree: PurePosixPath | None = None) -> Iterator[Path]: ...
def read_note(path: Path) -> Note: ...                    # raises NoteParseError
def resolve_project(slug: str) -> ProjectState: ...       # D-020, verbatim
def known_slugs() -> list[str]: ...                       # sorted; scans for project.md
def main(argv: Sequence[str] | None = None) -> int: ...   # <slug> | --list
```

**The vault is ambient, not threaded** — resolved once per process by
`zk_config.current()`. D-020 writes `resolve_project(slug)` and the plan audit's P-05
conformed to it; a one-argument resolver beside a two-argument reader would be incoherent,
so the parameter is gone from **every** `zk_read.py` entry point and from the read paths
of `zk_index.py`, `zk_recall.py`, and `zk_lint.py`. `zk_config.init_vault(target)` keeps
its argument — it creates a vault rather than reading one.

Tests point at a fixture by setting `ZK_VAULT` (D-006) and calling
`zk_config.reset_cache()`, which `vault_factory` does.

`scripts/zk_recall.py`

```python
class BundleSection(NamedTuple):
    label: str                          # "charter" | "decisions" | "logs" | "topics"
    count: int
    text: str

def build_bundle(slug: str) -> str: ...                         # flags land in T-05
def main(argv: Sequence[str] | None = None) -> int: ...
```

`tests/conftest.py`

```python
@pytest.fixture
def ground_vault(tmp_path) -> Path: ...                 # mkdir territory + render index.md
@pytest.fixture
def vault_factory(tmp_path, monkeypatch) -> Callable[[str], Path]: ...
    # copies tests/fixtures/vaults/<name>/ onto a ground vault in tmp_path,
    # sets ZK_VAULT, then calls zk_config.reset_cache()
```

`ground_vault` cannot render `index.md` until T-04, so in T-01 it writes the two
directories only and the fixture carries no index. **Named as a seam, closed by T-04** —
the factory gains the render call there and no test asserts on `index.md` before then.

## Behaviour that must be exact

- **Resolution.** `ZK_VAULT` unset → exit 2, message naming `ZK_VAULT`, `zk.toml`, and
  `zk_config.py --init` (§1, D-006). Value relative → exit 2, never anchored to cwd.
  Normalize with `expanduser()` then `resolve()`; no `expandvars()` (D-018, E-013).
  Resolved path missing or not a directory → exit 2.
- **Banner** on stderr, one line, every script, before any other output (D-014):
  `zk: vault <path>  (from ZK_VAULT)`. Never stdout — the bundle lives there.
- **Exclusion** (§9, D-053): `private` or `archive` as **any component** of the
  vault-relative path, **casefolded**, tested on the walked path **and** the resolved
  target — either match excludes. Ties are not split; ambiguous is private.
- **Encoding**: `zk_read.py` opens `utf-8-sig`. It is the only place BOM handling exists.
- **Three states** (§2, D-020): CHARTED = `projects/<slug>/project.md` exists;
  UNCHARTED = directory without it; ABSENT = no directory. Both failures exit 1.
  Messages differ — UNCHARTED names the missing file, ABSENT lists known slugs.
- **Bundle order** (§8.1): `project.md` → `decisions.md` → logs → tag-matched topics.
  Absent sections omitted **entirely** — no empty headers, no absence narration (D-021).
- **Inventory comment**, first line of stdout, naming only what is present:
  `<!-- zk: game-x | charter, 1 log -->`. On any skip it is **mandatory** and names the
  skipped file plus the lint remedy (D-052). Bundle self-description is permitted; vault
  diagnostics are not (D-024).
- **Fail-soft**: an unparseable note is skipped and declared, never fatal.
- CLI per D-067: `zk_read.py <slug>` prints note paths and frontmatter to stdout;
  `--list` prints known slugs.

## Fixtures

`tests/fixtures/vaults/minimal/` — **frozen at two notes**, forever:

```
projects/game-x/project.md              # charter, all three required H2s filled
projects/game-x/log/2026-08-14-save-system.md
```

Both lint-clean by inspection now, by test at T-06. Growth belongs in `populated/`
(T-03) — extending `minimal/` rots this chunk's count assertions.

## Definition of done

- `pytest` green. Standing DoD in [plan.md](../plan.md) applies in full.
- `python scripts/zk_recall.py game-x` against `minimal/` prints a bundle whose first
  line is the inventory comment and which contains the charter and the log, in order,
  with no `decisions.md` or topics header of any kind.
- `resolve_project` returns all three states against purpose-built directories.
- Exit codes: 0 on the bundle, 1 on ABSENT and UNCHARTED, 2 on unset/relative/missing
  `ZK_VAULT`. Each nonzero exit asserted for **message content**, not just the code.
- Exclusion is unit-tested against every row of §9's table as string input. The
  behavioral fixture suite is T-03's — this chunk asserts the predicate, not the system.
  **D-053's one-suite clause binds the behavioral suite**, which stays whole in T-03; a
  chunk testing the function it writes is ordinary layering, not a staged rollout
  (scope ruled 2026-08-18, recorded in [plan.md](../plan.md)).
- `meta/test_encoding.py` green: no `open(` without `encoding=`, no write mode without
  `newline=`, anywhere in `scripts/`.
- Runs identically on Windows and POSIX. Paths compared as `PurePosixPath`.

## Contract deviations

*(record here during execution — none yet)*
