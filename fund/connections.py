from pymongo import MongoClient
import redis

from configuration import MONGO_HOST, MONGO_PORT, MONGO_USERNAME, MONGO_PASSWORD, REDIS_HOST, REDIS_PORT

def create_mongo_client():
    return MongoClient(
        host=MONGO_HOST, 
        port=MONGO_PORT, 
        username=MONGO_USERNAME, 
        password=MONGO_PASSWORD, 
        authSource="admin")

def create_redis_client():
    return redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        decode_responses=True)