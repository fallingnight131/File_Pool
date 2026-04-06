import os
from datetime import timedelta


class Config:
    """应用配置。"""

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'filepool.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_POOL_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
    FILE_TTL = timedelta(days=7)
