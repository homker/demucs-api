from app.routes import main, api, mcp

def init_app(app):
    """Initialize all route blueprints"""
    # Register main routes
    main.init_app(app)
    
    # Register API routes
    api.init_app(app)
    
    # Register MCP routes
    app.register_blueprint(mcp.mcp_bp)
    app.logger.info("Standard MCP routes initialized") 