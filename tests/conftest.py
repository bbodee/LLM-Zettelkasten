"""Vault factories. Every test points `ZK_VAULT` at a copy under `tmp_path` (D-006).

Fixture vaults are named directories under `fixtures/vaults/`, each an extension
of D-062's ground state (D-069). The ground state itself is built here rather
than committed: git tracks no empty directory, and a `.gitkeep` inside
`projects/` would be a stray file in the one fixture that must be pristine.
"""

from __future__ import annotations

import shutil
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
FIXTURE_VAULTS = Path(__file__).resolve().parent / "fixtures" / "vaults"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import zk_config  # noqa: E402  — importable only once `scripts/` is on the path


@pytest.fixture(autouse=True)
def _clean_vault_cache():
    """No process-memoized vault may leak between tests (D-014's `current()`)."""
    zk_config.reset_cache()
    yield
    zk_config.reset_cache()


@pytest.fixture
def ground_vault(tmp_path) -> Path:
    """D-062's ground state: territory present and empty, no reserved-name dirs.

    `index.md` is **absent** here, not empty — `zk_index.py`'s render path is its
    sole author (D-062) and does not exist until T-04, and writing a second
    implementation now is exactly the drift that decision forbids. Seam listed in
    docs/plan.md; no T-01 test asserts on `index.md`.
    """
    root = tmp_path / "vault"
    (root / "projects").mkdir(parents=True)
    (root / "topics").mkdir()
    return root


@pytest.fixture
def use_vault(monkeypatch) -> Callable[[Path], Path]:
    """Point `ZK_VAULT` at a vault and drop the memoized resolution."""

    def _point(root: Path) -> Path:
        monkeypatch.setenv("ZK_VAULT", str(root))
        zk_config.reset_cache()
        return root

    return _point


@pytest.fixture
def vault_factory(ground_vault, use_vault) -> Callable[[str], Path]:
    """Copy `fixtures/vaults/<name>/` onto a ground vault, then select it."""

    def _make(name: str) -> Path:
        source = FIXTURE_VAULTS / name
        if not source.is_dir():
            raise AssertionError(f"no fixture vault named {name!r} at {source}")
        shutil.copytree(source, ground_vault, dirs_exist_ok=True)
        return use_vault(ground_vault)

    return _make


def write_note(root: Path, rel: str, text: str) -> Path:
    """Add one note to a vault under construction. LF only, per D-018 and D-071."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path
