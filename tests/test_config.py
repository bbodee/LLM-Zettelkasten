"""`zk_config.py` — resolution, normalization, the banner, and the exit-2 posture.

SPEC §1, §11 · D-006, D-014, D-015, D-016, D-017 as graduated by D-022, D-018,
D-019.

Config trees are built in `tmp_path` rather than committed as fixture vaults: the
subject here is directory shape and file content, not vault content (T-02).
"""

from __future__ import annotations

import io
import sys
import tomllib
from pathlib import Path

import pytest

import zk_config
from zk_config import ENV_VAR, TomlConfig, VaultConfig, ZkError

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "zk.toml.example"


def resolve(path_value=None, **kwargs):
    env = {} if path_value is None else {ENV_VAR: str(path_value)}
    return zk_config.resolve_vault(env=env, **kwargs)


def make_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def make_repo(root: Path, *, dotgit: str = "dir") -> Path:
    """A repo root. `dotgit="file"` is the worktree/submodule shape (D-015)."""
    make_dir(root)
    marker = root / ".git"
    if dotgit == "dir":
        marker.mkdir()
    else:
        with open(marker, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("gitdir: C:/work/proj/.git/worktrees/task-T-02\n")
    return root


def write_toml(directory: Path, body: str) -> Path:
    make_dir(directory)
    path = directory / "zk.toml"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    return path


def toml_naming(vault: Path, *, extra: str = "") -> str:
    return f'[zk]\nvault = "{vault.as_posix()}"\n{extra}'


# --- no vault configured --------------------------------------------------------


def test_unset_env_exits_2_naming_all_three_mechanisms(tmp_path):
    with pytest.raises(ZkError) as caught:
        resolve(cwd=tmp_path)
    assert caught.value.exit_code == 2
    message = str(caught.value)
    assert ENV_VAR in message
    assert "zk.toml" in message
    assert "zk_config.py --init" in message


def test_empty_env_reads_as_unset(tmp_path):
    """Windows deletes a variable set to the empty string, so the two cases are
    one situation on that platform. Treating them alike keeps AC-7 honest."""
    with pytest.raises(ZkError) as caught:
        zk_config.resolve_vault(env={ENV_VAR: "   "}, cwd=tmp_path)
    assert caught.value.exit_code == 2
    assert "no vault configured" in str(caught.value)


# --- normalization --------------------------------------------------------------


def test_relative_value_exits_2_and_is_never_anchored_to_cwd(tmp_path, monkeypatch):
    (tmp_path / "vault").mkdir()
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ZkError) as caught:
        resolve("vault")
    assert caught.value.exit_code == 2
    message = str(caught.value)
    assert "not absolute" in message
    assert "never anchored to the current directory" in message


def test_dot_segments_are_collapsed(tmp_path):
    (tmp_path / "vault").mkdir()
    cfg = resolve(tmp_path / "vault" / ".." / "vault")
    assert cfg.path == (tmp_path / "vault").resolve()


def test_tilde_is_expanded(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / "vault").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    cfg = resolve("~/vault")
    assert cfg.path == (home / "vault").resolve()


def test_env_vars_inside_the_value_are_not_expanded(tmp_path, monkeypatch):
    """E-013 parks expansion; `expandvars` would turn a typo into 'not found'."""
    monkeypatch.setenv("ZK_SOMEWHERE", str(tmp_path))
    with pytest.raises(ZkError) as caught:
        resolve("$ZK_SOMEWHERE/vault")
    assert caught.value.exit_code == 2


def test_missing_path_exits_2_naming_init(tmp_path):
    with pytest.raises(ZkError) as caught:
        resolve(tmp_path / "nope")
    assert caught.value.exit_code == 2
    assert "does not exist" in str(caught.value)
    assert "--init" in str(caught.value)


def test_file_instead_of_directory_exits_2(tmp_path):
    target = tmp_path / "vault"
    target.write_text("not a vault\n", encoding="utf-8", newline="\n")
    with pytest.raises(ZkError) as caught:
        resolve(target)
    assert caught.value.exit_code == 2
    assert "not a directory" in str(caught.value)


def test_source_names_the_mechanism(tmp_path):
    (tmp_path / "vault").mkdir()
    cfg = resolve(tmp_path / "vault")
    assert cfg.source == ENV_VAR
    assert cfg.ignore == ()  # T-02 fills this from zk.toml


# --- banner ---------------------------------------------------------------------


def test_banner_is_one_line_with_forward_slashes(tmp_path):
    (tmp_path / "vault").mkdir()
    cfg = resolve(tmp_path / "vault")
    stream = io.StringIO()
    zk_config.announce(cfg, stream=stream)
    printed = stream.getvalue()
    assert printed.count("\n") == 1
    assert printed == f"zk: vault {cfg.path.as_posix()}  (from {ENV_VAR})\n"
    assert "\\" not in printed


def test_banner_prints_once_per_process(tmp_path, use_vault, capsys):
    (tmp_path / "vault").mkdir()
    use_vault(tmp_path / "vault")
    zk_config.current()
    zk_config.current()
    zk_config.current()
    assert capsys.readouterr().err.count("zk: vault") == 1


def test_reset_cache_lets_a_second_vault_resolve(tmp_path, use_vault):
    for name in ("one", "two"):
        (tmp_path / name).mkdir()
        use_vault(tmp_path / name)
        assert zk_config.current().path == (tmp_path / name).resolve()


# --- CLI ------------------------------------------------------------------------


def test_main_prints_the_vault_and_exits_0(tmp_path, use_vault, capsys):
    (tmp_path / "vault").mkdir()
    use_vault(tmp_path / "vault")
    assert zk_config.main([]) == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == (tmp_path / "vault").resolve().as_posix()
    assert captured.err.startswith("zk: vault ")


def test_main_reports_and_returns_2_when_unconfigured(tmp_path, monkeypatch, capsys):
    """Run from an empty `tmp_path`: once step 2 exists, the developer's own
    `zk.toml` at the repo root would otherwise decide this test."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.chdir(make_dir(tmp_path / "elsewhere"))
    assert zk_config.main([]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no vault configured" in captured.err


def test_main_rejects_an_unknown_flag_with_2(capsys):
    with pytest.raises(SystemExit) as caught:
        zk_config.main(["--nope"])
    assert caught.value.code == 2


def test_vault_config_is_a_record_of_three_fields(tmp_path):
    (tmp_path / "vault").mkdir()
    cfg = resolve(tmp_path / "vault")
    assert isinstance(cfg, VaultConfig)
    assert cfg._fields == ("path", "source", "ignore")
    assert isinstance(cfg.path, Path) and cfg.path.is_absolute()


# --- the fence: repo root (D-015) -----------------------------------------------


def test_repo_root_is_cwd_when_cwd_holds_dot_git(tmp_path):
    root = make_repo(tmp_path / "proj")
    assert zk_config.find_repo_root(root) == root.resolve()


def test_repo_root_is_the_nearest_ancestor(tmp_path):
    root = make_repo(tmp_path / "proj")
    deep = make_dir(root / "a" / "b")
    assert zk_config.find_repo_root(deep) == root.resolve()


def test_dot_git_as_a_file_still_fences(tmp_path):
    """The worktree and submodule shape: `.git` is a file holding a `gitdir:`
    pointer, so `is_dir()` would drop the fence exactly where it matters."""
    root = make_repo(tmp_path / "worktree", dotgit="file")
    assert (root / ".git").is_file()
    assert zk_config.find_repo_root(root) == root.resolve()


def test_dot_git_as_a_file_fences_from_a_subdirectory(tmp_path):
    root = make_repo(tmp_path / "worktree", dotgit="file")
    deep = make_dir(root / "scripts")
    assert zk_config.find_repo_root(deep) == root.resolve()


def test_no_repo_anywhere_above_cwd(tmp_path):
    deep = make_dir(tmp_path / "loose" / "sub")
    assert zk_config.find_repo_root(deep) is None


def test_nearest_root_wins_over_an_outer_one(tmp_path):
    make_repo(tmp_path / "outer")
    inner = make_repo(tmp_path / "outer" / "inner")
    assert zk_config.find_repo_root(inner) == inner.resolve()


# --- the fence: search paths (D-015) --------------------------------------------


def test_search_paths_run_cwd_first_up_to_the_root_inclusive(tmp_path):
    root = make_repo(tmp_path / "proj")
    deep = make_dir(root / "a" / "b")
    assert zk_config.search_paths(deep) == [
        deep.resolve(),
        (root / "a").resolve(),
        root.resolve(),
    ]


def test_search_stops_at_the_root_and_never_climbs_past_it(tmp_path):
    root = make_repo(tmp_path / "proj")
    deep = make_dir(root / "a")
    assert root.resolve().parent not in zk_config.search_paths(deep)


def test_search_paths_at_the_root_itself_is_one_directory(tmp_path):
    root = make_repo(tmp_path / "proj")
    assert zk_config.search_paths(root) == [root.resolve()]


def test_no_repo_means_cwd_only_and_no_walk(tmp_path):
    deep = make_dir(tmp_path / "loose" / "sub")
    assert zk_config.search_paths(deep) == [deep.resolve()]


# --- step 2: finding zk.toml ----------------------------------------------------


def test_zk_toml_at_cwd_is_found(tmp_path):
    root = make_repo(tmp_path / "proj")
    vault = make_dir(tmp_path / "vault")
    write_toml(root, toml_naming(vault))
    cfg = resolve(cwd=root)
    assert cfg.path == vault.resolve()
    assert cfg.source == (root / "zk.toml").resolve().as_posix()


def test_zk_toml_at_the_repo_root_is_found_from_a_subdirectory(tmp_path):
    root = make_repo(tmp_path / "proj")
    vault = make_dir(tmp_path / "vault")
    write_toml(root, toml_naming(vault))
    deep = make_dir(root / "a" / "b")
    assert resolve(cwd=deep).path == vault.resolve()


def test_the_nearer_zk_toml_wins_when_both_exist(tmp_path):
    root = make_repo(tmp_path / "proj")
    near = make_dir(tmp_path / "near")
    far = make_dir(tmp_path / "far")
    write_toml(root, toml_naming(far))
    deep = make_dir(root / "a")
    write_toml(deep, toml_naming(near))
    cfg = resolve(cwd=deep)
    assert cfg.path == near.resolve()
    assert cfg.source == (deep / "zk.toml").resolve().as_posix()


def test_a_zk_toml_above_the_repo_root_is_never_found(tmp_path):
    """The fence's whole reason to exist: an unbounded walk turns a *deleted*
    config into a *wrong vault* rather than an error (D-015)."""
    outer = make_dir(tmp_path / "outer")
    above_vault = make_dir(tmp_path / "above-vault")
    write_toml(outer, toml_naming(above_vault))
    root = make_repo(outer / "repo")
    deep = make_dir(root / "sub")

    with pytest.raises(ZkError) as caught:
        resolve(cwd=deep)
    assert caught.value.exit_code == 2
    message = str(caught.value)
    assert "no vault configured" in message
    assert above_vault.as_posix() not in message


def test_the_no_vault_message_lists_every_directory_searched(tmp_path):
    root = make_repo(tmp_path / "proj")
    deep = make_dir(root / "a" / "b")
    with pytest.raises(ZkError) as caught:
        resolve(cwd=deep)
    message = str(caught.value)
    for directory in zk_config.search_paths(deep):
        assert directory.as_posix() in message


def test_the_no_vault_message_marks_where_the_search_stopped(tmp_path):
    root = make_repo(tmp_path / "proj")
    deep = make_dir(root / "a")
    message = str(pytest.raises(ZkError, resolve, cwd=deep).value)
    assert f"{root.resolve().as_posix()}  <- repo root; the search stops here" in message


def test_the_no_vault_message_says_so_when_there_is_no_repo(tmp_path):
    deep = make_dir(tmp_path / "loose" / "sub")
    message = str(pytest.raises(ZkError, resolve, cwd=deep).value)
    assert deep.resolve().as_posix() in message
    assert "did not walk up" in message
    assert "repo root" not in message


# --- precedence (D-014) ---------------------------------------------------------


def test_env_wins_when_both_are_set_and_disagree(tmp_path):
    root = make_repo(tmp_path / "proj")
    from_env = make_dir(tmp_path / "env-vault")
    from_file = make_dir(tmp_path / "file-vault")
    write_toml(root, toml_naming(from_file))

    cfg = zk_config.resolve_vault(env={ENV_VAR: str(from_env)}, cwd=root)
    assert cfg.path == from_env.resolve()
    assert cfg.source == ENV_VAR


def test_env_branch_carries_no_ignore_list(tmp_path):
    """D-014 stops the cascade at the first hit, so no `zk.toml` was read."""
    root = make_repo(tmp_path / "proj")
    from_env = make_dir(tmp_path / "env-vault")
    write_toml(root, toml_naming(from_env, extra='ignore = [".obsidian"]\n'))
    cfg = zk_config.resolve_vault(env={ENV_VAR: str(from_env)}, cwd=root)
    assert cfg.ignore == ()


def test_a_broken_zk_toml_is_invisible_when_env_answers(tmp_path):
    root = make_repo(tmp_path / "proj")
    vault = make_dir(tmp_path / "vault")
    write_toml(root, "this is not toml at all\n")
    assert zk_config.resolve_vault(env={ENV_VAR: str(vault)}, cwd=root).path == (
        vault.resolve()
    )


def test_banner_names_the_file_when_zk_toml_won(tmp_path):
    root = make_repo(tmp_path / "proj")
    vault = make_dir(tmp_path / "vault")
    source = write_toml(root, toml_naming(vault))
    stream = io.StringIO()
    zk_config.announce(resolve(cwd=root), stream=stream)
    printed = stream.getvalue()
    assert printed == (
        f"zk: vault {vault.resolve().as_posix()}  (from {source.resolve().as_posix()})\n"
    )
    assert "\\" not in printed


# --- schema (D-017 as graduated by D-022) ---------------------------------------


def test_load_toml_returns_the_raw_value_and_its_source(tmp_path):
    source = write_toml(tmp_path, '[zk]\nvault = "C:/Users/you/vault"\n')
    cfg = zk_config.load_toml(source)
    assert isinstance(cfg, TomlConfig)
    assert cfg._fields == ("vault", "ignore", "source")
    assert cfg.vault == "C:/Users/you/vault"
    assert cfg.ignore == ()
    assert cfg.source == source


def test_ignore_defaults_to_empty(tmp_path):
    root = make_repo(tmp_path / "proj")
    vault = make_dir(tmp_path / "vault")
    write_toml(root, toml_naming(vault))
    assert resolve(cwd=root).ignore == ()


def test_ignore_is_parsed_and_carried_onto_the_vault_config(tmp_path):
    root = make_repo(tmp_path / "proj")
    vault = make_dir(tmp_path / "vault")
    write_toml(root, toml_naming(vault, extra='ignore = [".obsidian", "attachments"]\n'))
    assert resolve(cwd=root).ignore == (".obsidian", "attachments")


@pytest.mark.parametrize(
    "line",
    [
        'vault = "C:/Users/you"',
        'vault = "C:\\\\Users\\\\you"',
        "vault = 'C:\\Users\\you'",
    ],
    ids=["forward-slash", "doubled-backslash", "literal-string"],
)
def test_all_three_string_forms_parse_to_the_same_value(tmp_path, line):
    """Rejecting a config that parses and works to enforce one style is out
    (D-017). `pathlib` normalizes separators after parsing."""
    source = write_toml(tmp_path, f"[zk]\n{line}\n")
    assert Path(zk_config.load_toml(source).vault) == Path("C:/Users/you")


def test_unknown_key_names_the_near_match(tmp_path):
    source = write_toml(tmp_path, '[zk]\nvalut = "C:/Users/you/vault"\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    assert "unknown key 'valut' in zk.toml — did you mean 'vault'?" in str(caught.value)


def test_unknown_key_with_no_near_match_still_errors(tmp_path):
    source = write_toml(tmp_path, '[zk]\nvault = "C:/v"\nzzzz = 1\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    assert "unknown key 'zzzz'" in str(caught.value)
    assert "did you mean" not in str(caught.value)


def test_a_bare_top_level_vault_key_is_directed_at_the_table(tmp_path):
    """D-022 converted the file to a `[zk]` table; the pre-table form is the
    shape a user copying an older snippet types."""
    source = write_toml(tmp_path, 'vault = "C:/Users/you/vault"\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    message = str(caught.value)
    assert "no [zk] table" in message
    assert "[zk]" in message


def test_an_unknown_top_level_table_names_zk(tmp_path):
    source = write_toml(tmp_path, '[zkk]\nvault = "C:/Users/you/vault"\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    assert "did you mean 'zk'?" in str(caught.value)


def test_an_empty_file_says_it_names_no_vault(tmp_path):
    source = write_toml(tmp_path, "# nothing here yet\n")
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    assert "names no vault" in str(caught.value)


def test_a_table_without_vault_says_which_key_is_missing(tmp_path):
    source = write_toml(tmp_path, '[zk]\nignore = [".obsidian"]\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    assert "no vault key" in str(caught.value)


def test_a_non_string_vault_is_rejected(tmp_path):
    source = write_toml(tmp_path, "[zk]\nvault = 3\n")
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    assert "not a path string" in str(caught.value)


def test_a_relative_vault_from_zk_toml_is_rejected_naming_the_file(tmp_path):
    root = make_repo(tmp_path / "proj")
    make_dir(root / "vault")
    write_toml(root, '[zk]\nvault = "vault"\n')
    with pytest.raises(ZkError) as caught:
        resolve(cwd=root)
    assert caught.value.exit_code == 2
    message = str(caught.value)
    assert "not absolute" in message
    assert (root / "zk.toml").resolve().as_posix() in message


def test_a_missing_vault_directory_from_zk_toml_exits_2(tmp_path):
    root = make_repo(tmp_path / "proj")
    write_toml(root, toml_naming(tmp_path / "nowhere"))
    with pytest.raises(ZkError) as caught:
        resolve(cwd=root)
    assert caught.value.exit_code == 2
    assert "does not exist" in str(caught.value)


def test_a_bom_prefixed_zk_toml_still_parses(tmp_path):
    """Notepad writes a BOM. `tomllib` would answer "Invalid statement (at line
    1, column 1)", which is the undirected failure D-016 bans."""
    source = tmp_path / "zk.toml"
    with open(source, "w", encoding="utf-8-sig", newline="\n") as handle:
        handle.write('[zk]\nvault = "C:/Users/you/vault"\n')
    assert source.read_bytes().startswith(b"\xef\xbb\xbf")
    assert zk_config.load_toml(source).vault == "C:/Users/you/vault"


# --- parse failure (D-016) ------------------------------------------------------


def test_unescaped_backslash_is_re_emitted_with_the_corrected_line(tmp_path):
    """The shape a Windows user types first: `\\U` opens a Unicode escape, so the
    file fails to parse before any value is read."""
    source = write_toml(tmp_path, '[zk]\nvault = "C:\\Users\\you"\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    message = str(caught.value)
    assert "cannot parse zk.toml" in message
    assert 'Line 2: vault = "C:\\Users\\you"' in message
    assert 'vault = "C:/Users/you"' in message
    assert 'vault = "C:\\\\Users\\\\you"' in message
    assert "vault = 'C:\\Users\\you'" in message


def test_a_raw_toml_decode_error_never_reaches_the_user(tmp_path):
    source = write_toml(tmp_path, '[zk]\nvault = "C:\\Users\\you"\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert not str(caught.value).startswith("Invalid")
    assert str(caught.value).startswith("zk: ")


def test_a_generic_parse_failure_shows_the_line_and_points_at_the_example(tmp_path):
    source = write_toml(tmp_path, "[zk]\nvault = C:/Users/you\n")
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    message = str(caught.value)
    assert "cannot parse zk.toml" in message
    assert "Line 2: vault = C:/Users/you" in message
    assert "zk.toml.example" in message


def test_a_doubled_backslash_is_not_mistaken_for_a_bad_escape():
    assert zk_config._has_bad_escape("C:\\\\Users\\\\you") is False
    assert zk_config._has_bad_escape("C:\\Users\\you") is True
    assert zk_config._has_bad_escape("C:/Users/you") is False


def test_a_non_utf8_zk_toml_is_re_emitted(tmp_path):
    source = tmp_path / "zk.toml"
    source.write_bytes(b'[zk]\nvault = "C:/\xff\xfe/vault"\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    assert "not valid UTF-8" in str(caught.value)


# --- `ignore` semantics (D-022) -------------------------------------------------


@pytest.mark.parametrize("name", ["private", "archive", "Private", "ARCHIVE"])
def test_ignoring_a_reserved_directory_is_a_hard_error(tmp_path, name):
    """Not a no-op, so nobody believes it did something (D-022)."""
    source = write_toml(tmp_path, f'[zk]\nvault = "C:/v"\nignore = ["{name}"]\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    message = str(caught.value)
    assert "not permitted" in message
    assert "grant nothing" in message


def test_a_reserved_name_with_a_trailing_slash_is_still_reserved(tmp_path):
    source = write_toml(tmp_path, '[zk]\nvault = "C:/v"\nignore = ["private/"]\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert "not permitted" in str(caught.value)
    assert "did you mean" not in str(caught.value)


@pytest.mark.parametrize(
    "entry, suggested",
    [
        ("attachments/", "attachments"),
        (" .obsidian", ".obsidian"),
        ("*.tmp", None),
        ("notes/drafts", None),
        ("", None),
        ("..", None),
    ],
)
def test_an_ignore_entry_that_could_never_match_is_rejected(tmp_path, entry, suggested):
    """Exact top-level directory names only. An entry that cannot match would
    silence nothing while reading as though it had — the silence D-022 ends."""
    source = write_toml(tmp_path, f'[zk]\nvault = "C:/v"\nignore = ["{entry}"]\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    message = str(caught.value)
    assert "invalid ignore entry" in message
    if suggested is None:
        assert "did you mean" not in message
    else:
        assert f"did you mean {suggested!r}?" in message


def test_a_non_list_ignore_is_rejected(tmp_path):
    source = write_toml(tmp_path, '[zk]\nvault = "C:/v"\nignore = ".obsidian"\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert caught.value.exit_code == 2
    assert "not a list of strings" in str(caught.value)


def test_a_list_of_non_strings_is_rejected(tmp_path):
    source = write_toml(tmp_path, '[zk]\nvault = "C:/v"\nignore = [1, 2]\n')
    with pytest.raises(ZkError) as caught:
        zk_config.load_toml(source)
    assert "not a list of strings" in str(caught.value)


def test_duplicate_ignore_entries_collapse(tmp_path):
    source = write_toml(
        tmp_path, '[zk]\nvault = "C:/v"\nignore = ["a", "b", "a"]\n'
    )
    assert zk_config.load_toml(source).ignore == ("a", "b")


# --- exit-code grading (D-019) --------------------------------------------------


def _no_config(tmp_path):
    return make_dir(tmp_path / "loose"), None


def _unparseable(tmp_path):
    root = make_repo(tmp_path / "proj")
    write_toml(root, '[zk]\nvault = "C:\\Users\\you"\n')
    return root, None


def _unknown_key(tmp_path):
    root = make_repo(tmp_path / "proj")
    write_toml(root, '[zk]\nvalut = "C:/Users/you"\n')
    return root, None


def _relative_from_toml(tmp_path):
    root = make_repo(tmp_path / "proj")
    write_toml(root, '[zk]\nvault = "vault"\n')
    return root, None


def _relative_from_env(tmp_path):
    return make_dir(tmp_path / "loose"), "vault"


def _reserved_ignore(tmp_path):
    root = make_repo(tmp_path / "proj")
    vault = make_dir(tmp_path / "v")
    write_toml(root, toml_naming(vault, extra='ignore = ["private"]\n'))
    return root, None


def _missing_target(tmp_path):
    root = make_repo(tmp_path / "proj")
    write_toml(root, toml_naming(tmp_path / "gone"))
    return root, None


def _file_target(tmp_path):
    root = make_repo(tmp_path / "proj")
    target = tmp_path / "vault"
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("not a vault\n")
    write_toml(root, toml_naming(target))
    return root, None


@pytest.mark.parametrize(
    "build",
    [
        _no_config,
        _unparseable,
        _unknown_key,
        _relative_from_toml,
        _relative_from_env,
        _reserved_ignore,
        _missing_target,
        _file_target,
    ],
    ids=lambda fn: fn.__name__.strip("_"),
)
def test_every_config_failure_grades_2(tmp_path, build):
    """No condition in this layer grades 1: the same command, unchanged, would
    fail identically for every possible invocation (D-019's tiebreak)."""
    cwd, env_value = build(tmp_path)
    env = {} if env_value is None else {ENV_VAR: env_value}
    with pytest.raises(ZkError) as caught:
        zk_config.resolve_vault(env=env, cwd=cwd)
    assert caught.value.exit_code == 2
    assert str(caught.value).startswith("zk: ")


def test_a_resolved_vault_grades_0_end_to_end_through_zk_toml(
    tmp_path, monkeypatch, capsys
):
    root = make_repo(tmp_path / "proj")
    vault = make_dir(tmp_path / "vault")
    source = write_toml(root, toml_naming(vault))
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.chdir(make_dir(root / "scripts"))

    assert zk_config.main([]) == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == vault.resolve().as_posix()
    assert captured.err.strip() == (
        f"zk: vault {vault.resolve().as_posix()}  (from {source.resolve().as_posix()})"
    )


# --- path shapes: Windows and POSIX (AC-7) --------------------------------------


@pytest.mark.skipif(sys.platform != "win32", reason="drive letters are Windows")
def test_a_drive_letter_path_is_absolute_on_windows(tmp_path):
    with pytest.raises(ZkError) as caught:
        resolve("C:/zk-no-such-directory-T02")
    assert "does not exist" in str(caught.value)
    assert "not absolute" not in str(caught.value)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX has no drive letters")
def test_a_drive_letter_path_is_not_absolute_on_posix():
    """Divergent input, not divergent behaviour: on POSIX `C:/…` is a relative
    path whose first segment happens to be named `C:`."""
    with pytest.raises(ZkError) as caught:
        resolve("C:/Users/you/vault")
    assert "not absolute" in str(caught.value)


def test_a_unc_path_is_never_rejected_as_relative():
    """`//server/share/vault` is absolute on both platforms, so the failure must
    be "does not exist" and never "not absolute"."""
    assert Path("//server/share/zk-no-such-share-T02").is_absolute()
    with pytest.raises(ZkError) as caught:
        resolve("//server/share/zk-no-such-share-T02")
    assert "not absolute" not in str(caught.value)


def test_a_windows_style_vault_value_round_trips_through_the_parser(tmp_path):
    source = write_toml(tmp_path, "[zk]\nvault = 'C:\\Users\\you\\OneDrive\\vault'\n")
    assert zk_config.load_toml(source).vault == "C:\\Users\\you\\OneDrive\\vault"


# --- the committed example (D-006, §1) ------------------------------------------


def test_the_example_file_exists_at_the_repo_root():
    assert EXAMPLE.is_file()


def test_the_example_opens_with_the_required_line():
    first = EXAMPLE.read_text(encoding="utf-8").splitlines()[0]
    assert first == "# Copy to zk.toml and edit — this file is never read."


def test_the_example_parses_and_names_an_absolute_forward_slash_vault():
    data = tomllib.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert set(data) == {"zk"}
    vault = data["zk"]["vault"]
    assert "\\" not in vault
    assert vault.startswith("C:/")


def test_the_example_carries_a_commented_ignore_line():
    """P-12: the line is present but inert, so uncommenting is the whole edit."""
    text = EXAMPLE.read_text(encoding="utf-8")
    assert "# ignore = [" in text
    assert "\nignore = [" not in text


def test_uncommenting_the_example_ignore_line_yields_a_valid_config(tmp_path):
    text = EXAMPLE.read_text(encoding="utf-8").replace("# ignore = [", "ignore = [")
    source = write_toml(tmp_path, text)
    assert zk_config.load_toml(source).ignore == (".obsidian", "attachments")


def test_zk_toml_is_gitignored():
    lines = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "zk.toml" in lines
    assert "zk.toml.example" not in lines
