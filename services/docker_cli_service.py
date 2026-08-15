from __future__ import annotations

import os
import shutil
import subprocess
from typing import Sequence


class DockerCliUnavailable(RuntimeError):
    """Raised when neither native Docker CLI nor WSL Docker can be invoked."""


def docker_prefix() -> list[str]:
    """
    Return the command prefix used to invoke Docker.

    Priority:
    1. Native Docker CLI on PATH.
    2. On Windows, Docker available inside the default WSL distribution.

    This keeps the project compatible with the current development layout where
    Python/Streamlit run in Windows/PyCharm while Docker is available in WSL.
    """
    native = shutil.which("docker")
    if native:
        return [native]

    if os.name == "nt":
        wsl = shutil.which("wsl") or shutil.which("wsl.exe")
        if wsl:
            return [wsl, "docker"]

    raise DockerCliUnavailable(
        "Docker CLI is not available to this Python process. "
        "Install Docker on PATH or, on Windows, ensure WSL is installed and "
        "`wsl docker version` works."
    )


def docker_command(*args: str) -> list[str]:
    return [*docker_prefix(), *args]


def run_docker(
    args: Sequence[str],
    *,
    check: bool = False,
    capture_output: bool = False,
    text: bool = False,
    input: bytes | str | None = None,
) -> subprocess.CompletedProcess:
    command = [*docker_prefix(), *args]
    return subprocess.run(
        command,
        check=check,
        capture_output=capture_output,
        text=text,
        input=input,
    )
