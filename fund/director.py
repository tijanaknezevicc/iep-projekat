import json
import threading
import uuid
import time

from flask import Flask, jsonify, request
from configuration import GANACHE_URL, MONGO_DB_NAME, Configuration
from connections import create_mongo_client, create_redis_client
from datetime import datetime, timezone

from flask_jwt_extended import JWTManager

from bson import ObjectId
from bson.errors import InvalidId

from decorators import role_check

import solcx
from web3 import Web3

with open("solidity/voting.sol", "r") as file:
    source = file.read()

compiled = solcx.compile_source(source, output_values=["abi", "bin"], solc_version="0.8.18")

interface = compiled["<stdin>:Voting"]
abi = interface["abi"]
bytecode = interface["bin"]

web3 = Web3(Web3.HTTPProvider(GANACHE_URL))

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)

client = create_mongo_client()

database = client[MONGO_DB_NAME]
assets = database["assets"]

redis_client = create_redis_client()

active_filters = {}

stop = False
stopped = lambda: stop

@application.route("/pending_orders", methods=["GET"])
@role_check("director")
def get_pending_orders():
    orders = []

    for key in redis_client.keys("*"):
        raw = redis_client.get(key)
        orders.append(json.loads(raw))

    return jsonify({"orders": orders}), 200

# @application.route("/decision", methods=["POST"]) # no blockchain implementation
# @role_check("director")
# def decision():
#     data = request.get_json(silent=True) or {}

#     if "uuid" not in data or len(data["uuid"]) == 0:
#         return jsonify({"message": "Field uuid is missing."}), 400

#     try:
#         order_id = uuid.UUID(data["uuid"])
#     except ValueError:
#         return jsonify({"message": "Invalid uuid."}), 400

#     raw = redis_client.get(str(order_id))

#     if raw is None:
#         return jsonify({"message": "Invalid uuid."}), 400

#     if "approved" not in data:
#         return jsonify({"message": "Field approved is missing."}), 400

#     if not isinstance(data["approved"], bool):
#         return jsonify({"message": "Invalid decision."}), 400
  
#     approved = data["approved"]
#     order = json.loads(raw)

#     if approved:
#         if order["order_type"] == "BUY":
#             assets.insert_one({
#                 "name": order["name"],
#                 "categories": order["categories"],
#                 "buying_price": order["buying_price"],
#                 "buying_date": datetime.now(timezone.utc),
#                 "info": order["info"],
#             })
#         elif order["order_type"] == "SELL":
#             assets.update_one(
#                 {"_id": ObjectId(order["id"])},
#                 {"$set": {
#                     "selling_price": order["selling_price"], 
#                     "selling_date": datetime.now(timezone.utc)
#                 }}
#             )

#     redis_client.delete(str(order_id))

#     return "", 200    

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

    if "voters" not in data or len(data["voters"]) == 0:
        return jsonify({"message": "Field voters is missing."}), 400

    for voter in data["voters"]:
        if not Web3.is_address(voter):
            return jsonify({"message": f"Invalid voter address."}), 400

    if len(data["voters"]) % 2 == 0:
        return jsonify({"message": "Even number of voters."}), 400
  
    order = json.loads(raw)

    contract = web3.eth.contract(abi=abi, bytecode=bytecode)

    deploy_tx_hash = contract.constructor(data["voters"]).transact({
        "from": web3.eth.accounts[0],
    })

    receipt = web3.eth.wait_for_transaction_receipt(deploy_tx_hash)

    deployed_contract = web3.eth.contract(address=receipt.contractAddress, abi=abi)

    event_filter = deployed_contract.events.Finished.create_filter(from_block="latest")
    active_filters[receipt.contractAddress] = (event_filter, data["uuid"])

    approve_transaction = {
        "to": receipt.contractAddress,
        "data": deployed_contract.encode_abi(abi_element_identifier="approve"),
    }

    reject_transaction = {
        "to": receipt.contractAddress,
        "data": deployed_contract.encode_abi(abi_element_identifier="reject"),
    }    

    return jsonify({
        "approve_transaction": approve_transaction,
        "reject_transaction": reject_transaction
    }), 200

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

def voting_listener(stopped):
    while not stopped():
        for contract_address, (event_filter, order_id) in list(active_filters.items()):
            events = event_filter.get_new_entries()
            for event in events:
                approved = event["args"]["approved"]
                order = json.loads(redis_client.get(order_id))

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
                redis_client.delete(order_id)
                del active_filters[contract_address]

        time.sleep(1)

threading.Thread(target=voting_listener, args=(stopped,), daemon=True).start()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5002, debug=True)