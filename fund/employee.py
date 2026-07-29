import json
import uuid

from flask import Flask, jsonify, request
from configuration import MONGO_DB_NAME, Configuration
from connections import create_mongo_client, create_redis_client
from datetime import datetime

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

@application.route("/search", methods=["POST"])
@role_check("employee")
def search():

    data = request.get_json(silent=True) or {}
    query = {}

    if "name" in data:
        query["name"] = {"$regex": data["name"]}

    if "category" in data:
        query["categories"] = data["category"]

    if "buying_date" in data:
        query["buying_date"] = {"$gt": datetime.fromisoformat(data["buying_date"].replace("Z", "+00:00"))}

    if "selling_date" in data:
        query["selling_date"] = {"$lt": datetime.fromisoformat(data["selling_date"].replace("Z", "+00:00"))}

    for f in data.get("info_filters", []):
        query["info." + f["field"]] = {"$" + f["operator"]: f["value"]}

    found = assets.find(query)
    result = []

    for asset in found:
        item = {
            "id": str(asset["_id"]),
            "name": asset["name"],
            "categories": asset["categories"],
            "buying_date": asset["buying_date"].isoformat(),
            "buying_price": asset["buying_price"],
            "info": asset["info"]
        }

        if "selling_date" in asset:
            item["selling_date"] = asset["selling_date"].isoformat()
            item["selling_price"] = asset["selling_price"]

        result.append(item)

    return jsonify({"assets": result}), 200

@application.route("/create_buy_order", methods=["POST"])
@role_check("employee")
def create_buy_order():
    data = request.get_json(silent=True) or {}

    if ("name" not in data or len(data["name"]) == 0 or len(data["name"]) > 256):
        return jsonify({"message": "Field name is missing."}), 400

    required_fields = ["categories", "buying_price", "info"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Field {field} is missing."}), 400

    if len(data["categories"]) == 0:
        return jsonify({"message": "Categories list is empty."}), 400

    if not isinstance(data["buying_price"], (int, float)) or data["buying_price"] <= 0:
        return jsonify({"message": "Invalid buying price."}), 400

    order_id = str(uuid.uuid4())

    order = {
        "uuid": order_id,
        "order_type": "BUY",
        "name": data["name"],
        "categories": data["categories"],
        "info": data["info"],
        "buying_price": data["buying_price"]
    }

    redis_client.set(order_id, json.dumps(order))

    return "", 200

@application.route("/create_sell_order", methods=["POST"])
@role_check("employee")
def create_sell_order():
    data = request.get_json(silent=True) or {}

    if ("id" not in data or len(data["id"]) == 0):
        return jsonify({"message": "Field id is missing."}), 400

    if ("selling_price" not in data):
        return jsonify({"message": "Field selling_price is missing."}), 400

    try:
        object_id = ObjectId(data["id"])
    except InvalidId:
        return jsonify({"message": "Invalid id."}), 400

    if assets.find_one({"_id": object_id}) is None:
        return jsonify({"message": "Invalid id."}), 400    

    if (not isinstance(data["selling_price"], (int, float)) or data["selling_price"] <= 0):
        return jsonify({"message": "Invalid selling price."}), 400

    order_id = str(uuid.uuid4())

    order = {
        "uuid": order_id,
        "order_type": "SELL",
        "id": data["id"],
        "selling_price": data["selling_price"]
    }

    redis_client.set(order_id, json.dumps(order))

    return "", 200
       

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5001, debug=True)