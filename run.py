import os
from app import app as application
from app.config import get_config

if __name__ == '__main__':
    config = get_config()
    application.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    ) 