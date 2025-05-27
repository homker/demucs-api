import os
from pathlib import Path

class Config:
    """Application configuration class"""
    
    # General configuration
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-12345')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # API设置
    BASE_URL = os.environ.get('BASE_URL', '')  # API基础路径，例如/demucs
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', BASE_URL)  # Flask应用根路径
    
    # Admin settings
    ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'admin-token-12345')  # 用于管理接口认证的令牌
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # File paths
    BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__))).parent
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/demucs/uploads')
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', '/demucs/outputs')
    
    # File settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))  # 降低为100MB
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg', 'm4a', 'mp4'}
    FILE_RETENTION_MINUTES = int(os.environ.get('FILE_RETENTION_MINUTES', 30))  # 降低为30分钟
    
    # Audio processing settings - 资源限制配置
    DEFAULT_MODEL = os.environ.get('DEFAULT_MODEL', 'htdemucs')
    AVAILABLE_MODELS = ['htdemucs']  # 只支持默认模型
    SAMPLE_RATE = int(os.environ.get('SAMPLE_RATE', 22050))  # 降低采样率节省资源
    CHANNELS = int(os.environ.get('CHANNELS', 2))
    
    # Audio output settings - 资源限制配置
    DEFAULT_OUTPUT_FORMAT = os.environ.get('DEFAULT_OUTPUT_FORMAT', 'mp3')  # 默认MP3
    SUPPORTED_OUTPUT_FORMATS = ['mp3']  # 只支持MP3格式
    
    # Audio quality settings - 资源限制配置
    DEFAULT_AUDIO_QUALITY = os.environ.get('DEFAULT_AUDIO_QUALITY', 'low')  # 默认低质量
    AUDIO_QUALITY_SETTINGS = {
        'low': {
            'mp3_bitrate': '128k',
            'sample_rate': 22050,
            'description': '低质量 (128kbps, 22kHz)'
        }
    }
    
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
    UPLOAD_FOLDER = '/demucs/test_uploads'
    OUTPUT_FOLDER = '/demucs/test_outputs'


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