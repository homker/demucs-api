import logging
from flask import Blueprint, render_template, current_app, redirect, url_for

from app.utils.helpers import create_success_response

logger = logging.getLogger(__name__)

# 创建蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@main_bp.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok'}

def init_app(app):
    """Initialize main routes"""
    app.register_blueprint(main_bp)
    app.logger.info("Main routes initialized") 