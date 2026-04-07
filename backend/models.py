from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class File(db.Model):
    """文件池记录。"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    size = db.Column(db.BigInteger, default=0)
    mime_type = db.Column(db.String(128))
    is_link = db.Column(db.Boolean, default=False)
    url = db.Column(db.Text)
    cos_status = db.Column(db.String(16), default=None)  # pending / done / failed / None
    status = db.Column(db.String(16), default='alive')
    expire_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
