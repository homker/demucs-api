import os
import logging
from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv

from app import routes
from app.config import Config
from app.services.audio_separator import AudioSeparator
from app.services.file_manager import FileManager
from app.services.mcp_server import MCPServer

# 加载环境变量
load_dotenv()

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    # Create Flask app
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/mcp/*": {"origins": "*"},
        r"/api/*": {"origins": "*"}
    })
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Configure logging
    configure_logging(app)
    
    # Initialize services
    init_services(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def configure_logging(app):
    """Configure application logging"""
    log_level = app.config['LOG_LEVEL']
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(getattr(logging, log_level))
    app.logger.info(f"Logging configured at {log_level} level")

def init_services(app):
    """Initialize application services"""
    # Create config instance - 使用Config类实例而不是Flask config字典
    config_instance = Config()
    
    # Create service instances
    app.file_manager = FileManager(config_instance)
    app.audio_separator = AudioSeparator(config_instance)
    app.mcp_server = MCPServer()
    
    # Set app reference for MCP service
    app.mcp_server.set_app(app)
    
    app.logger.info("Application services initialized")

def register_blueprints(app):
    """Register Flask blueprints"""
    # Import and register routes from routes module
    routes.init_app(app)
    
    # 注册管理面板路由
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    
    # MCP测试页面路由 - 直接定义，因为它不在main_bp中
    @app.route('/test/mcp')
    def mcp_test():
        base_url = app.config.get('BASE_URL', '')
        return render_template('mcp_test.html', base_url=base_url)
        
    app.logger.info("Application blueprints registered")

def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(404)
    def not_found(error):
        from app.utils.helpers import create_error_response
        return create_error_response("Resource not found", 404)
    
    @app.errorhandler(500)
    def server_error(error):
        from app.utils.helpers import create_error_response
        return create_error_response("Internal server error", 500)
    
    app.logger.info("Error handlers registered") 