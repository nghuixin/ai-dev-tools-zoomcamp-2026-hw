"""Align generated /openapi.json with repo-root openapi.yaml."""

from __future__ import annotations

from typing import Any

from fastapi.openapi.utils import get_openapi

ERROR_RESPONSE = {
    "content": {
        "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
    }
}

# Status codes and descriptions from openapi.yaml
OPERATION_DOC: dict[str, dict[str, Any]] = {
    "listBoards": {"tags": ["boards"], "codes": {"200": "Board list"}},
    "createBoard": {
        "tags": ["boards"],
        "codes": {
            "201": "Created board with nested columns",
            "400": "Validation or business-rule error",
        },
    },
    "getBoard": {
        "tags": ["boards"],
        "codes": {"200": "Board detail", "404": "Resource not found"},
    },
    "updateBoard": {
        "tags": ["boards"],
        "codes": {
            "200": "Updated board",
            "400": "Validation or business-rule error",
            "404": "Resource not found",
        },
    },
    "deleteBoard": {
        "tags": ["boards"],
        "codes": {"204": "Deleted", "404": "Resource not found"},
    },
    "createColumn": {
        "tags": ["columns"],
        "codes": {
            "201": "Created column",
            "400": "Validation or business-rule error",
            "404": "Resource not found",
        },
    },
    "updateColumn": {
        "tags": ["columns"],
        "codes": {
            "200": "Updated column",
            "400": "Validation or business-rule error",
            "404": "Resource not found",
        },
    },
    "deleteColumn": {
        "tags": ["columns"],
        "codes": {"204": "Deleted", "404": "Resource not found"},
    },
    "createCard": {
        "tags": ["cards"],
        "codes": {
            "201": "Created card",
            "400": "Validation or business-rule error",
            "404": "Resource not found",
        },
    },
    "updateCard": {
        "tags": ["cards"],
        "codes": {
            "200": "Updated card",
            "400": "Validation or business-rule error",
            "404": "Resource not found",
        },
    },
    "moveCard": {
        "tags": ["cards"],
        "codes": {
            "200": "Moved card",
            "400": "Validation or business-rule error",
            "404": "Resource not found",
        },
    },
    "deleteCard": {
        "tags": ["cards"],
        "codes": {"204": "Deleted", "404": "Resource not found"},
    },
}


def apply_contract(schema: dict[str, Any]) -> dict[str, Any]:
    schema["servers"] = [
        {"url": "http://localhost:8091", "description": "Local FastAPI backend"}
    ]
    schema["tags"] = [
        {"name": "boards"},
        {"name": "columns"},
        {"name": "cards"},
    ]

    components = schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas["Error"] = {
        "type": "object",
        "title": "Error",
        "additionalProperties": False,
        "required": ["detail"],
        "properties": {"detail": {"type": "string", "title": "Detail"}},
    }
    schemas.pop("HTTPValidationError", None)
    schemas.pop("ValidationError", None)

    for item in schema.get("paths", {}).values():
        for op in item.values():
            if not isinstance(op, dict) or "operationId" not in op:
                continue
            doc = OPERATION_DOC.get(op["operationId"])
            if not doc:
                continue
            op["tags"] = list(doc["tags"])
            existing = op.get("responses") or {}
            rewritten: dict[str, Any] = {}
            for code, description in doc["codes"].items():
                if code in {"400", "404"}:
                    rewritten[code] = {"description": description, **ERROR_RESPONSE}
                elif code in existing:
                    kept = dict(existing[code])
                    kept["description"] = description
                    rewritten[code] = kept
                else:
                    rewritten[code] = {"description": description}
            op["responses"] = rewritten
    return schema


def build_openapi(app) -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    app.openapi_schema = apply_contract(schema)
    return app.openapi_schema
