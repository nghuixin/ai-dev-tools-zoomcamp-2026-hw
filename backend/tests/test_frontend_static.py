from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import mount_frontend


def test_backend_serves_frontend_without_shadowing_api(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>Mini Kanban</title>")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("export default 1")

    application = FastAPI()

    @application.get("/boards")
    def list_boards():
        return [{"name": "Workshop"}]

    assert mount_frontend(application, tmp_path) is True
    client = TestClient(application)

    home = client.get("/")
    assert home.status_code == 200
    assert "Mini Kanban" in home.text
    assert client.get("/assets/app.js").text == "export default 1"
    assert client.get("/boards").json() == [{"name": "Workshop"}]


def test_mount_skipped_when_frontend_is_missing(tmp_path):
    application = FastAPI()
    assert mount_frontend(application, tmp_path) is False
    assert TestClient(application).get("/").status_code == 404
