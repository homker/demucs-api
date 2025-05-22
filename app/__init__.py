from app.factory import create_app
from app.config import get_config

__all__ = ['create_app']

# Default application instance for direct import
app = create_app(get_config()) 