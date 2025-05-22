import os
import logging
from flask import Flask

from app.config import get_config
from app.routes import register_blueprints
from app.services import init_services

def configure_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_app(config_name=None):
    """
    应用工厂函数
    
    Parameters:
    - config_name: 配置名称，可选值：development, testing, production
    
    Returns:
    - Flask应用实例
    """
    # 配置日志
    configure_logging()
    
    # 创建应用
    app = Flask(__name__)
    
    # 加载配置
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(get_config())
    
    # 确保上传和输出目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # 初始化服务
    init_services(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    return app 