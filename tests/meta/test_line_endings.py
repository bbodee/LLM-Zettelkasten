"""Committed text arrives with LF, in binary (D-071).

`.gitattributes` pins `* text eol=lf`, but `zk` cannot enforce a checkout it does
not perform. This is the **resident** guard: it catches a stripped
`.gitattributes` or a clone configured with `core.autocrlf=true`, either of which
silently falsifies three ratified byte-level claims (D-012's index determinism,
D-018/D-028's newline discipline, D-069's SPEC-to-fixture byte equality).

Sibling to `test_encoding.py`: that one reads our source, this one reads what git
actually delivered. Opened in binary, because every text-mode reader in Python
translates the very bytes under test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_VAULTS = REPO_ROOT / "tests" / "fixtures" / "vaults"
TRACKED_SUFFIXES = {".md", ".py", ".toml", ".example"}
TRACKED_NAMES = {"LICENSE", ".gitattributes", ".gitignore"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}


def committed_text_files() -> list[Path]:
    """Extensionless committed text counts too — `LICENSE` predates `.gitattributes`
    and is exactly the file a stale working tree keeps CRLF in longest."""
    return sorted(
        path
        for path in REPO_ROOT.rglob("*")
        if path.is_file()
        and (path.suffix in TRACKED_SUFFIXES or path.name in TRACKED_NAMES)
        and not SKIP_DIRS & set(path.relative_to(REPO_ROOT).parts)
    )


def fixture_notes() -> list[Path]:
    return sorted(FIXTURE_VAULTS.rglob("*.md"))


def test_fixture_vaults_carry_notes():
    """Without this, the guard below passes over an empty list and proves nothing."""
    assert fixture_notes(), f"no fixture notes under {FIXTURE_VAULTS}"


@pytest.mark.parametrize(
    "path", fixture_notes(), ids=lambda p: p.relative_to(FIXTURE_VAULTS).as_posix()
)
def test_a_committed_fixture_note_has_no_carriage_return(path: Path):
    assert b"\r" not in path.read_bytes()


def test_no_committed_text_file_carries_a_carriage_return():
    offenders = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in committed_text_files()
        if b"\r" in path.read_bytes()
    ]
    assert not offenders, (
        "CRLF in the working tree — check .gitattributes and core.autocrlf: "
        f"{offenders}"
    )
