"""Offline/local HyperFrames availability regression tests (no downloads)."""

from __future__ import annotations

import subprocess

from tools.video.hyperframes_compose import HyperFramesCompose


def test_locally_verified_doctor_skips_npm_registry(monkeypatch):
    cls = HyperFramesCompose
    monkeypatch.setattr(cls, "_npm_resolve_cache", None)
    monkeypatch.setattr(cls, "_cli_probe_cache", None)
    monkeypatch.setattr(cls, "_verified_local_command", None)
    calls = []

    def which(name):
        return {"npx": "npx", "npm": "npm", "hyperframes": "hyperframes"}.get(name)

    def run(args, **kwargs):
        calls.append(args)
        if args == ["hyperframes", "doctor", "--json"]:
            return subprocess.CompletedProcess(args, 0, '{"status":"ok"}', "")
        if args == ["hyperframes", "check"]:
            return subprocess.CompletedProcess(args, 0, "", "")
        raise AssertionError(f"unexpected command (especially npm registry): {args}")

    monkeypatch.setattr("tools.video.hyperframes_compose.shutil.which", which)
    monkeypatch.setattr("tools.video.hyperframes_compose.subprocess.run", run)

    result = cls._resolve_npm_package()
    assert result["version"] == "verified-local-cli"
    assert cls._probe_cli() == {"status": "ok"}
    result = cls()._run_hf(["check"], cwd=None, timeout=30, check=False)
    assert result.returncode == 0
    assert calls == [
        ["hyperframes", "doctor", "--json"],
        ["hyperframes", "check"],
    ]


def test_unusable_local_cli_keeps_existing_registry_fallback(monkeypatch):
    cls = HyperFramesCompose
    monkeypatch.setattr(cls, "_npm_resolve_cache", None)
    monkeypatch.setattr(cls, "_cli_probe_cache", None)
    monkeypatch.setattr(cls, "_verified_local_command", None)
    calls = []

    def which(name):
        return {"npx": "npx", "npm": "npm"}.get(name)

    def run(args, **kwargs):
        calls.append(args)
        if "--offline" in args:
            return subprocess.CompletedProcess(args, 1, "", "not cached")
        if args == ["npm", "view", "hyperframes", "version"]:
            return subprocess.CompletedProcess(args, 0, "0.8.185\n", "")
        raise AssertionError(args)

    monkeypatch.setattr("tools.video.hyperframes_compose.shutil.which", which)
    monkeypatch.setattr("tools.video.hyperframes_compose.subprocess.run", run)

    assert cls._resolve_npm_package() == {"version": "0.8.185"}
    assert len(calls) == 2
    assert "--offline" in calls[0]
    assert calls[1] == ["npm", "view", "hyperframes", "version"]
