from flask import Blueprint

from .files import bp as files_bp
from .link import bp as link_bp
from .upload import bp as upload_bp


api_bp = Blueprint('api', __name__)


def register_blueprints(app):
    """注册所有 API 路由。"""
    app.register_blueprint(upload_bp)
    app.register_blueprint(link_bp)
    app.register_blueprint(files_bp)
