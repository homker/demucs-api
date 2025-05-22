import os
import logging
from flask import Flask

from app import routes
from app.config import Config
from app.services.audio_separator import AudioSeparator
from app.services.file_manager import FileManager

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Configure logging
    configure_logging(app)
    
    # Initialize services
    init_services(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Add error handlers
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