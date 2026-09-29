import mongomock
import pytest

import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "MongoClient", mongomock.MongoClient)
    flask_app = app_module.create_app(mongo_uri="mongodb://localhost/taskdb")
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_create_and_get_task(client):
    resp = client.post("/tasks", json={"title": "Write Terraform module"})
    assert resp.status_code == 201
    task = resp.get_json()
    assert task["title"] == "Write Terraform module"
    assert task["done"] is False

    resp = client.get(f"/tasks/{task['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == task["id"]


def test_create_task_requires_title(client):
    resp = client.post("/tasks", json={})
    assert resp.status_code == 400


def test_list_tasks(client):
    client.post("/tasks", json={"title": "a"})
    client.post("/tasks", json={"title": "b"})
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


def test_update_task(client):
    task = client.post("/tasks", json={"title": "old"}).get_json()
    resp = client.put(f"/tasks/{task['id']}", json={"done": True})
    assert resp.status_code == 200
    assert resp.get_json()["done"] is True


def test_delete_task(client):
    task = client.post("/tasks", json={"title": "temp"}).get_json()
    resp = client.delete(f"/tasks/{task['id']}")
    assert resp.status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_get_missing_task_returns_404(client):
    resp = client.get("/tasks/000000000000000000000000")
    assert resp.status_code == 404
