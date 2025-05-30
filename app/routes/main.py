import logging
from flask import Blueprint, render_template, current_app, redirect, url_for, send_from_directory
import os

from app.utils.helpers import create_success_response

logger = logging.getLogger(__name__)

# 创建蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main page"""
    base_url = current_app.config.get('BASE_URL', '')
    return render_template('index.html', base_url=base_url)

@main_bp.route('/mcp')
def mcp_page():
    """MCP测试页面"""
    base_url = current_app.config.get('BASE_URL', '')
    return render_template('mcp_test.html', base_url=base_url)

@main_bp.route('/api-docs')
def api_docs_page():
    """API文档页面"""
    base_url = current_app.config.get('BASE_URL', '')
    return render_template('api.html', base_url=base_url)

@main_bp.route('/docs')
def docs_page():
    """使用指南页面"""
    base_url = current_app.config.get('BASE_URL', '')
    return render_template('docs.html', base_url=base_url)

@main_bp.route('/test_ui_fix.html')
def test_ui_fix():
    """测试UI修复页面"""
    # 返回项目根目录下的test_ui_fix.html文件
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return send_from_directory(base_dir, 'test_ui_fix.html')

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