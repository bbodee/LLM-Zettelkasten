# T-02 — Config completion

**Size:** M · **Depends on:** T-01 · **Status:** todo
**Binds:** SPEC §1, §11 · D-006, D-014, D-015, D-016, D-017, D-018, D-019, D-022, D-062

Closes the `zk.toml` seam T-01 opened. `--init` is **not** here — it calls
`zk_index.py`'s render path, which does not exist until T-04 (D-062).

## Scope

- `zk.toml` discovery, fenced at the repo root.
- `[zk]` table parse: `vault`, `ignore`. Unknown-key and parse-failure handling.
- `zk.toml.example` at the repo root; `zk.toml` in `.gitignore`.
- Exit-code grading swept across every config failure path.

## Interface contract

```python
class TomlConfig(NamedTuple):
    vault: str                          # raw string, pre-normalization
    ignore: tuple[str, ...]
    source: Path                        # the zk.toml that supplied it

def find_repo_root(cwd: Path) -> Path | None: ...       # nearest ancestor where .git exists
def search_paths(cwd: Path) -> list[Path]: ...          # fenced; cwd-first, ordered
def load_toml(path: Path) -> TomlConfig: ...            # raises ZkError(exit_code=2)
def resolve_vault(*, cwd=None, env=None) -> VaultConfig: ...   # gains the step-2 branch
```

`search_paths` is public so the error message can list every directory searched without
re-deriving the fence.

## Behaviour that must be exact

- **Order** (D-014): `ZK_VAULT` first — found there, nothing below runs. Then `zk.toml`.
- **Fence first, then search** (D-015). Repo root = nearest ancestor of cwd, **cwd
  included**, where `.git` **exists** — `.exists()`, never `is_dir()`, because in a
  worktree or submodule `.git` is a file holding a `gitdir:` pointer and `is_dir()` drops
  the fence exactly where it matters. Repo found → search cwd upward through the root
  inclusive, then stop. No repo → search cwd only, no walk.
- **Neither found** → exit 2 listing **every directory searched**, marking where the
  search stopped, naming both mechanisms and `zk_config.py --init` (D-006, §1).
- **Schema** (D-017 as graduated by D-022): `[zk]` table. `vault` absolute; `ignore`
  optional, defaults empty.
- **Unknown key** → exit 2 naming the near-match via `difflib.get_close_matches`:
  `unknown key 'valut' in zk.toml — did you mean 'vault'?` Never ignored.
- **TOML parse failure** → caught and re-emitted per D-016 with the corrected line shown.
  A raw `TOMLDecodeError` reaching the user is a defect. The unescaped-backslash case
  (`"C:\Users\you"`, where `\U` opens a Unicode escape) is the one that must be shown
  corrected, since it is the shape a Windows user types first.
- **All three valid string forms parse identically**: `"C:/Users/you"`,
  `"C:\\Users\\you"`, `'C:\Users\you'`. Rejecting a config that parses and works to
  enforce one style is out.
- **`ignore` semantics, deliberately narrow** (D-022): exact top-level directory names,
  no globs, no paths. It **silences warnings and grants nothing** — an ignored directory
  is still never indexed, linted, or recalled. Listing `private` or `archive` is a hard
  error, not a no-op, so nobody believes it did something.
- **Banner names the file** when `zk.toml` won:
  `zk: vault C:/…/vault  (from C:/work/proj/zk.toml)`.
- **Scripts never prompt.** The script states the remedy; `zk-log` may offer the edit
  conversationally at T-11. A blocking question would hang a batch run.
- `tomllib`, stdlib since 3.11 — no dependency. The 3.11 floor is load-bearing here.

## Exit-code grading (D-019)

Every path classified in this chunk, because "nothing ran" dominates the config layer.

| Condition | Code | Test |
|---|---|---|
| Vault resolved | 0 | did its job, positive |
| No config found anywhere in the fence | 2 | no invocation could work |
| `zk.toml` unparseable | 2 | same |
| Unknown key in `zk.toml` | 2 | same |
| `vault` relative, from either source | 2 | same |
| `ignore` lists `private` or `archive` | 2 | same |
| Resolved path missing or not a directory | 2 | same |

No condition here grades 1. Recorded so the absence reads as decided, not overlooked.

## Fixtures

Config tests build trees in `tmp_path` rather than committing fixture vaults — the
subject is directory shape and file content, not vault content. Cases:

- `.git` as a directory; `.git` as a file with a `gitdir:` pointer (the worktree case).
- No `.git` anywhere above cwd.
- `zk.toml` at the repo root, at cwd, at both, and one directory **above** the root — the
  last must **not** be found. This is the fence's whole reason to exist.
- `ZK_VAULT` and `zk.toml` both set and disagreeing → env wins, banner says so.
- Each malformed-TOML shape, asserted for message content.

## Definition of done

- `pytest` green; standing DoD applies.
- The above-the-fence `zk.toml` is provably not found, and the error lists the searched
  directories including the stop point.
- Every exit-2 message asserted for content, not just code (D-016).
- `zk.toml.example` committed at the repo root, opening with
  `# Copy to zk.toml and edit — this file is never read.`, showing forward slashes and
  a commented `ignore` line.
- `zk.toml` present in `.gitignore` (D-006).
- Windows and POSIX identical — including the drive-letter and UNC path shapes.

## Contract deviations

*(record here during execution — none yet)*
