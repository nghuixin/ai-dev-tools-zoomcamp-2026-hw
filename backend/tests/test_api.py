from uuid import uuid4


def test_seeded_board_is_listed(client):
    response = client.get("/boards")
    assert response.status_code == 200
    boards = response.json()
    assert len(boards) == 1
    assert boards[0]["name"] == "Workshop"
    assert "createdAt" in boards[0]


def test_get_board_includes_default_columns_and_cards(client):
    board_id = client.get("/boards").json()[0]["id"]
    response = client.get(f"/boards/{board_id}")
    assert response.status_code == 200
    board = response.json()
    assert [column["title"] for column in board["columns"]] == [
        "To Do",
        "In Progress",
        "Done",
    ]
    assert [card["title"] for card in board["columns"][0]["cards"]] == [
        "Write OpenAPI contract",
        "Connect frontend",
    ]
    assert board["columns"][0]["cards"][1]["description"] == "Swap mock for HTTP client"


def test_create_board_seeds_columns(client):
    response = client.post("/boards", json={"name": "  Sprint  "})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Sprint"
    assert [column["title"] for column in body["columns"]] == [
        "To Do",
        "In Progress",
        "Done",
    ]
    assert all(column["wipLimit"] is None for column in body["columns"])


def test_rename_and_delete_board(client):
    board_id = client.post("/boards", json={"name": "Temp"}).json()["id"]
    renamed = client.patch(f"/boards/{board_id}", json={"name": "Renamed"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Renamed"
    deleted = client.delete(f"/boards/{board_id}")
    assert deleted.status_code == 204
    assert client.get(f"/boards/{board_id}").status_code == 404
    assert client.get(f"/boards/{board_id}").json() == {"detail": "Board not found"}


def test_column_create_reorder_and_delete(client):
    board = client.get("/boards").json()[0]
    created = client.post(
        f"/boards/{board['id']}/columns",
        json={"title": "Review", "wipLimit": 3},
    )
    assert created.status_code == 201
    column_id = created.json()["id"]
    assert created.json()["position"] == 3
    assert created.json()["wipLimit"] == 3

    moved = client.patch(f"/columns/{column_id}", json={"position": 0})
    assert moved.status_code == 200
    board = client.get(f"/boards/{board['id']}").json()
    assert [column["title"] for column in board["columns"]][:2] == ["Review", "To Do"]

    todo_id = next(column["id"] for column in board["columns"] if column["title"] == "To Do")
    deleted = client.delete(f"/columns/{todo_id}")
    assert deleted.status_code == 204
    board = client.get(f"/boards/{board['id']}").json()
    assert all(column["title"] != "To Do" for column in board["columns"])
    assert [column["position"] for column in board["columns"]] == list(
        range(len(board["columns"]))
    )


def test_card_lifecycle_and_move(client):
    board = client.get(f"/boards/{client.get('/boards').json()[0]['id']}").json()
    todo = board["columns"][0]
    doing = board["columns"][1]
    created = client.post(
        f"/columns/{todo['id']}/cards",
        json={"title": "Ship it", "description": "tonight"},
    )
    assert created.status_code == 201
    card_id = created.json()["id"]
    assert created.json()["position"] == 2

    edited = client.patch(
        f"/cards/{card_id}",
        json={"title": "Ship it now", "description": None},
    )
    assert edited.status_code == 200
    assert edited.json()["title"] == "Ship it now"
    assert edited.json()["description"] is None

    moved = client.post(
        f"/cards/{card_id}/move",
        json={"columnId": doing["id"], "position": 0},
    )
    assert moved.status_code == 200
    assert moved.json()["columnId"] == doing["id"]
    assert moved.json()["position"] == 0

    board = client.get(f"/boards/{board['id']}").json()
    assert board["columns"][1]["cards"][0]["id"] == card_id
    assert all(card["id"] != card_id for card in board["columns"][0]["cards"])

    deleted = client.delete(f"/cards/{card_id}")
    assert deleted.status_code == 204
    board = client.get(f"/boards/{board['id']}").json()
    assert all(card["id"] != card_id for card in board["columns"][1]["cards"])


def test_validation_and_not_found(client):
    missing = uuid4()
    assert client.get(f"/boards/{missing}").status_code == 404
    assert client.post("/boards", json={"name": "   "}).status_code == 400
    board_id = client.get("/boards").json()[0]["id"]
    too_long = client.post(
        f"/boards/{board_id}/columns",
        json={"title": "x" * 61},
    )
    assert too_long.status_code == 400
    assert "detail" in too_long.json()
    assert isinstance(too_long.json()["detail"], str)


def test_column_and_card_not_found(client):
    missing = uuid4()
    assert client.patch(f"/columns/{missing}", json={"title": "Nope"}).json() == {
        "detail": "Column not found"
    }
    assert client.delete(f"/cards/{missing}").status_code == 404
    assert client.delete(f"/cards/{missing}").json() == {"detail": "Card not found"}


def test_empty_column_patch_is_400(client):
    board = client.get(f"/boards/{client.get('/boards').json()[0]['id']}").json()
    response = client.patch(f"/columns/{board['columns'][0]['id']}", json={})
    assert response.status_code == 400
    assert response.json() == {"detail": "At least one field is required"}


def test_api_has_no_auth(client):
    spec = client.get("/openapi.json").json()
    assert "securitySchemes" not in spec.get("components", {})
    assert not spec.get("security")


def test_cannot_move_card_across_boards(client):
    first = client.get("/boards").json()[0]
    second = client.post("/boards", json={"name": "Other"}).json()
    source_board = client.get(f"/boards/{first['id']}").json()
    card_id = source_board["columns"][0]["cards"][0]["id"]
    target_column = second["columns"][0]["id"]
    response = client.post(
        f"/cards/{card_id}/move",
        json={"columnId": target_column, "position": 0},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot move a card to another board"}
