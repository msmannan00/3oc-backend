from flask import jsonify
from app import app


# ========== ENDPOINT FOR TESTING IF API IS RUNNING ===========
@app.route("/api", methods=["GET"])
def check_for_run():
    return jsonify({"message": "API runs successfully"}), 201


@app.route("/api/check", methods=["GET"])
def check_for_run_2():
    return jsonify({"message": "API runs successfully"}), 201
