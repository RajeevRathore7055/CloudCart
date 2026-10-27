import os
from dotenv import load_dotenv

load_dotenv()  # local: reads .env | AWS: real environment variables are used


class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", "3306"))
    DATABASE_NAME = os.getenv("DATABASE_NAME", "cloudcart")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    AWS_REGION = os.getenv("AWS_REGION", "")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
    IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "").rstrip("/")
    COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


settings = Settings()

if not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY missing. Create a .env file (copy .env.example).")
