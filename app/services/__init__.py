from app.services.file_manager import FileManager
from app.services.audio_separator import AudioSeparator

def init_services(app):
    """初始化所有服务"""
    # 文件管理服务
    app.file_manager = FileManager(app)
    
    # 音频分离服务
    app.audio_separator = AudioSeparator(app) 