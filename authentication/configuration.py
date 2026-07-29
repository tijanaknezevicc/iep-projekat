import os
from datetime import timedelta

class Configuration:
    SQLALCHEMY_DATABASE_URI   = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///database.db")
    JWT_SECRET_KEY            = os.environ.get("JWT_SECRET_KEY", "super-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(minutes = 60)