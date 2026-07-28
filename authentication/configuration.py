from datetime import timedelta

class Configuration:
    SQLALCHEMY_DATABASE_URI   = "sqlite:///database.db" 
    JWT_SECRET_KEY            = "super-secret-key-change-in-production"
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(minutes = 60)
    # JWT_REFRESH_TOKEN_EXPIRES = timedelta ( days = 30 )