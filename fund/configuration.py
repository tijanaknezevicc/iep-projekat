import os

class Configuration:
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-key-change-in-production")

MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "fund")
MONGO_USERNAME = os.environ.get("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD", "example")

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

GANACHE_URL = os.environ.get("GANACHE_URL", "http://localhost:8545")