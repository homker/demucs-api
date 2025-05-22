from app.routes import main, api

def init_app(app):
    """Initialize all route blueprints"""
    # Register main routes
    main.init_app(app)
    
    # Register API routes
    api.init_app(app) 