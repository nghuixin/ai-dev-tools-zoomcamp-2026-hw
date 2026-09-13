from app.openapi_contract import OPERATION_DOC


def test_live_openapi_matches_error_contract(client):
    spec = client.get("/openapi.json").json()
    assert spec["info"]["title"] == "Mini Kanban API"
    assert spec["servers"] == [
        {"url": "http://localhost:8091", "description": "Local FastAPI backend"}
    ]
    assert "Error" in spec["components"]["schemas"]
    assert "HTTPValidationError" not in spec["components"]["schemas"]
    assert "ValidationError" not in spec["components"]["schemas"]
    assert spec["components"]["schemas"]["Error"]["required"] == ["detail"]

    documented = {}
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if not isinstance(op, dict) or "operationId" not in op:
                continue
            documented[op["operationId"]] = {
                "tags": op.get("tags"),
                "codes": set(op.get("responses", {})),
            }
            assert "422" not in op.get("responses", {})

    assert set(documented) == set(OPERATION_DOC)
    for operation_id, expected in OPERATION_DOC.items():
        assert documented[operation_id]["tags"] == expected["tags"]
        assert documented[operation_id]["codes"] == set(expected["codes"])


def test_validation_still_returns_400_error_model(client):
    response = client.post("/boards", json={"name": "   "})
    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)
