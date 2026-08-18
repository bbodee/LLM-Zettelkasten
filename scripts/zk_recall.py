"""Assemble one project's context bundle on stdout.

SPEC §8.1 (bundle composition), §9 (exclusion), §11, §12 · D-010, D-019, D-020,
D-021, D-024, D-052, D-062.

T-01 emits sections 2-5. Section 1, the computed index section, needs an
`index.md` that does not exist until T-04, and `--logs` / `--deep` / `--topics`
land in T-05. Both seams are listed in docs/plan.md §"Deferral seams".
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import PurePosixPath
from typing import NamedTuple, TextIO

import zk_config
import zk_read
from zk_config import ZkError
from zk_read import Note, NoteParseError, ProjectState

DEFAULT_LOGS = 5
"""Logs included when nothing overrides it. `--logs N` and `--deep` land in T-05."""

DECISIONS = "decisions.md"

_SINGULAR = {"decisions": "decision", "logs": "log", "topics": "topic"}
_ENTRY = re.compile(r"^## D-\d+\b")


class BundleSection(NamedTuple):
    label: str
    """`"charter"` | `"decisions"` | `"logs"` | `"topics"`."""
    count: int
    """Charters count files; decisions count **entries**, per §8.1's example."""
    text: str
    """The rendered markdown, or `""` when the section is absent."""


class _Gathered(NamedTuple):
    sections: list[BundleSection]
    skipped: list[NoteParseError]


# --- rendering ------------------------------------------------------------------


def _render_note(note: Note) -> str:
    """One note under a path heading: frontmatter block, then body.

    Frontmatter is included because the bundle is retrieval surface — `summary`,
    `tags`, `updated`, and `status` all belong there, and §4 requires a
    non-active status to stay *visible* rather than be filtered away.

    It is re-emitted through `zk_read.render_frontmatter` rather than copied from
    the file, so `utf-8-sig` decoding stays in exactly one place (D-028): a
    second reader here would be a second home for BOM handling.

    `#` rather than `##` because a note's own sections are `##` and a path
    heading is their parent. The bundle is not a vault note, so §6's H1 ban does
    not reach it.
    """
    block = zk_read.render_frontmatter(note.frontmatter)
    body = note.body.strip("\n")
    rendered = f"# {note.rel}\n\n---\n{block}\n---\n"
    return f"{rendered}\n{body}\n" if body else rendered


def _section(label: str, notes: Sequence[Note], count: int | None = None) -> BundleSection:
    return BundleSection(
        label=label,
        count=len(notes) if count is None else count,
        text="\n".join(_render_note(note) for note in notes),
    )


def _plural(count: int, singular: str) -> str:
    return f"{count} {singular}" if count == 1 else f"{count} {singular}s"


def _inventory(slug: str, sections: Sequence[BundleSection]) -> str:
    """One factual comment naming only what the bundle contains (§8.1, D-021).

    Diagnostic by category and load-bearing by obligation (D-066): nothing
    branches on it, *and* D-052 makes it the surface that declares a skip. Absent
    categories do not appear; when nothing at all survived, the slug stands alone
    rather than trailing an empty list.
    """
    parts = [
        "charter" if section.label == "charter"
        else _plural(section.count, _SINGULAR[section.label])
        for section in sections
        if section.count
    ]
    return f"<!-- zk: {slug} | {', '.join(parts)} -->" if parts else f"<!-- zk: {slug} -->"


def _skip_notice(skip: NoteParseError) -> str:
    """Mandatory on any skip, naming the file and the lint remedy (§8.1, D-052).

    Bundle self-description, not a vault diagnostic — D-024 keeps complaints
    about *other* notes out of the bundle; this reports the completeness of what
    is being handed over. Which of the three parse shapes failed stays on stderr:
    grading a parse failure is lint's jurisdiction (D-052).
    """
    return (f"<!-- zk: SKIPPED {skip.rel} — frontmatter did not parse. "
            "Run zk_lint.py on it. -->")


# --- gathering ------------------------------------------------------------------


def _log_date(note: Note) -> str:
    """`stem[:10]` — positional, because the date itself contains hyphens (§3)."""
    return note.rel.stem[:10]


def _count_entries(note: Note) -> int:
    return sum(1 for line in note.body.split("\n") if _ENTRY.match(line))


def _gather(slug: str) -> _Gathered:
    charter: Note | None = None
    decisions: Note | None = None
    logs: list[Note] = []
    skipped: list[NoteParseError] = []

    for item in zk_read.iter_notes(subtree=zk_read.project_subtree(slug)):
        if isinstance(item, NoteParseError):
            skipped.append(item)
            continue
        parts = item.rel.parts
        if len(parts) == 3 and parts[2] == zk_read.CHARTER:
            charter = item
        elif len(parts) == 3 and parts[2] == DECISIONS:
            decisions = item
        elif len(parts) == 4 and parts[2] == zk_read.LOG_DIR:
            logs.append(item)
        # Anything else under the project is a stray: skipped silently here and
        # reported by lint. Warnings never enter the bundle (D-024).

    topics, topic_skips = _topics_for(charter)
    skipped.extend(topic_skips)

    # D-012's pinned sort, so identical content cannot reorder between runs:
    # filename date descending, vault-relative path ascending as tiebreak.
    logs.sort(key=lambda note: str(note.rel))
    logs.sort(key=_log_date, reverse=True)

    sections = [
        _section("charter", [charter] if charter else []),
        _section("decisions", [decisions] if decisions else [],
                 count=_count_entries(decisions) if decisions else 0),
        _section("logs", logs[:DEFAULT_LOGS]),
        _section("topics", topics),
    ]
    return _Gathered(sections=sections, skipped=skipped)


def _topics_for(charter: Note | None) -> tuple[list[Note], list[NoteParseError]]:
    """Topics whose tags intersect the project's (§8.1). `--topics` overrides at T-05."""
    if charter is None:
        return [], []
    wanted = {str(tag) for tag in charter.frontmatter.get("tags") or []}
    if not wanted:
        return [], []

    matched: list[Note] = []
    skipped: list[NoteParseError] = []
    for item in zk_read.iter_notes(subtree=PurePosixPath(zk_read.TOPICS)):
        if isinstance(item, NoteParseError):
            skipped.append(item)
            continue
        if wanted & {str(tag) for tag in item.frontmatter.get("tags") or []}:
            matched.append(item)
    matched.sort(key=lambda note: str(note.rel))
    return matched, skipped


# --- assembly -------------------------------------------------------------------


def _assemble(slug: str) -> tuple[str, list[NoteParseError]]:
    state = zk_read.resolve_project(slug)
    if state is not ProjectState.CHARTED:
        raise zk_read.unresolved_error(slug, state)

    gathered = _gather(slug)
    head = [_inventory(slug, gathered.sections)]
    head.extend(_skip_notice(skip) for skip in gathered.skipped)
    body = "\n\n".join(
        section.text.strip("\n") for section in gathered.sections if section.text
    )
    text = "\n".join(head) + "\n"
    if body:
        text += "\n" + body + "\n"
    return text, gathered.skipped


def build_bundle(slug: str) -> str:
    """The markdown bundle for one project. Flags land in T-05.

    Raises `ZkError` (exit 1) when the slug is not CHARTED.
    """
    return _assemble(slug)[0]


def _report_skips(skips: Sequence[NoteParseError], err: TextIO) -> None:
    """Which shape failed, on stderr only — permitted there, banned on stdout (D-024)."""
    for skip in skips:
        print(f"zk: skipped {skip.rel} — {skip.reason}. Run zk_lint.py on it.", file=err)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="zk_recall.py",
        description="Print one project's context bundle to stdout.",
    )
    parser.add_argument("project", help="project slug to assemble a bundle for")
    args = parser.parse_args(argv)

    try:
        zk_config.current()  # banner first, before anything reaches stdout (D-014)
        bundle, skips = _assemble(args.project)
    except ZkError as exc:
        return zk_config.report(exc)

    _report_skips(skips, sys.stderr)
    sys.stdout.write(bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
