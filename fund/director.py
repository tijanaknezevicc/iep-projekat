import json
import uuid

from flask import Flask, jsonify, request
from configuration import MONGO_DB_NAME, Configuration
from connections import create_mongo_client, create_redis_client
from datetime import datetime, timezone

from flask_jwt_extended import JWTManager

from bson import ObjectId
from bson.errors import InvalidId

from decorators import role_check

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

client = create_mongo_client()

database = client[MONGO_DB_NAME]
assets = database["assets"]

redis_client = create_redis_client()

@application.route("/pending_orders", methods=["GET"])
@role_check("director")
def get_pending_orders():
    orders = []

    for key in redis_client.keys("*"):
        raw = redis_client.get(key)
        orders.append(json.loads(raw))

    return jsonify({"orders": orders}), 200

@application.route("/decision", methods=["POST"])
@role_check("director")
def decision():
    data = request.get_json(silent=True) or {}

    if "uuid" not in data or len(data["uuid"]) == 0:
        return jsonify({"message": "Field uuid is missing."}), 400

    try:
        order_id = uuid.UUID(data["uuid"])
    except ValueError:
        return jsonify({"message": "Invalid uuid."}), 400

    raw = redis_client.get(str(order_id))

    if raw is None:
        return jsonify({"message": "Invalid uuid."}), 400

    if "approved" not in data:
        return jsonify({"message": "Field approved is missing."}), 400

    if not isinstance(data["approved"], bool):
        return jsonify({"message": "Invalid decision."}), 400
  
    approved = data["approved"]
    order = json.loads(raw)

    if approved:
        if order["order_type"] == "BUY":
            assets.insert_one({
                "name": order["name"],
                "categories": order["categories"],
                "buying_price": order["buying_price"],
                "buying_date": datetime.now(timezone.utc),
                "info": order["info"],
            })
        elif order["order_type"] == "SELL":
            assets.update_one(
                {"_id": ObjectId(order["id"])},
                {"$set": {
                    "selling_price": order["selling_price"], 
                    "selling_date": datetime.now(timezone.utc)
                }}
            )

    redis_client.delete(str(order_id))

    return "", 200    

@application.route("/report", methods=["GET"])
@role_check("director")
def report():
    pipeline = [
        {"$unwind": "$categories"},
        {"$group": {
            "_id": "$categories",
            "spent": {"$sum": "$buying_price"},
            "earned": {"$sum": "$selling_price"}
        }},
        {"$project": {
            "_id": 0,
            "category": "$_id",
            "spent": 1,
            "earned": 1
        }},
        {"$sort": {
            "earned": -1,
            "spent": 1,
            "category": 1
        }}
    ]

    statistics = list(assets.aggregate(pipeline))

    return jsonify({"statistics": statistics}), 200


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5002, debug=True)