import os

class Config:
    """应用配置基类"""
    # 上传文件大小限制（200MB）
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024
    
    # 目录配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', 'outputs')
    
    # 文件保留时间（分钟）
    FILE_RETENTION_MINUTES = int(os.environ.get('FILE_RETENTION_MINUTES', 300))
    
    # Demucs 相关配置
    DEFAULT_MODEL = 'htdemucs'
    DEFAULT_SEGMENT = 7  # htdemucs 默认分段长度（秒）
    OTHER_DEFAULT_SEGMENT = 10  # 其他模型默认分段长度（秒）
    DEFAULT_MP3_BITRATE = 320


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = False
    TESTING = True
    # 测试环境可以使用更短的保留时间
    FILE_RETENTION_MINUTES = 5


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False


# 配置映射
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 根据环境变量获取配置
def get_config():
    env = os.environ.get('FLASK_ENV', 'default')
    return config_by_name[env] 