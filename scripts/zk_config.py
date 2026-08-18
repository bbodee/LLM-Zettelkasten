"""Vault location — resolve it, announce it, expose it as ambient process state.

SPEC §1 (vault location), §11 (exit codes) · D-006, D-014, D-015, D-016,
D-017 as graduated by D-022, D-018, D-019.

`--init` lands in T-04: it calls `zk_index.py`'s render path rather than writing
`index.md` itself (D-062), and that path does not exist yet. The seam is listed in
docs/plan.md §"Deferral seams"; the no-vault message names the flag deliberately.
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NamedTuple, TextIO

ENV_VAR = "ZK_VAULT"
TOML_NAME = "zk.toml"
EXAMPLE_NAME = "zk.toml.example"
TABLE = "zk"
KEYS = ("ignore", "vault")
RESERVED_DIRS = ("archive", "private")

_VALID_ESCAPES = frozenset('btnfr"\\uU')
_IGNORE_REJECTS = frozenset("/\\*?[]")


class ZkError(Exception):
    """A failure whose message is already actionable (D-016) and graded (D-019).

    `message` is the complete user-facing text, `zk: ` prefix and indented
    continuation lines included, so the templates in this repo read the way SPEC
    prints them. `exit_code` is 1 (did the job, negative result) or 2 (could not
    do the job at all).
    """

    def __init__(self, message: str, *, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class VaultConfig(NamedTuple):
    path: Path
    """Absolute and resolved — symlinks and junctions followed (D-018)."""
    source: str
    """`"ZK_VAULT"`, or the posix path of the `zk.toml` that answered (D-014)."""
    ignore: tuple[str, ...]
    """Top-level directory names whose schema warning is silenced (D-022).

    Empty whenever `ZK_VAULT` answered: D-014 stops the cascade at the first hit,
    so no `zk.toml` was read and there is no list to carry.
    """


class TomlConfig(NamedTuple):
    vault: str
    """Raw string, pre-normalization — `_normalize` is D-018's single home."""
    ignore: tuple[str, ...]
    source: Path
    """The `zk.toml` that supplied it. D-014's banner names this file."""


# --- the fence (D-015) ----------------------------------------------------------


def find_repo_root(cwd: Path) -> Path | None:
    """Nearest ancestor of `cwd`, cwd included, where `.git` **exists**.

    `.exists()`, never `is_dir()`: in a git worktree or submodule `.git` is a
    *file* holding a `gitdir:` pointer, and `is_dir()` would silently drop the
    fence in exactly the isolated-agent context where it matters most (D-015).
    """
    start = Path(cwd).resolve()
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return directory
    return None


def search_paths(cwd: Path) -> list[Path]:
    """Directories to look for `zk.toml` in, cwd first, in order.

    Fence first, then search (D-015). Repo found → cwd upward through the root,
    inclusive, then stop. No repo → cwd only, no walk.

    Public so the no-vault message can list every directory searched without
    re-deriving the fence — a second derivation is a second chance to disagree.
    """
    start = Path(cwd).resolve()
    root = find_repo_root(start)
    chain = [start, *start.parents]
    if root is None:
        return chain[:1]
    return chain[: chain.index(root) + 1]


# --- `zk.toml` (D-017 as graduated by D-022) ------------------------------------


def load_toml(path: Path) -> TomlConfig:
    """Parse and validate one `zk.toml`. Raises `ZkError(exit_code=2)`.

    Whole-file validation before any value is used: a file with two faults names
    the first one and stops, rather than half-applying and reporting the other.
    """
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ZkError(
            f"zk: cannot read {TOML_NAME}: {path.as_posix()}\n"
            f"  The file is not valid UTF-8 ({exc.reason} at byte {exc.start}).\n"
            f"  TOML is UTF-8 by definition. Re-save the file as UTF-8, or set\n"
            f"  {ENV_VAR} instead.",
            exit_code=2,
        ) from exc
    except OSError as exc:
        raise ZkError(
            f"zk: cannot read {TOML_NAME}: {path.as_posix()}\n"
            f"  {exc.strerror or exc}\n"
            f"  Fix the file's permissions, or set {ENV_VAR} instead.",
            exit_code=2,
        ) from exc

    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ZkError(_parse_failure(path, text, exc), exit_code=2) from exc

    table = _table(path, data)
    unknown = [key for key in table if key not in KEYS]
    if unknown:
        raise ZkError(_unknown_key(path, unknown[0], KEYS), exit_code=2)

    return TomlConfig(
        vault=_vault_value(path, table),
        ignore=_ignore_value(path, table),
        source=path,
    )


def _table(path: Path, data: dict) -> dict:
    """The `[zk]` table, or a directed error. D-022 converted the file to a table."""
    stray = [key for key in data if key != TABLE]
    if TABLE in data:
        if stray:
            raise ZkError(_unknown_key(path, stray[0], (TABLE,)), exit_code=2)
        table = data[TABLE]
        if not isinstance(table, dict):
            raise ZkError(
                f"zk: [{TABLE}] in {TOML_NAME} is not a table.\n"
                f"  In {path.as_posix()}\n"
                f"  Write it as a section header on its own line: [{TABLE}]\n"
                f"  See {EXAMPLE_NAME}.",
                exit_code=2,
            )
        return table

    bare = [key for key in data if key in KEYS]
    if bare:
        listed = ", ".join(sorted(bare))
        raise ZkError(
            f"zk: {TOML_NAME} has no [{TABLE}] table.\n"
            f"  In {path.as_posix()}\n"
            f"  Found {listed} at the top level. Settings moved under a [{TABLE}]\n"
            f"  header. Add this line above them:\n"
            f"    [{TABLE}]\n"
            f"  See {EXAMPLE_NAME}.",
            exit_code=2,
        )
    if stray:
        raise ZkError(_unknown_key(path, stray[0], (TABLE,)), exit_code=2)
    raise ZkError(
        f"zk: {TOML_NAME} names no vault.\n"
        f"  In {path.as_posix()}\n"
        f"  The file parses but is empty of settings. It needs:\n"
        f"    [{TABLE}]\n"
        f'    vault = "C:/Users/you/OneDrive/vault"\n'
        f"  See {EXAMPLE_NAME}.",
        exit_code=2,
    )


def _unknown_key(path: Path, key: str, valid: Sequence[str]) -> str:
    """Never silently ignored: a typo would otherwise fall through to "no vault
    configured," sending the user hunting for a file sitting right there (D-017)."""
    close = difflib.get_close_matches(key, valid, n=1)
    hint = f" — did you mean {close[0]!r}?" if close else ""
    known = ", ".join(sorted(valid))
    return (
        f"zk: unknown key {key!r} in {TOML_NAME}{hint}\n"
        f"  In {path.as_posix()}\n"
        f"  Known: {known}\n"
        f"  See {EXAMPLE_NAME}."
    )


def _vault_value(path: Path, table: dict) -> str:
    if "vault" not in table:
        raise ZkError(
            f"zk: {TOML_NAME} has a [{TABLE}] table but no vault key.\n"
            f"  In {path.as_posix()}\n"
            f"  Add: vault = \"C:/Users/you/OneDrive/vault\"\n"
            f"  See {EXAMPLE_NAME}.",
            exit_code=2,
        )
    value = table["vault"]
    if not isinstance(value, str) or not value.strip():
        raise ZkError(
            f"zk: vault in {TOML_NAME} is not a path string: {value!r}\n"
            f"  In {path.as_posix()}\n"
            f'  Write it quoted: vault = "C:/Users/you/OneDrive/vault"\n'
            f"  See {EXAMPLE_NAME}.",
            exit_code=2,
        )
    return value


def _ignore_value(path: Path, table: dict) -> tuple[str, ...]:
    """Exact top-level directory names, nothing else (D-022).

    Deliberately narrow, and validated rather than tolerated: an entry that
    cannot match — `attachments/`, `*.tmp` — would silence nothing while looking
    like it did, which is the silence D-022 exists to end.
    """
    raw = table.get("ignore", [])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ZkError(
            f"zk: ignore in {TOML_NAME} is not a list of strings: {raw!r}\n"
            f"  In {path.as_posix()}\n"
            f'  Write it as: ignore = [".obsidian", "attachments"]\n'
            f"  See {EXAMPLE_NAME}.",
            exit_code=2,
        )

    names: list[str] = []
    for entry in raw:
        clean = entry.strip().strip("/\\")
        # Reserved first, and against the cleaned form: `"private/"` is one
        # mistake, not two, and must not be answered with "did you mean
        # 'private'?" — that suggestion is itself a hard error.
        if clean.casefold() in RESERVED_DIRS:
            raise ZkError(
                f"zk: ignore in {TOML_NAME} lists {entry!r}, which is not permitted.\n"
                f"  In {path.as_posix()}\n"
                f"  private/ and archive/ are already excluded from every read,\n"
                f"  index, and bundle. Ignoring them would grant nothing while\n"
                f"  reading as though it granted something.\n"
                f"  Remove the entry.",
                exit_code=2,
            )
        if (
            clean != entry
            or not clean
            or _IGNORE_REJECTS & set(clean)
            or clean in (".", "..")
        ):
            raise ZkError(_bad_ignore_entry(path, entry, clean), exit_code=2)
        if clean not in names:
            names.append(clean)
    return tuple(names)


def _bad_ignore_entry(path: Path, entry: str, clean: str) -> str:
    usable = clean and not (_IGNORE_REJECTS & set(clean)) and clean not in (".", "..")
    hint = f" — did you mean {clean!r}?" if usable else ""
    return (
        f"zk: invalid ignore entry {entry!r} in {TOML_NAME}{hint}\n"
        f"  In {path.as_posix()}\n"
        f"  ignore takes exact top-level directory names: no globs, no paths,\n"
        f"  no slashes, no surrounding whitespace.\n"
        f"  See {EXAMPLE_NAME}."
    )


def _parse_failure(path: Path, text: str, exc: tomllib.TOMLDecodeError) -> str:
    """Re-emit a `TOMLDecodeError` with the fix attached (D-016, §1).

    A raw `Invalid \\escape (at line 2, column 12)` is loud and useless, and the
    config step is where a new user has the least context to debug it. The
    unescaped-backslash case gets its corrected line shown, because it is the
    shape a Windows user types first.
    """
    header = f"zk: cannot parse {TOML_NAME}: {path.as_posix()}\n  {exc}"

    escape = _unescaped_backslash(text)
    if escape is not None:
        number, line, key, body = escape
        slashed = body.replace("\\", "/")
        doubled = body.replace("\\", "\\\\")
        forms = "\n".join(
            f"    {form}"
            for form in (
                f'{key} = "{slashed}"',
                f'{key} = "{doubled}"',
                f"{key} = '{body}'",
            )
        )
        return (
            f"{header}\n"
            f"  Line {number}: {line.strip()}\n"
            f"  A backslash opens an escape sequence inside a \"quoted\" TOML\n"
            f"  string, so a Windows path must be written one of these ways —\n"
            f"  all three mean the same directory:\n"
            f"{forms}\n"
            f"  Or set {ENV_VAR} instead and delete {TOML_NAME}."
        )

    number = _error_line(exc)
    lines = text.splitlines()
    shown = ""
    if number is not None and 1 <= number <= len(lines):
        shown = f"\n  Line {number}: {lines[number - 1].strip()}"
    return (
        f"{header}{shown}\n"
        f"  Compare the file against {EXAMPLE_NAME}, or set {ENV_VAR} instead."
    )


def _error_line(exc: tomllib.TOMLDecodeError) -> int | None:
    """`lineno` is an attribute from 3.14 and message text before it."""
    lineno = getattr(exc, "lineno", None)
    if isinstance(lineno, int):
        return lineno
    found = re.search(r"at line (\d+)", str(exc))
    return int(found.group(1)) if found else None


def _unescaped_backslash(text: str) -> tuple[int, str, str, str] | None:
    """First `key = "…"` line whose body holds a backslash that opens nothing.

    Scanned independently of the exception rather than from its position: the
    exception reports where the parser gave up, which is the escape itself, and
    we want the whole assignment so the correction can be shown in full.
    """
    for number, line in enumerate(text.splitlines(), start=1):
        match = re.match(r'\s*([A-Za-z0-9_.-]+)\s*=\s*"(.*)"\s*$', line)
        if match is not None and _has_bad_escape(match.group(2)):
            return number, line, match.group(1), match.group(2)
    return None


def _has_bad_escape(body: str) -> bool:
    index = 0
    while index < len(body):
        if body[index] != "\\":
            index += 1
            continue
        if index + 1 >= len(body) or body[index + 1] not in _VALID_ESCAPES:
            return True
        index += 2  # a valid pair consumes both characters, so `\\U` is fine
    return False


# --- resolution -----------------------------------------------------------------


def resolve_vault(
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> VaultConfig:
    """Locate the vault. Pure and injectable — tests never mutate process state.

    D-014's order, first hit wins: `ZK_VAULT`, then `zk.toml` within D-015's
    fence. Found in the env, nothing below runs — including the `ignore` list,
    which therefore stays empty on that branch.

    A `zk.toml` that is found but faulty is fatal, never skipped: continuing the
    walk past a broken config is how a typo becomes "no vault configured."

    Raises `ZkError` with exit code 2 throughout — every failure in this layer
    would fail identically for every possible invocation (D-019's tiebreak).
    """
    env = os.environ if env is None else env
    cwd = Path.cwd() if cwd is None else cwd

    raw = env.get(ENV_VAR)
    if raw is not None and raw.strip():
        return _normalize(raw, source=ENV_VAR)

    searched = search_paths(cwd)
    for directory in searched:
        candidate = directory / TOML_NAME
        if candidate.is_file():
            cfg = load_toml(candidate)
            return _normalize(
                cfg.vault, source=cfg.source.as_posix(), ignore=cfg.ignore
            )

    raise ZkError(
        _no_vault(searched, repo_root=find_repo_root(cwd)),
        exit_code=2,
    )


def _no_vault(searched: Sequence[Path], *, repo_root: Path | None) -> str:
    """List every directory searched and mark where the search stopped (D-015).

    The stop point is the load-bearing half: without it the message reads as
    "your config is nowhere," when the truth is "your config is above the fence,"
    and those have different fixes.
    """
    lines = [
        "zk: no vault configured.",
        f"  Set {ENV_VAR} to the absolute path of your vault, or create a {TOML_NAME}",
        f"  naming one (see {EXAMPLE_NAME}).",
        f"  Searched for {TOML_NAME} in:",
    ]
    for directory in searched:
        marker = "  <- repo root; the search stops here" if directory == repo_root else ""
        lines.append(f"    {directory.as_posix()}{marker}")
    if repo_root is None:
        lines.append("    (no .git here or above, so the search did not walk up)")
    lines.append("  To create a new vault: python scripts/zk_config.py --init <path>")
    return "\n".join(lines)


def _normalize(
    raw: str, *, source: str, ignore: tuple[str, ...] = ()
) -> VaultConfig:
    """Expand `~`, require absolute, then collapse and follow links (D-018).

    Identical for both sources — that is the whole point of D-018, and the reason
    `zk.toml`'s relative-path rejection needs no separate implementation.

    Order matters: `resolve()` anchors a relative path to cwd, which D-018
    forbids, so absoluteness is checked before resolving. On Windows a
    drive-less path like `/vault` is *not* absolute — it resolves against the
    current drive, which is part of cwd — so it is rejected there and accepted
    on POSIX. Divergent input, not divergent behaviour.
    """
    value = raw.strip()
    try:
        candidate = Path(value).expanduser()
    except RuntimeError as exc:  # no home directory to expand `~` against
        raise ZkError(
            f"zk: cannot expand '~' in the vault path from {source}: {value!r}\n"
            f"  {exc}\n"
            f"  Set {ENV_VAR} to a fully qualified path instead.",
            exit_code=2,
        ) from exc

    if not candidate.is_absolute():
        raise ZkError(
            f"zk: vault path from {source} is not absolute: {value!r}\n"
            "  Relative paths are never anchored to the current directory.\n"
            "  Give a fully qualified path, e.g. C:/Users/you/OneDrive/vault "
            "or /home/you/vault.",
            exit_code=2,
        )

    path = candidate.resolve()
    if not path.exists():
        raise ZkError(
            f"zk: vault path does not exist: {path.as_posix()}\n"
            f"  Configured by {source}.\n"
            "  Create it with: python scripts/zk_config.py --init "
            f"{path.as_posix()}",
            exit_code=2,
        )
    if not path.is_dir():
        raise ZkError(
            f"zk: vault path is not a directory: {path.as_posix()}\n"
            f"  Configured by {source}.\n"
            "  Point it at the vault root, not at a file inside it.",
            exit_code=2,
        )
    return VaultConfig(path=path, source=source, ignore=ignore)


_cache: VaultConfig | None = None


def current() -> VaultConfig:
    """The ambient vault — resolved once per process, announced on first call.

    Memoized because D-014 requires one banner per process, not one per call.
    That the banner cannot repeat is therefore structural, not a discipline
    obligation on each script (docs/plan.md, P-05's side effect).
    """
    global _cache
    if _cache is None:
        cfg = resolve_vault()
        announce(cfg)
        _cache = cfg
    return _cache


def reset_cache() -> None:
    """Drop the memoized vault. Tests only — see `tests/conftest.py`."""
    global _cache
    _cache = None


def announce(cfg: VaultConfig, *, stream: TextIO | None = None) -> None:
    """One line to stderr naming the vault and what chose it (D-014, §1).

    Stderr, never stdout: `zk_recall.py` emits its bundle on stdout and a banner
    there would land inside the context bundle. Forward slashes on every
    platform, so the line is identical wherever it prints — and when `zk.toml`
    won, the source *is* the file, so the banner says which one.

    `sys.stderr` is read at call time, not bound as a default — a default would
    capture whatever stream existed at import and write past any later
    redirection.
    """
    out = sys.stderr if stream is None else stream
    print(f"zk: vault {cfg.path.as_posix()}  (from {cfg.source})", file=out)


def report(exc: ZkError, *, stream: TextIO | None = None) -> int:
    """Print an already-actionable message and hand back its exit grade."""
    print(exc, file=sys.stderr if stream is None else stream)
    return exc.exit_code


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="zk_config.py",
        description="Print the resolved vault path. Fails loudly when none is configured.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    _parser().parse_args(argv)
    try:
        cfg = current()
    except ZkError as exc:
        return report(exc)
    print(cfg.path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
