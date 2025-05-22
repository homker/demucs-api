import os
import logging
from flask import Flask, render_template
from dotenv import load_dotenv

from app import routes
from app.config import Config
from app.services.audio_separator import AudioSeparator
from app.services.file_manager import FileManager

# 加载环境变量
load_dotenv()

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    # Create Flask app
    app = Flask(__name__)
    
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
    # Create service instances
    app.file_manager = FileManager(app.config)
    app.audio_separator = AudioSeparator(app.config)
    
    app.logger.info("Application services initialized")

def register_blueprints(app):
    """Register Flask blueprints"""
    # Import and register routes from routes module
    routes.init_app(app)
    
    # 主页路由
    @app.route('/')
    def index():
        # 获取BASE_URL环境变量传递给模板
        base_url = app.config.get('BASE_URL', '')
        return render_template('index.html', base_url=base_url)
    
    # 调试页面路由
    @app.route('/debug')
    def debug():
        return render_template('debug.html')
        
    app.logger.info("Main routes initialized")
    
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