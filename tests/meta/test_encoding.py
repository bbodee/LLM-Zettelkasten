"""No bare `open()` anywhere in `scripts/` (SPEC §3, D-018, D-028).

Every call passes `encoding=`; every write mode also passes `newline="\\n"`. This
is a meta-test rather than a convention because the failure it prevents is
silent: on Windows a missing `encoding` falls back to the system ANSI codepage
and mangles non-ASCII content with no exception and no diff.

Read over the AST, not the text, so a call split across lines cannot slip past.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
WRITE_MODE_CHARS = set("wax+")


def script_paths() -> list[Path]:
    return sorted(SCRIPTS.glob("*.py"))


def test_scripts_directory_is_not_empty():
    """A meta-test over zero files passes vacuously — say so out loud."""
    assert script_paths(), f"no scripts found under {SCRIPTS}"


def open_calls(tree: ast.AST):
    """Every `open(...)` and `<something>.open(...)`, with its mode argument.

    Builtin `open` takes the mode at position 1; `Path.open` takes it at
    position 0. Both accept it as `mode=`.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "open":
            yield node, _arg(node, 1)
        elif isinstance(func, ast.Attribute) and func.attr == "open":
            yield node, _arg(node, 0)


def _arg(node: ast.Call, index: int):
    for keyword in node.keywords:
        if keyword.arg == "mode":
            return keyword.value
    return node.args[index] if len(node.args) > index else None


def _kwargs(node: ast.Call) -> set[str]:
    return {keyword.arg for keyword in node.keywords if keyword.arg}


def _is_write(mode) -> bool:
    """Unknown modes count as writes — the conservative direction is the safe one."""
    if mode is None:
        return False
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return bool(WRITE_MODE_CHARS & set(mode.value))
    return True


@pytest.mark.parametrize("path", script_paths(), ids=lambda p: p.name)
def test_every_open_declares_its_encoding(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    offenders = [
        f"{path.name}:{node.lineno}"
        for node, _ in open_calls(tree)
        if "encoding" not in _kwargs(node)
    ]
    assert not offenders, f"open() without encoding=: {offenders}"


@pytest.mark.parametrize("path", script_paths(), ids=lambda p: p.name)
def test_every_write_declares_its_newline(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    offenders = [
        f"{path.name}:{node.lineno}"
        for node, mode in open_calls(tree)
        if _is_write(mode) and "newline" not in _kwargs(node)
    ]
    assert not offenders, f"write mode without newline=: {offenders}"


def test_the_detector_catches_a_planted_violation(tmp_path):
    """A meta-test that cannot fail is a false coverage claim (D-037)."""
    planted = tmp_path / "bad.py"
    planted.write_text(
        "open('a.md')\n"
        "open('b.md', 'w', encoding='utf-8')\n"
        "p.open('w', encoding='utf-8')\n",
        encoding="utf-8",
        newline="\n",
    )
    tree = ast.parse(planted.read_text(encoding="utf-8"))
    calls = list(open_calls(tree))
    assert len([n for n, _ in calls if "encoding" not in _kwargs(n)]) == 1
    assert len([n for n, m in calls if _is_write(m) and "newline" not in _kwargs(n)]) == 2
