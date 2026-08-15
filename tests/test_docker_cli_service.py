from __future__ import annotations

import os

import services.docker_cli_service as docker_cli


def test_native_docker_preferred(monkeypatch):
    def fake_which(name: str):
        if name == "docker":
            return "/usr/bin/docker"
        return None

    monkeypatch.setattr(docker_cli.shutil, "which", fake_which)
    assert docker_cli.docker_prefix() == ["/usr/bin/docker"]


def test_windows_wsl_fallback(monkeypatch):
    def fake_which(name: str):
        if name == "docker":
            return None
        if name in {"wsl", "wsl.exe"}:
            return r"C:\Windows\System32\wsl.exe"
        return None

    monkeypatch.setattr(docker_cli.shutil, "which", fake_which)
    monkeypatch.setattr(docker_cli.os, "name", "nt", raising=False)

    assert docker_cli.docker_prefix() == [
        r"C:\Windows\System32\wsl.exe",
        "docker",
    ]


def test_unavailable_raises(monkeypatch):
    monkeypatch.setattr(docker_cli.shutil, "which", lambda _name: None)
    monkeypatch.setattr(docker_cli.os, "name", "posix", raising=False)

    try:
        docker_cli.docker_prefix()
    except docker_cli.DockerCliUnavailable:
        pass
    else:
        raise AssertionError("DockerCliUnavailable was not raised")
