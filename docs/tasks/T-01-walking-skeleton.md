# T-01 — Walking skeleton

**Size:** M · **Depends on:** T-00 · **Status:** done (2026-08-18)
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
- **A committed fixture note reads with no `\r`, opened in binary** (D-071). `zk` cannot
  enforce a checkout it does not perform, so this is the resident guard against a
  stripped `.gitattributes` or a misconfigured clone. Sibling to the meta-test above:
  that one reads our source, this one reads what git actually delivered.
- Runs identically on Windows and POSIX. Paths compared as `PurePosixPath`.

## Contract deviations

One, and it is a test-harness signature only.

- **`vault_factory(ground_vault, use_vault)`, not `(tmp_path, monkeypatch)`.** The
  contract's two arguments are what the fixture *needs*; composing the two fixtures that
  already own those needs avoids a second copy of the ground-state `mkdir`s and a second
  copy of the `setenv` + `reset_cache` pair. Behaviour is unchanged: it still copies
  `fixtures/vaults/<name>/` onto a ground vault in `tmp_path`, sets `ZK_VAULT`, and
  resets the cache.

Nothing else in the contract moved. Every listed signature is implemented verbatim.

## Decisions made in-jurisdiction

Implementation choices with no SPEC section or decision entry behind them. They bind this
code and nothing beyond it; a choice that later needs to bind *contract* gets promoted.

- **An empty or whitespace-only `ZK_VAULT` reads as unset.** Windows deletes a variable
  set to the empty string, so the two states are one situation on that platform.
  Conflating them deliberately is what keeps AC-7 true; the alternative diverges by
  platform for a single user mistake.
- **Absoluteness is checked between `expanduser()` and `resolve()`.** `resolve()` anchors
  a relative path to cwd, which D-018 forbids, so the check cannot come after it. A
  consequence worth naming: a drive-less `/vault` is rejected on Windows and accepted on
  POSIX, because on Windows it resolves against the current drive and is therefore
  cwd-relative. Divergent input, not divergent behaviour.
- **The banner renders `path.as_posix()`.** §1's own example prints a Windows path with
  forward slashes, and a platform-stable banner is one less thing for AC-7 to carry.
- **`is_excluded` relativizes the resolved target against the vault when it lands
  inside, and judges its raw components when it lands outside.** Relativizing is what
  stops a vault that itself lives under some unrelated `archive/` directory from
  excluding its own entire contents. Judging an outside target on raw components
  over-excludes, which is the direction D-053 says to err in.
- **The walker prunes excluded directories rather than filtering after the fact.**
  `archive/` is documented to hold a whole legacy vault; descending into it to discard
  the results would charge every command for content no command may read.
- **Symlink cycles are broken by a visited-resolved-directory set.** Hanging is not one
  of D-019's three outcomes.
- **Notes are emitted into the bundle through `zk_read.render_frontmatter`, not copied
  from the file.** A second reader in `zk_recall.py` would be a second home for
  `utf-8-sig` handling, which D-028 puts in exactly one place. YAML folding is disabled
  because §5 requires `summary` on one line, and flow style is kept for simple
  collections so `tags: [a, b]` stays dense. Values round-trip semantically; only
  quoting and flow style may differ — the latitude D-029 already grants `--fix`.
- **Each note appears under a `#` path heading.** The bundle is not a vault note, so §6's
  H1 ban does not reach it, and a note's own `##` sections need a parent rather than a
  peer. There are **no category headers** — grouping is carried entirely by §8.1's order,
  which is what makes "absent sections omitted entirely" true by construction.
- **Logs sort by filename date descending with a vault-relative path tiebreak**, then cap
  at the architecture.md default of 5. The tiebreak is D-012's pinned sort applied to a
  second artifact; without it two same-day logs could swap between runs.
- **The inventory comment counts decision *entries*, not files** — §8.1's own example
  reads `4 decisions` for a file that holds four. Counted by matching `^## D-\d+`, which
  needs none of the lint machinery arriving at T-06. When nothing survives, the comment
  is `<!-- zk: <slug> -->` with no trailing empty list.
- **The skip notice carries §8.1's wording verbatim and not the parse shape.** Which of
  the three shapes failed goes to stderr: grading a parse failure is lint's jurisdiction
  (D-052), and one skip is one line rather than the wrapped pair §8.1 prints for page
  width.
- **`zk_read.py --list` exits 0 on a zero-slug vault**, printing nothing to stdout and
  D-062's message to stderr. Enumerating zero slugs is a complete answer, so it is not
  D-019's negative result; stdout stays machine-parseable and the human still gets told.
- **§2's and §12's slug messages live in `zk_read.unresolved_error`.** Both scripts and
  both skills branch on `resolve_project`; letting either reimplement its *messages*
  would be the drift D-030 deletes copies to prevent.
- **The D-071 guard is `tests/meta/test_line_endings.py`**, a module D-069's layout
  sketch does not enumerate. What D-069 makes normative is the taxonomy — cross-cutting
  invariants get their own module under `meta/` — and a guard over delivered bytes is
  cross-cutting. It is verified to fire: planting CRLF in the fixture fails it.
- **`tests/conftest.py` puts `scripts/` on `sys.path` and adds a `use_vault` fixture and
  a `write_note` helper.** No packaging, no `__init__.py`; `import zk_config` then works
  identically under pytest and under `python scripts/zk_read.py`, where the interpreter
  supplies the same path itself.
- **`.gitignore` created** with `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, and
  `zk.toml`. The last traces to D-006 and is T-02's DoD line; the rest are this chunk's
  own artefacts, which appear the moment pytest first runs. architecture.md's root layout
  gained the row.

## D-071 confirmed load-bearing, not theoretical

This machine has `core.autocrlf=true` set globally. `.gitattributes` overrides it, so
every tracked file checks out LF — which is D-071 working exactly as argued, on the very
configuration it was written against.

One residue was found and fixed: `LICENSE` was `i/lf w/crlf`. Git's stored copy was
already correct; the *working tree* copy predated `.gitattributes` and had never been
re-checked-out. Refreshed from the index — no content change, and a fresh clone was never
affected. The guard's sweep now covers extensionless committed text, since `LICENSE` is
the file a stale tree holds CRLF in longest.

## Notes for later chunks

- **T-02** inherits `resolve_vault`'s `cwd` parameter, currently accepted and unused —
  it is the input to D-015's fenced search. `VaultConfig.ignore` has no default, so the
  `zk.toml` branch must state it.
- **T-03** inherits `iter_note_paths` unchanged, plus `relative`, `iter_notes`, and
  `render_frontmatter`. `resolve_project` already returns ABSENT for a reserved-name
  slug; ZK044 is the warning that keeps that from being traceless.
- **T-04** closes two seams now listed in plan.md: `--init` (named by the no-vault
  message) and `ground_vault`'s missing `index.md`.
