"""`zk_read.py` — the exclusion predicate, the walker, parsing, and slug states.

SPEC §2, §3, §4, §9, §11 · D-016, D-019, D-020, D-028, D-052, D-053, D-067.

The **behavioral** exclusion suite is T-03's and stays whole there
(`tests/test_exclusion.py`). What is asserted here is the predicate this chunk
writes — ordinary layering, not a staged rollout of D-053's one-suite clause
(scope ruled 2026-08-18, docs/plan.md).
"""

from __future__ import annotations

from pathlib import PurePosixPath

import pytest

import zk_read
from zk_read import NoteParseError, ProjectState

from conftest import write_note

CHARTER = """---
type: project
project: {slug}
tags: [{tags}]
status: active
updated: 2026-08-14
summary: A charter dense enough to clear the twenty-character floor in section five
---

## Stack
- Nothing yet.

## Conventions
- Nothing yet.

## Current state
- Nothing yet.
"""


def charter(slug: str = "game-x", tags: str = "engine") -> str:
    return CHARTER.format(slug=slug, tags=tags)


# --- exclusion: every row of SPEC §9's table, as string input --------------------


@pytest.mark.parametrize(
    ("rel", "excluded", "why"),
    [
        ("private/budgeting-y/accounts.md", True, "root private"),
        ("archive/old-vault/notes.md", True, "root archive"),
        ("projects/game-x/private/secrets.md", True, "any-component"),
        ("projects/private/notes.md", True, "any-component; slug shadowing"),
        ("Private/cased.md", True, "casefolded"),
        ("projects/private-api/project.md", False, "component match, not substring"),
    ],
)
def test_exclusion_table(ground_vault, use_vault, rel, excluded, why):
    use_vault(ground_vault)
    path = PurePosixPath(rel)
    assert zk_read.is_excluded(path, ground_vault / rel) is excluded, why


@pytest.mark.parametrize("rel", ["ARCHIVE/x.md", "projects/PRIVATE/x.md", "Archive/a/b.md"])
def test_exclusion_is_casefolded_at_every_depth(ground_vault, use_vault, rel):
    use_vault(ground_vault)
    assert zk_read.is_excluded(PurePosixPath(rel), ground_vault / rel)


@pytest.mark.parametrize(
    "rel", ["projects/private-api/project.md", "topics/archived-formats.md",
            "projects/game-x/log/2026-08-14-privateer.md"],
)
def test_substrings_of_reserved_names_are_not_excluded(ground_vault, use_vault, rel):
    use_vault(ground_vault)
    assert not zk_read.is_excluded(PurePosixPath(rel), ground_vault / rel)


def test_a_clean_path_pointing_into_private_is_excluded_on_its_target(
    ground_vault, use_vault
):
    """The symlink arm, asserted on the predicate. The behavioural suite is T-03's."""
    use_vault(ground_vault)
    rel = PurePosixPath("projects/game-x/notes.md")
    target = ground_vault / "private" / "secrets.md"
    assert zk_read.is_excluded(rel, target)


def test_a_target_outside_the_vault_is_judged_on_its_own_components(
    ground_vault, use_vault, tmp_path
):
    use_vault(ground_vault)
    rel = PurePosixPath("projects/game-x/notes.md")
    assert zk_read.is_excluded(rel, tmp_path / "elsewhere" / "archive" / "x.md")
    assert not zk_read.is_excluded(rel, tmp_path / "elsewhere" / "ok" / "x.md")


def test_a_vault_living_under_an_archive_directory_is_not_wholly_excluded(
    tmp_path, use_vault
):
    """Relativizing before matching is what keeps the vault's own ancestors out."""
    root = tmp_path / "archive" / "vault"
    (root / "projects").mkdir(parents=True)
    use_vault(root)
    rel = PurePosixPath("projects/game-x/project.md")
    assert not zk_read.is_excluded(rel, root / "projects" / "game-x" / "project.md")


# --- walking --------------------------------------------------------------------


def test_walker_yields_both_minimal_notes_and_nothing_else(vault_factory):
    root = vault_factory("minimal")
    found = [zk_read.relative(p) for p in zk_read.iter_note_paths()]
    assert found == [
        PurePosixPath("projects/game-x/log/2026-08-14-save-system.md"),
        PurePosixPath("projects/game-x/project.md"),
    ]
    assert all(isinstance(p, PurePosixPath) for p in found)


def test_walker_skips_excluded_subtrees(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "private/secrets.md", charter("secrets"))
    write_note(root, "archive/old/notes.md", charter("old"))
    write_note(root, "projects/game-x/private/leak.md", charter("leak"))
    found = {str(zk_read.relative(p)) for p in zk_read.iter_note_paths()}
    assert not [rel for rel in found if "private" in rel or "archive" in rel]
    assert len(found) == 2


def test_walker_sees_stray_markdown_outside_the_schema(vault_factory):
    """No exempt category (§8, D-052) — grading a stray is lint's job, not the walker's."""
    root = vault_factory("minimal")
    write_note(root, ".obsidian/workspace.md", "no frontmatter here\n")
    found = {str(zk_read.relative(p)) for p in zk_read.iter_note_paths()}
    assert ".obsidian/workspace.md" in found


def test_walker_ignores_non_markdown(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/notes.txt", "not a note\n")
    assert len(list(zk_read.iter_note_paths())) == 2


def test_subtree_narrows_the_walk(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "topics/serialization.md", charter("t"))
    found = {str(zk_read.relative(p))
             for p in zk_read.iter_note_paths(subtree=PurePosixPath("topics"))}
    assert found == {"topics/serialization.md"}


def test_subtree_that_is_itself_excluded_yields_nothing(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "private/x.md", charter("x"))
    assert list(zk_read.iter_note_paths(subtree=PurePosixPath("private"))) == []


def test_missing_subtree_yields_nothing(vault_factory):
    vault_factory("minimal")
    assert list(zk_read.iter_note_paths(subtree=PurePosixPath("projects/absent"))) == []


def test_walk_order_is_stable_across_runs(vault_factory):
    vault_factory("minimal")
    first = [str(zk_read.relative(p)) for p in zk_read.iter_note_paths()]
    second = [str(zk_read.relative(p)) for p in zk_read.iter_note_paths()]
    assert first == second


# --- parsing --------------------------------------------------------------------


def test_read_note_splits_frontmatter_from_body(vault_factory):
    root = vault_factory("minimal")
    note = zk_read.read_note(root / "projects" / "game-x" / "project.md")
    assert note.frontmatter["type"] == "project"
    assert note.frontmatter["project"] == "game-x"
    assert note.frontmatter["tags"] == ["engine", "save-system"]
    assert note.rel == PurePosixPath("projects/game-x/project.md")
    assert note.body.lstrip("\n").startswith("## Stack")
    assert "---" not in note.body


def test_read_note_tolerates_a_bom(vault_factory):
    """`utf-8-sig` here and only here (§3, D-028). Lint still flags it — ZK034, T-06."""
    root = vault_factory("minimal")
    path = root / "projects" / "game-x" / "project.md"
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    assert zk_read.read_note(path).frontmatter["type"] == "project"


def test_read_note_reads_crlf_without_leaving_carriage_returns(vault_factory):
    root = vault_factory("minimal")
    path = root / "projects" / "game-x" / "project.md"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    note = zk_read.read_note(path)
    assert note.frontmatter["type"] == "project"
    assert "\r" not in note.body


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("no frontmatter at all\n", NoteParseError.NO_FRONTMATTER),
        ("---\ntype: log\nnever closed\n", NoteParseError.NO_FRONTMATTER),
        ("---\ntype: [unclosed\n---\n\nbody\n", NoteParseError.MALFORMED_YAML),
        ("---\njust a string\n---\n\nbody\n", NoteParseError.NOT_A_MAPPING),
        ("---\n---\n\nbody\n", NoteParseError.NOT_A_MAPPING),
        ("", NoteParseError.NO_FRONTMATTER),
    ],
)
def test_read_note_names_which_of_the_three_shapes_failed(
    vault_factory, text, reason
):
    root = vault_factory("minimal")
    path = write_note(root, "projects/game-x/log/2026-08-15-broken.md", text)
    with pytest.raises(NoteParseError) as caught:
        zk_read.read_note(path)
    assert caught.value.reason == reason
    assert caught.value.rel == PurePosixPath(
        "projects/game-x/log/2026-08-15-broken.md"
    )


def test_iter_notes_hands_back_failures_as_data(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/log/2026-08-15-broken.md", "nope\n")
    items = list(zk_read.iter_notes(subtree=PurePosixPath("projects/game-x")))
    failures = [i for i in items if isinstance(i, NoteParseError)]
    assert len(items) == 3 and len(failures) == 1


def test_unknown_keys_survive_the_read(vault_factory):
    """Cargo: preserved and inert (D-029). Nothing in `scripts/` branches on one."""
    root = vault_factory("minimal")
    path = write_note(
        root,
        "topics/serialization.md",
        "---\ntype: topic\ntags: [serialization]\nstatus: active\n"
        "updated: 2026-08-14\nsummary: Version the payload header before shipping "
        "any serializer\naliases: [ser]\ncssclasses: dense\n---\n\n## Rule\n- Yes.\n",
    )
    note = zk_read.read_note(path)
    assert note.frontmatter["aliases"] == ["ser"]
    assert note.frontmatter["cssclasses"] == "dense"


# --- slug resolution ------------------------------------------------------------


def test_charted(vault_factory):
    vault_factory("minimal")
    assert zk_read.resolve_project("game-x") is ProjectState.CHARTED


def test_uncharted(vault_factory):
    root = vault_factory("minimal")
    (root / "projects" / "half-made").mkdir()
    assert zk_read.resolve_project("half-made") is ProjectState.UNCHARTED


def test_uncharted_with_logs_is_still_uncharted(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "projects/orphan/log/2026-08-14-x.md", "---\ntype: log\n---\n")
    assert zk_read.resolve_project("orphan") is ProjectState.UNCHARTED


def test_absent(vault_factory):
    vault_factory("minimal")
    assert zk_read.resolve_project("nope") is ProjectState.ABSENT


def test_a_slug_shadowing_a_reserved_name_resolves_absent(vault_factory):
    """The accepted cost in D-053. ZK044 keeps it from being traceless — T-03."""
    root = vault_factory("minimal")
    write_note(root, "projects/private/project.md", charter("private"))
    assert zk_read.resolve_project("private") is ProjectState.ABSENT


def test_known_slugs_is_sorted_and_charter_gated(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "projects/alpha/project.md", charter("alpha"))
    (root / "projects" / "zeta-uncharted").mkdir()
    assert zk_read.known_slugs() == ["alpha", "game-x"]


def test_known_slugs_is_empty_on_the_ground_state(ground_vault, use_vault):
    use_vault(ground_vault)
    assert zk_read.known_slugs() == []


# --- messages -------------------------------------------------------------------


def test_uncharted_message_names_the_missing_file(vault_factory):
    root = vault_factory("minimal")
    (root / "projects" / "half-made").mkdir()
    error = zk_read.unresolved_error("half-made", ProjectState.UNCHARTED)
    assert error.exit_code == 1
    assert "projects/half-made/project.md is missing" in str(error)
    assert "/zk:recall half-made" in str(error)


def test_absent_message_lists_the_known_slugs(vault_factory):
    vault_factory("minimal")
    error = zk_read.unresolved_error("nope", ProjectState.ABSENT)
    assert error.exit_code == 1
    assert "unknown project 'nope'" in str(error)
    assert "Known projects: game-x" in str(error)


def test_empty_vault_gets_its_own_message_not_a_trailing_list(ground_vault, use_vault):
    """D-062: `Known projects:` followed by nothing implies a populated set."""
    use_vault(ground_vault)
    error = zk_read.unresolved_error("nope", ProjectState.ABSENT)
    assert error.exit_code == 1
    assert "this vault has no projects yet" in str(error)
    assert "Known projects" not in str(error)


# --- CLI (D-067) ----------------------------------------------------------------


def test_cli_list_prints_slugs(vault_factory, capsys):
    vault_factory("minimal")
    assert zk_read.main(["--list"]) == 0
    assert capsys.readouterr().out == "game-x\n"


def test_cli_list_on_an_empty_vault_says_so_on_stderr(ground_vault, use_vault, capsys):
    use_vault(ground_vault)
    assert zk_read.main(["--list"]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "this vault has no projects yet" in captured.err


def test_cli_slug_prints_paths_and_frontmatter(vault_factory, capsys):
    vault_factory("minimal")
    assert zk_read.main(["game-x"]) == 0
    out = capsys.readouterr().out
    assert "projects/game-x/project.md" in out
    assert "projects/game-x/log/2026-08-14-save-system.md" in out
    assert "  type: project" in out
    assert "  type: log" in out


def test_cli_never_folds_a_long_summary(vault_factory, capsys):
    """§5 requires one line. YAML's 80-column default fold would break it."""
    root = vault_factory("minimal")
    dense = "S" * 190
    write_note(
        root, "projects/wide/project.md",
        f"---\ntype: project\nproject: wide\ntags: [engine]\nstatus: active\n"
        f"updated: 2026-08-14\nsummary: {dense}\n---\n\n## Stack\n- x\n",
    )
    assert zk_read.main(["wide"]) == 0
    assert f"  summary: {dense}" in capsys.readouterr().out


def test_cli_keeps_tags_on_one_line(vault_factory, capsys):
    vault_factory("minimal")
    zk_read.main(["game-x"])
    assert "  tags: [engine, save-system]" in capsys.readouterr().out


def test_cli_absent_slug_exits_1_with_the_list(vault_factory, capsys):
    vault_factory("minimal")
    assert zk_read.main(["nope"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Known projects: game-x" in captured.err


def test_cli_uncharted_slug_exits_1_naming_the_file(vault_factory, capsys):
    root = vault_factory("minimal")
    (root / "projects" / "half-made").mkdir()
    assert zk_read.main(["half-made"]) == 1
    assert "projects/half-made/project.md is missing" in capsys.readouterr().err


def test_cli_unparseable_note_is_skipped_not_fatal(vault_factory, capsys):
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/log/2026-08-15-broken.md", "nope\n")
    assert zk_read.main(["game-x"]) == 0
    captured = capsys.readouterr()
    assert "2026-08-15-broken.md" in captured.err
    assert "2026-08-15-broken.md" not in captured.out


def test_cli_requires_exactly_one_of_slug_or_list(vault_factory):
    vault_factory("minimal")
    for argv in ([], ["game-x", "--list"]):
        with pytest.raises(SystemExit) as caught:
            zk_read.main(argv)
        assert caught.value.code == 2


def test_cli_reports_an_unconfigured_vault_with_2(monkeypatch, capsys):
    monkeypatch.delenv("ZK_VAULT", raising=False)
    assert zk_read.main(["--list"]) == 2
    assert "no vault configured" in capsys.readouterr().err
