import logging
from flask import Blueprint, render_template, current_app, redirect, url_for

from app.utils.helpers import create_success_response

logger = logging.getLogger(__name__)

# 创建蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main page"""
    base_url = current_app.config.get('BASE_URL', '')
    return render_template('index.html', base_url=base_url)

@main_bp.route('/health')
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'demucs-audio-separator'
    }

@main_bp.route('/test')
def test_redirect():
    """Redirect /test to /test/mcp"""
    return redirect(url_for('mcp_test'))

def init_app(app):
    """Initialize main routes"""
    app.register_blueprint(main_bp)
    app.logger.info("Main routes initialized") 