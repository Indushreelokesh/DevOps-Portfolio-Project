"""
DevOps Portfolio Project — Task Tracker API
A small Flask + MongoDB CRUD service, deliberately simple.
The point of this project is the pipeline/infrastructure around it,
not the app logic — so keep this file boring and stable.
"""
import os
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
from pymongo import MongoClient
from pymongo.errors import PyMongoError

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/taskdb")


def create_app(mongo_uri: str = MONGO_URI) -> Flask:
    app = Flask(__name__)

    # /metrics endpoint for Prometheus — used in Week 4 of the prep plan
    metrics = PrometheusMetrics(app)
    metrics.info("app_info", "Task Tracker API", version="1.0.0")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    db = client.get_default_database()
    tasks = db.tasks

    # ---------- Health endpoints (used by k8s liveness/readiness probes) ----------
    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.get("/ready")
    def ready():
        try:
            client.admin.command("ping")
            return jsonify(status="ready"), 200
        except PyMongoError:
            return jsonify(status="not-ready"), 503

    # ---------- Task CRUD ----------
    def serialize(task) -> dict:
        return {
            "id": str(task["_id"]),
            "title": task["title"],
            "done": task.get("done", False),
            "created_at": task.get("created_at"),
        }

    @app.get("/tasks")
    def list_tasks():
        return jsonify([serialize(t) for t in tasks.find()]), 200

    @app.post("/tasks")
    def create_task():
        body = request.get_json(silent=True) or {}
        title = body.get("title")
        if not title:
            return jsonify(error="'title' is required"), 400
        doc = {
            "title": title,
            "done": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = tasks.insert_one(doc)
        doc["_id"] = result.inserted_id
        return jsonify(serialize(doc)), 201

    @app.get("/tasks/<task_id>")
    def get_task(task_id):
        task = _find_or_404(task_id)
        if task is None:
            return jsonify(error="not found"), 404
        return jsonify(serialize(task)), 200

    @app.put("/tasks/<task_id>")
    def update_task(task_id):
        try:
            oid = ObjectId(task_id)
        except InvalidId:
            return jsonify(error="invalid id"), 400
        body = request.get_json(silent=True) or {}
        update = {k: v for k, v in body.items() if k in ("title", "done")}
        if not update:
            return jsonify(error="nothing to update"), 400
        result = tasks.find_one_and_update({"_id": oid}, {"$set": update})
        if result is None:
            return jsonify(error="not found"), 404
        return jsonify(serialize(tasks.find_one({"_id": oid}))), 200

    @app.delete("/tasks/<task_id>")
    def delete_task(task_id):
        try:
            oid = ObjectId(task_id)
        except InvalidId:
            return jsonify(error="invalid id"), 400
        result = tasks.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return jsonify(error="not found"), 404
        return "", 204

    def _find_or_404(task_id):
        try:
            oid = ObjectId(task_id)
        except InvalidId:
            return None
        return tasks.find_one({"_id": oid})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
