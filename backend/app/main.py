from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.deps import store
from app.openapi_contract import build_openapi
from app.routers import boards, cards, columns


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not store.boards:
        store.seed()
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


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0]
    location = " ".join(str(part) for part in first.get("loc", []) if part != "body")
    message = first.get("msg", "Invalid request")
    detail = f"{location}: {message}" if location else message
    return JSONResponse(status_code=400, content={"detail": detail})
