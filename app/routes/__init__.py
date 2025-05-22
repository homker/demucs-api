from app.routes.main import main_bp
from app.routes.api import api_bp

def register_blueprints(app):
    """注册所有蓝图"""
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp) 