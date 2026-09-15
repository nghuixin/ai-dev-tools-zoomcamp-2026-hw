"""Integration scenarios against docker-compose.yml (Postgres + app image)."""

from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from stack import compose, wait_until_ready

pytestmark = pytest.mark.integration


def test_health_endpoint(api: httpx.Client):
    response = api.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_serves_frontend_and_api_on_same_origin(api: httpx.Client):
    home = api.get("/")
    assert home.status_code == 200
    assert "text/html" in home.headers["content-type"]
    assert "Mini Kanban" in home.text
    assert "/assets/" in home.text

    boards = api.get("/boards")
    assert boards.status_code == 200
    assert isinstance(boards.json(), list)


def test_new_board_is_seeded_and_written_to_postgres(api: httpx.Client):
    name = f"IT {uuid4().hex[:8]}"
    created = api.post("/boards", json={"name": name})
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == name
    assert [column["title"] for column in body["columns"]] == [
        "To Do",
        "In Progress",
        "Done",
    ]

    listed = api.get("/boards")
    assert any(board["id"] == body["id"] for board in listed.json())
    fetched = api.get(f"/boards/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_card_move_is_visible_to_a_second_client(api: httpx.Client, base_url: str):
    board = api.post("/boards", json={"name": f"Two session {uuid4().hex[:8]}"}).json()
    todo, doing, _done = board["columns"]
    card = api.post(
        f"/columns/{todo['id']}/cards",
        json={"title": "Seen by interviewer"},
    ).json()

    moved = api.post(
        f"/cards/{card['id']}/move",
        json={"columnId": doing["id"], "position": 0},
    )
    assert moved.status_code == 200
    assert moved.json()["columnId"] == doing["id"]

    with httpx.Client(base_url=base_url, timeout=10) as other:
        other_view = other.get(f"/boards/{board['id']}").json()
    titles = {
        column["title"]: [item["title"] for item in column["cards"]]
        for column in other_view["columns"]
    }
    assert titles["To Do"] == []
    assert titles["In Progress"] == ["Seen by interviewer"]


def test_data_survives_app_container_restart(api: httpx.Client, base_url: str):
    name = f"Persist {uuid4().hex[:8]}"
    board = api.post("/boards", json={"name": name}).json()
    todo = board["columns"][0]
    api.post(f"/columns/{todo['id']}/cards", json={"title": "Still here"})

    compose("restart", "app")
    wait_until_ready(base_url)

    after = api.get(f"/boards/{board['id']}")
    assert after.status_code == 200
    assert after.json()["name"] == name
    assert after.json()["columns"][0]["cards"][0]["title"] == "Still here"


def test_compose_stack_returns_structured_errors(api: httpx.Client):
    missing = api.get(f"/boards/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Board not found"}

    invalid = api.post("/boards", json={"name": "   "})
    assert invalid.status_code == 400
    assert isinstance(invalid.json()["detail"], str)
