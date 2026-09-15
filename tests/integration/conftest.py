from __future__ import annotations

import os
from collections.abc import Iterator

import httpx
import pytest

from stack import APP_PORT, compose, wait_until_ready


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    configured = os.environ.get("INTEGRATION_BASE_URL")
    if configured:
        url = configured.rstrip("/")
        wait_until_ready(url)
        yield url
        return

    compose("up", "-d", "--build")
    url = f"http://127.0.0.1:{APP_PORT}"
    try:
        wait_until_ready(url)
        yield url
    finally:
        if os.environ.get("INTEGRATION_KEEP_STACK") != "1":
            compose("down", "-v")


@pytest.fixture
def api(base_url: str) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=base_url, timeout=10) as client:
        yield client
