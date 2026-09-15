import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.deps import get_store
from app.openapi_contract import build_openapi
from app.routers import boards, cards, columns

DEFAULT_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def static_dir() -> Path:
    configured = os.environ.get("STATIC_DIR")
    return Path(configured) if configured else DEFAULT_STATIC_DIR


def mount_frontend(application: FastAPI, directory: Path | None = None) -> bool:
    """Serve the Vite build if present. Mount last so API routes keep priority."""
    root = directory if directory is not None else static_dir()
    if not root.is_dir() or not (root / "index.html").is_file():
        return False
    application.mount("/", StaticFiles(directory=root, html=True), name="frontend")
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    override = app.dependency_overrides.get(get_store)
    current = override() if override else get_store()
    if not current.list_boards():
        current.seed()
    yield


app = FastAPI(
    title="Mini Kanban API",
    version="1.0.0",
    description=(
        "Contract derived from `frontend/src/services/BoardService`. "
        "JSON field names are camelCase. No authentication in v1."
    ),
    lifespan=lifespan,
)
app.openapi = lambda: build_openapi(app)  # type: ignore[method-assign]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(boards.router)
app.include_router(columns.router)
app.include_router(cards.router)


@app.get("/health", include_in_schema=False)
def health(request: Request):
    override = request.app.dependency_overrides.get(get_store)
    store = override() if override else get_store()
    try:
        store.list_boards()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unhealthy"})
    return {"status": "ok"}


mount_frontend(app)


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0]
    location = " ".join(str(part) for part in first.get("loc", []) if part != "body")
    message = first.get("msg", "Invalid request")
    detail = f"{location}: {message}" if location else message
    return JSONResponse(status_code=400, content={"detail": detail})
