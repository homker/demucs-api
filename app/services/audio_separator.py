import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioSeparator:
    """音频分离服务，负责调用Demucs进行音频分离处理"""
    
    def __init__(self, app=None):
        self.app = app
        self.default_model = None
        self.default_segment = None
        self.other_default_segment = None
        self.default_mp3_bitrate = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        self.app = app
        self.default_model = app.config.get('DEFAULT_MODEL', 'htdemucs')
        self.default_segment = app.config.get('DEFAULT_SEGMENT', 7)
        self.other_default_segment = app.config.get('OTHER_DEFAULT_SEGMENT', 10)
        self.default_mp3_bitrate = app.config.get('DEFAULT_MP3_BITRATE', 320)
    
    def separate_audio(self, file_path, model_name=None, two_stems=None, segment=None, mp3=False, mp3_bitrate=None, output_path=None):
        """
        分离音频文件
        
        Parameters:
        - file_path: 音频文件路径
        - model_name: 使用的模型名称
        - two_stems: 分为两个音轨的模式（vocals, drums, bass, other）
        - segment: 分段长度（秒）
        - mp3: 是否输出MP3格式
        - mp3_bitrate: MP3比特率
        - output_path: 输出路径
        
        Returns:
        - (bool, str, str): (成功标志, 模型名称, 分离结果目录)
        """
        try:
            # 使用默认值
            if model_name is None:
                model_name = self.default_model
                
            # 根据模型设置默认分段长度
            if segment is None:
                segment = str(self.default_segment if 'htdemucs' in model_name else self.other_default_segment)
            else:
                segment = str(segment)
            
            if mp3_bitrate is None:
                mp3_bitrate = str(self.default_mp3_bitrate)
            else:
                mp3_bitrate = str(mp3_bitrate)
            
            # 构建Demucs命令参数
            cmd_args = ['--device', 'cpu', '-n', model_name, '--segment', segment]
            
            if two_stems:
                cmd_args.append('--two-stems')
                cmd_args.append(two_stems)
            
            if mp3:
                cmd_args.append('--mp3')
                cmd_args.append('--mp3-bitrate')
                cmd_args.append(mp3_bitrate)
            
            cmd_args.append(file_path)
            
            # 设置输出路径环境变量
            if output_path:
                os.environ["DEMUCS_OUTPUT"] = output_path
            
            logger.info(f"开始分离音频，参数: {' '.join(cmd_args)}")
            
            # 调用Demucs进行分离
            import demucs.separate
            demucs.separate.main(cmd_args)
            
            # 分离完成后，查找输出文件夹
            separated_dir = os.path.join(os.getcwd(), 'separated')
            logger.info(f"查找分离结果目录: {separated_dir}")
            
            if not os.path.exists(separated_dir):
                logger.error(f"找不到分离结果目录: {separated_dir}")
                return False, model_name, None
                
            model_output_dir = os.path.join(separated_dir, model_name)
            logger.info(f"模型输出目录: {model_output_dir}")
            
            if not os.path.exists(model_output_dir):
                logger.error(f"找不到模型输出目录: {model_output_dir}")
                return False, model_name, None
            
            # 返回成功结果
            return True, model_name, model_output_dir
            
        except Exception as e:
            logger.error(f"分离音频时出错: {str(e)}", exc_info=True)
            return False, model_name, None
    
    def find_track_output_dir(self, model_output_dir, filename):
        """查找音频文件对应的输出目录"""
        try:
            # 尝试找到音频文件对应的目录
            filename_without_ext = os.path.splitext(filename)[0]
            logger.info(f"查找音频文件名(不含扩展名): {filename_without_ext}")
            
            # 列出所有可能的候选目录
            all_dirs = os.listdir(model_output_dir)
            logger.info(f"模型输出目录中的所有子目录: {all_dirs}")
            
            # 查找匹配的目录
            track_output_dir = None
            for dir_name in all_dirs:
                if filename_without_ext.lower() in dir_name.lower():
                    track_output_dir = os.path.join(model_output_dir, dir_name)
                    logger.info(f"找到匹配的音轨输出目录: {track_output_dir}")
                    break
                    
            # 如果找不到精确匹配，使用第一个目录（假设只处理一个文件）
            if not track_output_dir and len(all_dirs) > 0:
                track_output_dir = os.path.join(model_output_dir, all_dirs[0])
                logger.info(f"未找到精确匹配，使用第一个目录: {track_output_dir}")
                
            if not track_output_dir or not os.path.exists(track_output_dir):
                logger.error(f"找不到音轨输出目录")
                return None
            
            return track_output_dir
            
        except Exception as e:
            logger.error(f"查找音轨输出目录时出错: {str(e)}", exc_info=True)
            return None 