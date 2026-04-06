import os

from flask import Flask
from flask_cors import CORS

from config import Config
from models import db
from routes import register_blueprints
from scheduler import init_scheduler


def create_app():
    """创建 Flask 应用实例。"""
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    CORS(app)
    db.init_app(app)
    register_blueprints(app)

    with app.app_context():
        db.create_all()

    init_scheduler(app)
    return app


app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
