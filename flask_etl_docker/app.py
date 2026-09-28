from flask import Flask, request, jsonify
from tasks import run_etl

app = Flask(__name__)


@app.route("/run-etl", methods=["POST"])
def trigger_etl():
    param = request.json.get("param", "default")

    # Enqueue Celery task
    task = run_etl.delay(param)

    return jsonify({"task_id": task.id}), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
