"""Vault location — resolve it, announce it, expose it as ambient process state.

SPEC §1 (vault location), §11 (exit codes) · D-006, D-014, D-016, D-018, D-019.

T-01 implements the `ZK_VAULT` branch only. `zk.toml` resolution and the `ignore`
list land in T-02; `--init` lands in T-04. Both seams are listed in
docs/plan.md §"Deferral seams".
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NamedTuple, TextIO

ENV_VAR = "ZK_VAULT"


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
    """`"ZK_VAULT"`, or the path to the `zk.toml` that answered (T-02)."""
    ignore: tuple[str, ...]
    """Top-level directory names whose warnings are silenced. Always `()` in T-01."""


_NO_VAULT = f"""zk: no vault configured.
  Set {ENV_VAR} to the absolute path of your vault, or create a zk.toml
  naming one (see zk.toml.example).
  To create a new vault: python scripts/zk_config.py --init <path>"""


def resolve_vault(
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> VaultConfig:
    """Locate the vault. Pure and injectable — tests never mutate process state.

    Raises `ZkError` with exit code 2 when no vault is configured, or when the
    configured value is relative, missing, or not a directory (D-019: no
    argument could make such an invocation work).
    """
    env = os.environ if env is None else env
    cwd = Path.cwd() if cwd is None else cwd

    raw = env.get(ENV_VAR)
    if raw is not None and raw.strip():
        return _normalize(raw, source=ENV_VAR)

    # T-02 inserts the fenced `zk.toml` search here, and `cwd` is its input.
    raise ZkError(_NO_VAULT, exit_code=2)


def _normalize(raw: str, *, source: str) -> VaultConfig:
    """Expand `~`, require absolute, then collapse and follow links (D-018).

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
    return VaultConfig(path=path, source=source, ignore=())


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
    platform, so the line is identical wherever it prints.

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
