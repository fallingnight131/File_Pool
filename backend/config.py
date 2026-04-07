import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置。"""

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'filepool.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_POOL_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
    FILE_TTL = timedelta(days=7)

    # 腾讯云 COS
    COS_SECRET_ID = os.getenv('COS_SECRET_ID', '')
    COS_SECRET_KEY = os.getenv('COS_SECRET_KEY', '')
    COS_REGION = os.getenv('COS_REGION', '')
    COS_BUCKET = os.getenv('COS_BUCKET', '')
    COS_INTERNAL_ENDPOINT = os.getenv('COS_INTERNAL_ENDPOINT', '')
    COS_ENABLED = bool(COS_SECRET_ID and COS_SECRET_KEY and COS_REGION and COS_BUCKET)
