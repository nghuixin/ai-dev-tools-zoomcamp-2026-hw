from app.database import database_url
from app.models import CreateBoardInput, CreateCardInput
from app.store import Store


def test_database_url_prefers_sdip_and_normalizes_postgres(monkeypatch):
    monkeypatch.setenv("SDIP_DATABASE_URL", "postgresql://sdip:sdip@localhost:5432/sdip")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_url() == "postgresql+psycopg://sdip:sdip@localhost:5432/sdip"


def test_store_survives_new_session_on_same_engine():
    first = Store()
    board = first.create_board(CreateBoardInput(name="Persist"))
    first.create_card(board.columns[0].id, CreateCardInput(title="Kept"))

    second = Store(first._session_factory)
    loaded = second.get_board(board.id)
    assert loaded.name == "Persist"
    assert loaded.columns[0].cards[0].title == "Kept"
