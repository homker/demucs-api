import os
from pathlib import Path

class Config:
    """Application configuration class"""
    
    # General configuration
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-12345')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Admin settings
    ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'admin-token-12345')  # 用于管理接口认证的令牌
    
    # File paths
    BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__))).parent
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', os.path.join(BASE_DIR, 'outputs'))
    
    # File settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500 MB
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg', 'm4a', 'mp4'}
    FILE_RETENTION_MINUTES = int(os.environ.get('FILE_RETENTION_MINUTES', 60))  # 1 hour
    
    # Audio processing settings
    DEFAULT_MODEL = os.environ.get('DEFAULT_MODEL', 'htdemucs')
    SAMPLE_RATE = int(os.environ.get('SAMPLE_RATE', 44100))
    CHANNELS = int(os.environ.get('CHANNELS', 2))
    
    # Flask server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    
    # In production, use a proper secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # Use temporary directories for tests
    UPLOAD_FOLDER = os.path.join(Config.BASE_DIR, 'test_uploads')
    OUTPUT_FOLDER = os.path.join(Config.BASE_DIR, 'test_outputs')


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Get configuration based on environment
def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, config_by_name['default']) 