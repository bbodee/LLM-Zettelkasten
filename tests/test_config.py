"""`zk_config.py` — resolution, normalization, the banner, and the exit-2 posture.

SPEC §1, §11 · D-006, D-014, D-016, D-018, D-019.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

import zk_config
from zk_config import ENV_VAR, VaultConfig, ZkError


def resolve(path_value=None, **kwargs):
    env = {} if path_value is None else {ENV_VAR: str(path_value)}
    return zk_config.resolve_vault(env=env, **kwargs)


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


def test_main_reports_and_returns_2_when_unconfigured(monkeypatch, capsys):
    monkeypatch.delenv(ENV_VAR, raising=False)
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
