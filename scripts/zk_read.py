"""The vault-walking chokepoint — the only place `private/` and `archive/` are excluded.

SPEC §2 (layout, slug states), §3 (encoding), §4 (frontmatter), §9 (exclusion),
§11 (exit codes) · D-016, D-019, D-020, D-028, D-052, D-053, D-067.

No other script walks the vault. A bypass is a bug, not a shortcut — enforced by
the grep companion at T-03. The vault is **ambient**, resolved once per process by
`zk_config.current()`, so no entry point here takes it as a parameter (D-020, and
docs/plan.md's P-05 conformance).
"""

from __future__ import annotations

import argparse
import enum
import sys
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple, TextIO

import yaml

import zk_config
from zk_config import ZkError

PROJECTS = "projects"
TOPICS = "topics"
CHARTER = "project.md"
LOG_DIR = "log"

RESERVED = frozenset({"private", "archive"})
"""Names that exclude a path when they appear as any component of it (§9, D-053)."""

NOTE_SUFFIX = ".md"


class ProjectState(enum.Enum):
    CHARTED = "CHARTED"
    UNCHARTED = "UNCHARTED"
    ABSENT = "ABSENT"


class Note(NamedTuple):
    path: Path
    """Absolute, as walked."""
    rel: PurePosixPath
    """Vault-relative, forward slashes — the form every comparison uses."""
    frontmatter: dict[str, Any]
    """The parsed mapping. Unknown keys ride along and are never read (D-029)."""
    body: str
    """Everything after the closing `---`."""


class NoteParseError(Exception):
    """One of §9/D-052's three parse shapes. This module reports; lint grades."""

    NO_FRONTMATTER = "no frontmatter"
    MALFORMED_YAML = "malformed yaml"
    NOT_A_MAPPING = "not a mapping"

    def __init__(self, rel: PurePosixPath, reason: str) -> None:
        super().__init__(f"{rel}: {reason}")
        self.rel = rel
        self.reason = reason


def vault() -> Path:
    return zk_config.current().path


# --- exclusion ------------------------------------------------------------------


def _reserved_hit(parts: Iterable[str]) -> bool:
    """Component match, casefolded — never substring (§9, D-053).

    Casefolded because this test runs *before* lint, so it cannot depend on
    D-025's lowercase rule having passed. `projects/private-api/` is not a hit:
    `private-api` is one component and it is not a reserved name.
    """
    return any(part.casefold() in RESERVED for part in parts)


def is_excluded(rel: PurePosixPath, resolved: Path) -> bool:
    """True when `rel` must never be read, indexed, or bundled (§9, D-053).

    Two arms, either of which excludes: the **walked** vault-relative path, and
    the **resolved target**, which catches a symlink pointing into `private/`.
    The walked arm catches the mirror case, a link *from* `private/` outward.

    A target inside the vault is judged on its vault-relative components, so a
    vault that itself lives under some unrelated `archive/` directory is not
    wholly excluded. A target outside the vault is judged on all of its
    components — over-exclusion, which is the direction D-053 says to err in.
    """
    if _reserved_hit(rel.parts):
        return True
    return _reserved_hit(_target_parts(resolved))


def _target_parts(resolved: Path) -> tuple[str, ...]:
    root = vault()
    try:
        return PurePosixPath(resolved.relative_to(root).as_posix()).parts
    except ValueError:
        return resolved.parts


# --- walking --------------------------------------------------------------------


def iter_note_paths(*, subtree: PurePosixPath | None = None) -> Iterator[Path]:
    """Yield every `.md` path in the vault that exclusion permits, in a fixed order.

    Excluded directories are **pruned**, not filtered after the fact: `archive/`
    is documented to hold a whole legacy vault, and descending into it to throw
    the results away would make every command pay for content no command may use.

    Every top-level directory is walked, not just `projects/` and `topics/` — a
    stray `.md` is counted and skipped by consumers, never exempted (§8, D-052).
    """
    root = vault()
    start = root if subtree is None else root / Path(*subtree.parts)
    start_rel = PurePosixPath() if subtree is None else subtree

    if not start.is_dir():
        return
    if start_rel.parts and is_excluded(start_rel, start.resolve()):
        return
    yield from _walk(start, start_rel, seen={start.resolve()})


def _walk(directory: Path, rel_dir: PurePosixPath, seen: set[Path]) -> Iterator[Path]:
    for entry in sorted(directory.iterdir(), key=lambda p: p.name):
        rel = rel_dir / entry.name
        resolved = entry.resolve()
        if is_excluded(rel, resolved):
            continue
        if entry.is_dir():
            if resolved in seen:  # a symlink cycle is not a reason to hang
                continue
            seen.add(resolved)
            yield from _walk(entry, rel, seen)
        elif entry.suffix == NOTE_SUFFIX:
            yield entry


def relative(path: Path) -> PurePosixPath:
    """Vault-relative, forward slashes — the only form paths are compared in.

    Lexical first, so a symlink whose target lies outside the vault still reports
    the path it was *walked* as. Resolving is the fallback for a caller that
    handed us a path spelled differently from the vault root.
    """
    root = vault()
    try:
        return PurePosixPath(path.relative_to(root).as_posix())
    except ValueError:
        return PurePosixPath(path.resolve().relative_to(root).as_posix())


# --- reading --------------------------------------------------------------------


def read_note(path: Path) -> Note:
    """Parse one note. Raises `NoteParseError` naming which of three shapes failed.

    Opened `utf-8-sig`, so a BOM is tolerated here and **only** here — BOM
    handling exists in exactly one place (§3, D-028). Lint still flags it
    (ZK034); tolerating a BOM does not make it harmless to other agents.
    """
    rel = relative(path)
    with open(path, encoding="utf-8-sig") as handle:
        text = handle.read()

    raw, body = _split_frontmatter(text, rel)
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise NoteParseError(rel, NoteParseError.MALFORMED_YAML) from exc
    if not isinstance(parsed, dict):
        raise NoteParseError(rel, NoteParseError.NOT_A_MAPPING)
    return Note(path=path, rel=rel, frontmatter=parsed, body=body)


def _split_frontmatter(text: str, rel: PurePosixPath) -> tuple[str, str]:
    """Return the raw YAML and the body. `---` on line 1, `---` closing (§4)."""
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != "---":
        raise NoteParseError(rel, NoteParseError.NO_FRONTMATTER)
    for index in range(1, len(lines)):
        if lines[index].rstrip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1:])
    raise NoteParseError(rel, NoteParseError.NO_FRONTMATTER)


_UNFOLDED = 10 ** 6
"""No line folding: §5 requires `summary` on one line, and a fold would break it."""


def render_frontmatter(frontmatter: dict[str, Any]) -> str:
    """A note's frontmatter as a YAML block — the one renderer every consumer uses.

    Key order is preserved (`safe_load` keeps insertion order) and values
    round-trip semantically; only quoting and flow style may differ, the same
    latitude D-029 grants `--fix`. Flow style for simple collections keeps
    `tags: [a, b]` on one line, which is what the vault is written as and what
    D-001's density argument wants in a bundle.
    """
    return yaml.safe_dump(
        frontmatter,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=None,
        width=_UNFOLDED,
    ).rstrip("\n")


def iter_notes(*, subtree: PurePosixPath | None = None) -> Iterator[Note | NoteParseError]:
    """Read every permitted note, handing back the failure rather than raising it.

    Consumers are fail-soft (§8, §8.1, D-052) and each declares its own skips, so
    a parse failure is data here, not control flow.
    """
    for path in iter_note_paths(subtree=subtree):
        try:
            yield read_note(path)
        except NoteParseError as exc:
            yield exc


# --- slug resolution ------------------------------------------------------------


def resolve_project(slug: str) -> ProjectState:
    """§2/D-020, verbatim: CHARTED, UNCHARTED, or ABSENT.

    A slug shadowing a reserved name resolves ABSENT — an excluded directory is
    invisible to every consumer, which is the accepted cost in D-053. ZK044, the
    warning that keeps that cost from being traceless, lands at T-03.
    """
    rel = PurePosixPath(PROJECTS) / slug
    directory = vault() / PROJECTS / slug
    if not directory.is_dir() or is_excluded(rel, directory.resolve()):
        return ProjectState.ABSENT
    if (directory / CHARTER).is_file():
        return ProjectState.CHARTED
    return ProjectState.UNCHARTED


def known_slugs() -> list[str]:
    """Every slug with a charter, sorted. UNCHARTED directories do not appear (§2)."""
    slugs = []
    for path in iter_note_paths(subtree=PurePosixPath(PROJECTS)):
        parts = relative(path).parts
        if len(parts) == 3 and parts[0] == PROJECTS and parts[2] == CHARTER:
            slugs.append(parts[1])
    return sorted(slugs)


def project_subtree(slug: str) -> PurePosixPath:
    return PurePosixPath(PROJECTS) / slug


def unresolved_error(slug: str, state: ProjectState) -> ZkError:
    """The §2 and §12 messages, verbatim, in one place for every consumer.

    Both scripts and both skills branch on `resolve_project`; neither may
    reimplement its messages either (D-020, D-030). Exit 1 throughout — the
    script ran, looked, and reported (D-019).
    """
    if state is ProjectState.UNCHARTED:
        return ZkError(
            f"zk: '{slug}' has no charter.\n"
            f"  {PROJECTS}/{slug}/ exists but {PROJECTS}/{slug}/{CHARTER} is missing.\n"
            f"  Run /zk:recall {slug} to scaffold the charter, or create the file "
            "directly.",
            exit_code=1,
        )
    slugs = known_slugs()
    if not slugs:
        # D-062: the zero-slug vault gets its own message, never a populated-vault
        # template trailing off after `Known projects:`.
        return ZkError(
            "zk: this vault has no projects yet.\n"
            "  Run /zk:recall <slug> to create the first one.",
            exit_code=1,
        )
    return ZkError(
        f"zk: unknown project '{slug}'.\n"
        f"  Known projects: {', '.join(slugs)}\n"
        f"  Run /zk:recall {slug} to scaffold a new project.",
        exit_code=1,
    )


# --- CLI (D-067) ----------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zk_read.py",
        description=(
            "Print a project's note paths and frontmatter, or the known project slugs. "
            "Exposes the exclusion chokepoint so no agent has to walk the vault itself."
        ),
    )
    parser.add_argument("slug", nargs="?", help="project slug to describe")
    parser.add_argument(
        "--list", action="store_true", dest="list_slugs",
        help="print the known project slugs, one per line",
    )
    return parser


def _print_slugs(out: TextIO, err: TextIO) -> int:
    slugs = known_slugs()
    if not slugs:
        # Nothing on stdout, so the machine-readable surface stays honest; the
        # human gets D-062's message on stderr. Enumerating zero slugs is a
        # complete answer, so this is exit 0 (D-019).
        print(
            "zk: this vault has no projects yet.\n"
            "  Run /zk:recall <slug> to create the first one.",
            file=err,
        )
        return 0
    for slug in slugs:
        print(slug, file=out)
    return 0


def _print_project(slug: str, out: TextIO, err: TextIO) -> int:
    state = resolve_project(slug)
    if state is not ProjectState.CHARTED:
        return zk_config.report(unresolved_error(slug, state), stream=err)

    for item in iter_notes(subtree=project_subtree(slug)):
        if isinstance(item, NoteParseError):
            # Fail-soft, declared: the read itself succeeded (D-052).
            print(f"zk: skipped {item.rel} — {item.reason}. Run zk_lint.py on it.",
                  file=err)
            continue
        print(item.rel, file=out)
        for line in render_frontmatter(item.frontmatter).split("\n"):
            print(f"  {line}", file=out)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.list_slugs == bool(args.slug):
        parser.error("give exactly one of <slug> or --list")

    try:
        zk_config.current()
        if args.list_slugs:
            return _print_slugs(sys.stdout, sys.stderr)
        return _print_project(args.slug, sys.stdout, sys.stderr)
    except ZkError as exc:
        return zk_config.report(exc)


if __name__ == "__main__":
    raise SystemExit(main())
