"""Tests sans réseau : config, résolution d'URL, en-têtes."""

import importlib
import os

import persoia_auth


def _reload_clean(monkeypatch, tmp_path):
    """Pointe la config vers un fichier temporaire et purge les env vars."""
    for var in ("PERSOIA_API_KEY", "PERSOIA_API_BASE", "PERSOIA_MODEL"):
        monkeypatch.delenv(var, raising=False)
    cfg = tmp_path / "config.env"
    monkeypatch.setenv("PERSOIA_CONFIG", str(cfg))
    importlib.reload(persoia_auth)
    return cfg


def test_resolve_api_base_prod_vs_demo():
    assert persoia_auth.resolve_api_base("persoia_sk_abc") == persoia_auth.DEFAULT_API_BASE
    assert persoia_auth.resolve_api_base("persoia_demo_sk_abc") == persoia_auth.DEMO_API_BASE
    assert persoia_auth.resolve_api_base("", "https://x.persoia.com/v1") == "https://x.persoia.com/v1"


def test_valid_api_base_rejects_spoofed_host():
    assert persoia_auth._valid_api_base("https://chat.persoia.com/v1")
    assert persoia_auth._valid_api_base("https://evil.persoia.com.attacker.tld") == ""
    assert persoia_auth._valid_api_base("http://chat.persoia.com/v1") == ""  # pas https


def test_save_then_load_roundtrip(monkeypatch, tmp_path):
    _reload_clean(monkeypatch, tmp_path)
    persoia_auth.save_config({"PERSOIA_API_KEY": "persoia_sk_xyz"})
    assert persoia_auth.load_config()["PERSOIA_API_KEY"] == "persoia_sk_xyz"
    # prod déduit du préfixe
    assert persoia_auth.api_base() == persoia_auth.DEFAULT_API_BASE


def test_env_overrides_file(monkeypatch, tmp_path):
    _reload_clean(monkeypatch, tmp_path)
    persoia_auth.save_config({"PERSOIA_API_KEY": "persoia_sk_file"})
    monkeypatch.setenv("PERSOIA_API_KEY", "persoia_sk_env")
    assert persoia_auth.load_config()["PERSOIA_API_KEY"] == "persoia_sk_env"


def test_auth_headers_includes_client(monkeypatch, tmp_path):
    _reload_clean(monkeypatch, tmp_path)
    monkeypatch.setenv("PERSOIA_API_KEY", "persoia_sk_h")
    headers = persoia_auth.auth_headers(client="scan-cartes")
    assert headers["Authorization"] == "Bearer persoia_sk_h"
    assert headers["X-Persoia-Client"] == "scan-cartes"


def test_missing_key_non_interactive_raises(monkeypatch, tmp_path):
    _reload_clean(monkeypatch, tmp_path)
    try:
        persoia_auth.get_api_key(client="x", interactive=False)
        assert False, "doit lever MissingKeyError"
    except persoia_auth.MissingKeyError:
        pass


def test_config_path_unix_default(monkeypatch, tmp_path):
    monkeypatch.delenv("PERSOIA_CONFIG", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    importlib.reload(persoia_auth)
    if os.name != "nt":
        assert persoia_auth.get_config_path() == tmp_path / "persoia" / "config.env"
