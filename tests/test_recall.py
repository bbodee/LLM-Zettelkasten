"""`zk_recall.py` — bundle order, omission, the inventory comment, skip declaration.

SPEC §8.1, §9, §11, §12 · D-019, D-020, D-021, D-024, D-052, D-062.
Section 1 (the computed index section) and the flags are T-05's.
"""

from __future__ import annotations

import pytest

import zk_recall

from conftest import write_note

CHARTER_PATH = "projects/game-x/project.md"
LOG_PATH = "projects/game-x/log/2026-08-14-save-system.md"

DECISIONS = """---
type: decision
project: game-x
tags: [save-system]
updated: 2026-09-02
summary: Decisions on save format, compression, and input rebinding
---

## D-001 — 2026-07-28 — Store action names, not scancodes
- Decision: rebinding persists action names.

## D-002 — 2026-08-11 — Chunk the tilemap at 64x64
- Decision: autotile recalculation operates on chunks.

## D-003 — 2026-08-14 — Versioned JSON over pickle for saves
- Decision: saves are JSON with a `schema_version` header.
"""

TOPIC = """---
type: topic
tags: [{tags}]
status: active
updated: 2026-08-14
summary: Version the payload header before shipping any serializer; retrofits need a sniffer
---

## Rule
- Write `schema_version` from day one.
"""


def log(date: str, slug: str) -> str:
    return (
        f"---\ntype: log\nproject: game-x\ntags: [save-system]\nupdated: {date}\n"
        f"summary: A log summary long enough to clear the twenty-character floor\n"
        f"---\n\n## Done\n- Something happened in {slug}.\n"
    )


# --- the skeleton bundle --------------------------------------------------------


def test_minimal_bundle_is_charter_then_log_and_nothing_else(vault_factory):
    vault_factory("minimal")
    bundle = zk_recall.build_bundle("game-x")

    assert bundle.splitlines()[0] == "<!-- zk: game-x | charter, 1 log -->"
    assert bundle.index(f"# {CHARTER_PATH}") < bundle.index(f"# {LOG_PATH}")
    assert "decisions.md" not in bundle
    assert "topics/" not in bundle
    assert "SKIPPED" not in bundle


def test_absent_sections_leave_no_header_of_any_kind(vault_factory):
    """D-021: omitted entirely — no empty headers, no narration of what is missing."""
    vault_factory("minimal")
    bundle = zk_recall.build_bundle("game-x").lower()
    for ghost in ("decisions", "topics", "no decisions", "none", "empty"):
        assert f"# {ghost}" not in bundle
    assert "yet" not in bundle


def test_bundle_carries_frontmatter_and_body_verbatim_enough(vault_factory):
    vault_factory("minimal")
    bundle = zk_recall.build_bundle("game-x")
    assert "type: project" in bundle
    assert "tags: [engine, save-system]" in bundle
    assert "## Stack" in bundle
    assert "## Done" in bundle


def test_a_long_summary_stays_on_one_line(vault_factory):
    root = vault_factory("minimal")
    dense = "S" * 190
    write_note(
        root, "projects/wide/project.md",
        f"---\ntype: project\nproject: wide\ntags: [engine]\nstatus: active\n"
        f"updated: 2026-08-14\nsummary: {dense}\n---\n\n## Stack\n- x\n"
        f"\n## Conventions\n- x\n\n## Current state\n- x\n",
    )
    bundle = zk_recall.build_bundle("wide")
    assert f"summary: {dense}" in bundle


# --- full bundle order ----------------------------------------------------------


def test_all_four_sections_appear_in_spec_order(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/decisions.md", DECISIONS)
    write_note(root, "topics/serialization.md", TOPIC.format(tags="save-system"))
    bundle = zk_recall.build_bundle("game-x")

    order = [
        bundle.index(f"# {CHARTER_PATH}"),
        bundle.index("# projects/game-x/decisions.md"),
        bundle.index(f"# {LOG_PATH}"),
        bundle.index("# topics/serialization.md"),
    ]
    assert order == sorted(order)
    assert bundle.splitlines()[0] == (
        "<!-- zk: game-x | charter, 3 decisions, 1 log, 1 topic -->"
    )


def test_inventory_counts_decision_entries_not_files(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/decisions.md", DECISIONS)
    assert "3 decisions" in zk_recall.build_bundle("game-x")


def test_topics_join_on_tag_intersection_only(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "topics/serialization.md", TOPIC.format(tags="save-system"))
    write_note(root, "topics/unrelated.md", TOPIC.format(tags="gardening"))
    bundle = zk_recall.build_bundle("game-x")
    assert "topics/serialization.md" in bundle
    assert "topics/unrelated.md" not in bundle
    assert "1 topic" in bundle


def test_logs_are_capped_at_five_newest_first(vault_factory):
    root = vault_factory("minimal")
    for day in range(15, 22):
        write_note(root, f"projects/game-x/log/2026-08-{day}-t{day}.md",
                   log(f"2026-08-{day}", f"t{day}"))
    bundle = zk_recall.build_bundle("game-x")

    assert "5 logs" in bundle
    assert "2026-08-21-t21.md" in bundle
    assert "2026-08-17-t17.md" in bundle
    assert "2026-08-16-t16.md" not in bundle
    assert bundle.index("2026-08-21-t21.md") < bundle.index("2026-08-17-t17.md")


def test_bundle_is_stable_across_runs(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/decisions.md", DECISIONS)
    write_note(root, "topics/serialization.md", TOPIC.format(tags="save-system"))
    assert zk_recall.build_bundle("game-x") == zk_recall.build_bundle("game-x")


# --- exclusion ------------------------------------------------------------------


def test_no_excluded_path_reaches_the_bundle(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/private/secrets.md", log("2026-08-14", "secret"))
    write_note(root, "topics/private/leak.md", TOPIC.format(tags="save-system"))
    bundle = zk_recall.build_bundle("game-x")
    assert "private" not in bundle
    assert "secret" not in bundle


# --- fail-soft ------------------------------------------------------------------


def test_a_skip_is_declared_on_the_surface_the_model_reads(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/log/2026-08-15-broken.md", "no frontmatter\n")
    bundle = zk_recall.build_bundle("game-x")
    notice = [line for line in bundle.splitlines() if "SKIPPED" in line]
    assert len(notice) == 1
    assert "projects/game-x/log/2026-08-15-broken.md" in notice[0]
    assert "frontmatter did not parse" in notice[0]
    assert "zk_lint.py" in notice[0]


def test_a_skip_does_not_abort_the_bundle(vault_factory):
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/log/2026-08-15-broken.md", "no frontmatter\n")
    bundle = zk_recall.build_bundle("game-x")
    assert "1 log" in bundle
    assert f"# {CHARTER_PATH}" in bundle


def test_an_unparseable_charter_leaves_an_honest_inventory(vault_factory):
    root = vault_factory("minimal")
    write_note(root, CHARTER_PATH, "not a note\n")
    bundle = zk_recall.build_bundle("game-x")
    assert bundle.splitlines()[0] == "<!-- zk: game-x | 1 log -->"
    assert "SKIPPED" in bundle


def test_a_stray_file_inside_the_project_never_enters_the_bundle(vault_factory):
    """Warnings never enter the bundle — the bundle is retrieval surface (D-024)."""
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/scratch.md", log("2026-08-14", "scratch"))
    bundle = zk_recall.build_bundle("game-x")
    assert "scratch" not in bundle
    assert bundle.splitlines()[0] == "<!-- zk: game-x | charter, 1 log -->"


# --- CLI ------------------------------------------------------------------------


def test_main_prints_the_bundle_and_exits_0(vault_factory, capsys):
    vault_factory("minimal")
    assert zk_recall.main(["game-x"]) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "<!-- zk: game-x | charter, 1 log -->"
    assert captured.err.startswith("zk: vault ")


def test_the_banner_never_lands_on_stdout(vault_factory, capsys):
    vault_factory("minimal")
    zk_recall.main(["game-x"])
    captured = capsys.readouterr()
    assert "zk: vault" not in captured.out
    assert "zk: vault" in captured.err


def test_parse_shape_goes_to_stderr_never_into_the_bundle(vault_factory, capsys):
    root = vault_factory("minimal")
    write_note(root, "projects/game-x/log/2026-08-15-broken.md", "no frontmatter\n")
    assert zk_recall.main(["game-x"]) == 0
    captured = capsys.readouterr()
    assert "no frontmatter" in captured.err
    assert "no frontmatter" not in captured.out
    assert "SKIPPED" in captured.out


def test_absent_slug_exits_1_listing_known_slugs(vault_factory, capsys):
    vault_factory("minimal")
    assert zk_recall.main(["nope"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unknown project 'nope'" in captured.err
    assert "Known projects: game-x" in captured.err


def test_uncharted_slug_exits_1_naming_the_missing_charter(vault_factory, capsys):
    root = vault_factory("minimal")
    (root / "projects" / "half-made").mkdir()
    assert zk_recall.main(["half-made"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "has no charter" in captured.err
    assert "projects/half-made/project.md is missing" in captured.err


def test_empty_vault_exits_1_with_its_own_message(ground_vault, use_vault, capsys):
    use_vault(ground_vault)
    assert zk_recall.main(["anything"]) == 1
    captured = capsys.readouterr()
    assert "this vault has no projects yet" in captured.err
    assert "Known projects" not in captured.err


def test_unconfigured_vault_exits_2(monkeypatch, capsys):
    monkeypatch.delenv("ZK_VAULT", raising=False)
    assert zk_recall.main(["game-x"]) == 2
    assert "no vault configured" in capsys.readouterr().err


def test_build_bundle_raises_rather_than_exiting(vault_factory):
    from zk_config import ZkError

    vault_factory("minimal")
    with pytest.raises(ZkError) as caught:
        zk_recall.build_bundle("nope")
    assert caught.value.exit_code == 1
