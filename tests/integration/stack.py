from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
PROJECT = os.environ.get("INTEGRATION_COMPOSE_PROJECT", "kanban-it")
APP_PORT = os.environ.get("INTEGRATION_APP_PORT", "18091")
POSTGRES_PORT = os.environ.get("INTEGRATION_POSTGRES_PORT", "15432")


def compose_env() -> dict[str, str]:
    env = os.environ.copy()
    env["APP_PORT"] = APP_PORT
    env["POSTGRES_PORT"] = POSTGRES_PORT
    return env


def compose(*args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "-p", PROJECT, *args],
        cwd=REPO_ROOT,
        env=compose_env(),
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"docker compose {' '.join(args)} failed:\n{result.stderr or result.stdout}"
        )
    return result


def wait_until_ready(base_url: str, timeout: float = 240) -> None:
    deadline = time.time() + timeout
    last_error = "no attempt yet"
    while time.time() < deadline:
        try:
            response = httpx.get(f"{base_url}/health", timeout=2)
            if response.status_code < 500:
                return
            last_error = f"HTTP {response.status_code}"
        except httpx.HTTPError as exc:
            last_error = str(exc)
        time.sleep(1)
    raise RuntimeError(f"Compose stack at {base_url} was not ready: {last_error}")
