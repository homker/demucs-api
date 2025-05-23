import os
import logging
import uuid
import time
import subprocess
from typing import Dict, Optional, List, Tuple, Callable
import torch

try:
    from demucs import pretrained
    from demucs.apply import apply_model
    from demucs.audio import AudioFile, save_audio
except ImportError as e:
    raise ImportError(f"Demucs library not found: {e}")

logger = logging.getLogger(__name__)

class AudioSeparator:
    """Service for separating audio tracks using demucs models"""
    
    def __init__(self, config):
        self.config = config
        self.device = None
        self.models = {}
        self.models_loaded = False
        self.AudioFile = AudioFile
        self.save_audio = save_audio
    
    def initialize(self):
        """Load models on demand"""
        if not self.models_loaded:
            try:
                self.device = self._get_device()
                logger.info(f"Using device: {self.device}")
                
                # 使用正确的API
                self.models = {}
                available_models = ["htdemucs", "htdemucs_ft", "htdemucs_6s", "mdx", "mdx_q"]
                
                for model_name in available_models:
                    try:
                        model = pretrained.get_model(model_name)
                        self.models[model_name] = model
                        logger.info(f"Successfully loaded model: {model_name}")
                    except Exception as e:
                        logger.warning(f"Failed to load model {model_name}: {e}")
                
                if not self.models:
                    raise RuntimeError("No models could be loaded")
                
                self.models_loaded = True
                logger.info(f"Loaded {len(self.models)} models")
                
            except Exception as e:
                logger.error(f"Failed to initialize AudioSeparator: {e}")
                raise
    
    def _get_device(self) -> str:
        """Determine the best available device for processing"""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
    
    def _get_model(self, model_name: str):
        """Get a specific demucs model"""
        self.initialize()
        
        if model_name == "all":
            return list(self.models.values())
            
        if model_name in self.models:
            model = self.models[model_name]
            # 确保返回的是列表，方便后续统一处理
            return [model]
        
        available_models = list(self.models.keys())
        logger.error(f"Model {model_name} not found. Available models: {available_models}")
        raise ValueError(f"Model {model_name} not found. Available models: {available_models}")
    
    # 自定义apply_model包装函数，添加进度报告
    def _apply_model_with_progress(self, model, mix, shifts, split, overlap, progress, device, job_id, progress_callback, model_name, base_progress=10, max_progress=95):
        """包装apply_model函数以添加进度报告"""
        # 设置初始时间
        start_time = time.time()
        last_update_time = start_time
        update_interval = 2.0  # 每2秒更新一次进度
        
        # 预计总处理时间（根据经验值）
        estimated_total_time = 60 if self.device == "cuda" else 120
        
        # 计算进度范围
        progress_range = max_progress - base_progress
        
        def progress_reporter():
            """定期报告进度"""
            nonlocal last_update_time
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            # 如果距离上次更新已经过了update_interval秒
            if current_time - last_update_time >= update_interval:
                # 计算估计进度百分比（基于经验的时间估计），范围从base_progress到max_progress
                estimated_relative_progress = min(100, int((elapsed_time / estimated_total_time) * 100))
                # 转换为全局进度值
                estimated_progress = base_progress + (progress_range * estimated_relative_progress // 100)
                
                # 更新进度
                if progress_callback:
                    # 正确设置进度百分比，并使用更清晰的状态文本
                    message = f"正在处理音频，使用模型: {model_name}"
                    status = f"正在处理音频"
                    progress_callback(estimated_progress, message, status)
                
                # 记录日志
                logger.info(f"模型处理进度: {estimated_progress}%, 已用时间: {elapsed_time:.1f}秒")
                
                # 更新上次更新时间
                last_update_time = current_time
        
        # 创建一个线程定期报告进度
        import threading
        stop_reporter = False
        
        def report_thread():
            while not stop_reporter:
                progress_reporter()
                time.sleep(1)
        
        # 启动进度报告线程
        reporter = threading.Thread(target=report_thread)
        reporter.daemon = True
        reporter.start()
        
        try:
            # 执行原始apply_model函数 - 修复：使用demucs.apply.apply_model
            result = apply_model(
                model=model, 
                mix=mix,
                shifts=shifts,
                split=split,
                overlap=overlap,
                progress=progress,
                device=device
            )
            
            # 停止进度报告线程
            stop_reporter = True
            reporter.join(timeout=1.0)
            
            # 记录总处理时间
            total_time = time.time() - start_time
            logger.info(f"模型处理完成，总用时: {total_time:.1f}秒")
            
            # 报告完成进度
            if progress_callback:
                progress_callback(max_progress, f"模型处理完成，用时: {total_time:.1f}秒", "模型处理完成")
            
            return result
            
        except Exception as e:
            # 停止进度报告线程
            stop_reporter = True
            if reporter.is_alive():
                reporter.join(timeout=1.0)
                
            # 记录错误
            logger.error(f"模型处理出错: {str(e)}")
            
            # 传递异常
            raise
    
    def separate_track(self, 
                       input_file: str, 
                       output_dir: str, 
                       model_name: str = "htdemucs", 
                       stems: List[str] = None, 
                       output_format: str = None,
                       audio_quality: str = None,
                       progress_callback: Optional[Callable] = None) -> Dict:
        """
        Separate audio tracks using demucs models
        
        Args:
            input_file: Path to input audio file
            output_dir: Output directory for separated tracks
            model_name: Name of demucs model to use
            stems: List of stems to extract (default: all available)
            output_format: Output audio format ('wav', 'mp3', 'flac')
            audio_quality: Audio quality ('low', 'medium', 'high', 'lossless')
            progress_callback: Callback function for progress updates
            
        Returns:
            Dictionary with separation results
        """
        # Set defaults
        if output_format is None:
            output_format = self.config.DEFAULT_OUTPUT_FORMAT
        if audio_quality is None:
            audio_quality = self.config.DEFAULT_AUDIO_QUALITY
        if stems is None:
            stems = ["vocals", "drums", "bass", "other"]
        
        # Validate parameters
        if output_format not in self.config.SUPPORTED_OUTPUT_FORMATS:
            raise ValueError(f"不支持的输出格式: {output_format}。支持的格式: {self.config.SUPPORTED_OUTPUT_FORMATS}")
        
        if audio_quality not in self.config.AUDIO_QUALITY_SETTINGS:
            raise ValueError(f"不支持的音频质量: {audio_quality}。支持的质量: {list(self.config.AUDIO_QUALITY_SETTINGS.keys())}")
        
        # 确保模型已加载
        self.initialize()
        
        # Generate job ID if not provided
        job_id = str(uuid.uuid4())
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Get model(s)
            models = self._get_model(model_name)
            
            # Report initial progress
            if progress_callback:
                progress_callback(0, "开始加载音频文件", "初始化")
            
            # 记录加载开始时间
            load_start_time = time.time()
            
            # Get quality settings for sample rate
            quality_settings = self.config.AUDIO_QUALITY_SETTINGS[audio_quality]
            actual_samplerate = quality_settings.get('sample_rate', self.config.SAMPLE_RATE)
            
            # Load audio file with appropriate sample rate
            wav = self.AudioFile(input_file).read(
                streams=0,
                samplerate=actual_samplerate,
                channels=self.config.CHANNELS
            )
            
            # 记录加载完成时间和文件信息
            load_time = time.time() - load_start_time
            logger.info(f"音频加载完成，耗时: {load_time:.2f}秒，形状: {wav.shape}，采样率: {actual_samplerate}")
            
            # 更新加载进度
            if progress_callback:
                progress_callback(5, f"音频加载完成，时长: {wav.shape[-1]/actual_samplerate:.1f}秒，格式: {output_format.upper()}，质量: {quality_settings['description']}", "加载完成")
            
            # Get filename without extension
            ref = os.path.basename(input_file).rsplit(".", 1)[0]
            
            # Track progress
            total_models = len(list(models))
            total_stems = len(stems)
            total_steps = total_models * total_stems
            current_step = 0
            
            # 定义各阶段的进度范围
            LOADING_PROGRESS = 0   # 起始进度
            LOADING_COMPLETE = 5   # 加载完成进度
            MODEL_START = 10       # 模型处理开始进度
            MODEL_END = 85         # 模型处理结束进度（为格式转换预留更多时间）
            SAVING_START = 85      # 保存开始进度
            SAVING_END = 100       # 保存结束进度
            
            result_files = []
            
            # Process with each model
            for i, model in enumerate(models):
                # 获取模型名称 - 处理可能没有name属性的情况
                curr_model_name = model_name
                if hasattr(model, 'name'):
                    curr_model_name = model.name
                # BagOfModels可能是模型的集合，在文件名中使用传入的名称
                
                # 计算模型进度 - 在try块外定义
                model_start_progress = MODEL_START + (i * (MODEL_END - MODEL_START) // max(1, total_models))
                
                # Report model progress
                if progress_callback:
                    progress_callback(model_start_progress, 
                                     f"开始处理模型: {curr_model_name} ({i+1}/{total_models})",
                                     f"模型处理")
                
                # Apply model - 彻底修复解包错误
                try:
                    # 确保wav有正确的批次维度 [batch, channels, length]
                    if len(wav.shape) == 2:
                        # 如果是 [channels, length]，添加batch维度
                        input_wav = wav.to(self.device).unsqueeze(0)
                        logger.info(f"添加batch维度，新形状: {input_wav.shape}")
                    else:
                        input_wav = wav.to(self.device)
                    
                    # 应用模型处理，使用包装后的函数以添加进度报告
                    sources = self._apply_model_with_progress(
                        model=model, 
                        mix=input_wav,
                        shifts=1,
                        split=True,
                        overlap=0.25,
                        progress=False,
                        device=self.device,
                        job_id=job_id,
                        progress_callback=progress_callback,
                        model_name=curr_model_name,
                        base_progress=model_start_progress,
                        max_progress=MODEL_END  # 调整为新的模型结束进度
                    )
                    
                    # 将结果移回CPU
                    sources = sources.cpu()
                    
                    # 如果源有四个维度 [batch, sources, channels, time]，移除batch维度
                    if sources.dim() == 4 and sources.shape[0] == 1:
                        sources = sources.squeeze(0)
                        logger.info(f"移除batch维度，最终形状: {sources.shape}")
                        
                except Exception as e:
                    logger.error(f"应用模型时出错: {str(e)}")
                    if progress_callback:
                        progress_callback(model_start_progress, f"模型处理错误: {str(e)}", "error")
                    raise
                
                # Get source names from model
                # BagOfModels有sources属性
                source_names = getattr(model, 'sources', ["vocals", "drums", "bass", "other"])
                
                # Process each requested stem
                for stem in stems:
                    if stem in source_names:
                        stem_idx = source_names.index(stem)
                        
                        # 更新保存进度
                        current_step += 1
                        save_progress = SAVING_START + (current_step * (SAVING_END - SAVING_START) // total_steps)
                        
                        if progress_callback:
                            progress_callback(save_progress, 
                                            f"保存 {stem} 音轨 ({curr_model_name}) - {output_format.upper()}, {quality_settings['description']}",
                                            f"保存音轨文件")
                        
                        # Create output filename (without extension)
                        filename_base = f"{ref}_{curr_model_name}_{stem}"
                        output_path_base = os.path.join(output_dir, filename_base)
                        
                        # Save stem audio with custom format and quality
                        stem_audio = sources[stem_idx]  # 直接使用源索引获取对应的音频数据
                        save_start = time.time()
                        
                        # Use new save method with format and quality support
                        final_output_path = self.save_audio_with_format(
                            stem_audio, 
                            output_path_base,
                            format_type=output_format,
                            quality=audio_quality,
                            samplerate=actual_samplerate
                        )
                        
                        save_time = time.time() - save_start
                        file_size = os.path.getsize(final_output_path) if os.path.exists(final_output_path) else 0
                        
                        logger.info(f"保存 {stem} 音轨完成，耗时: {save_time:.2f}秒，"
                                  f"文件: {final_output_path}，大小: {file_size//1024}KB，"
                                  f"格式: {output_format.upper()}，质量: {audio_quality}")
                        
                        result_files.append({
                            "path": final_output_path,
                            "name": os.path.basename(final_output_path),
                            "stem": stem,
                            "model": curr_model_name,
                            "format": output_format,
                            "quality": audio_quality,
                            "size": file_size
                        })
            
            # Report completion
            if progress_callback:
                progress_callback(SAVING_END, f"音频分离完成，格式: {output_format.upper()}，质量: {audio_quality}", "完成")
            
            # Return results
            return {
                "job_id": job_id,
                "input_file": input_file,
                "output_dir": output_dir,
                "model": model_name,
                "stems": stems,
                "output_format": output_format,
                "audio_quality": audio_quality,
                "quality_description": quality_settings['description'],
                "files": result_files
            }
            
        except Exception as e:
            logger.error(f"音频分离过程中出错: {str(e)}")
            # Report error through callback
            if progress_callback:
                progress_callback(0, f"错误: {str(e)}", "error")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available demucs models"""
        self.initialize()
        return list(self.models.keys())
    
    def separate(self, 
                 file_path: str, 
                 output_dir: str, 
                 job_id: str = None,
                 model_name: str = "htdemucs", 
                 stems: List[str] = None, 
                 progress_callback: Optional[Callable] = None) -> List[str]:
        """
        Audio separation method compatible with API routes
        
        Args:
            file_path: Path to input audio file
            output_dir: Directory to save separated tracks
            job_id: Job ID for tracking (optional)
            model_name: Name of demucs model to use
            stems: List of stems to extract
            progress_callback: Callback function for progress updates
            
        Returns:
            List of output file paths
        """
        try:
            # Call the main separation method
            result = self.separate_track(
                input_file=file_path,
                output_dir=output_dir,
                model_name=model_name,
                stems=stems,
                progress_callback=progress_callback
            )
            
            # Extract file paths from the result
            if result and 'files' in result:
                return [file_info['path'] for file_info in result['files']]
            else:
                return []
                
        except Exception as e:
            logger.error(f"音频分离失败: {str(e)}")
            raise
    
    def save_audio_with_format(self, audio_tensor, output_path, 
                              format_type='wav', quality='high', samplerate=44100):
        """
        保存音频文件，支持不同格式和质量
        
        Args:
            audio_tensor: 音频张量
            output_path: 输出路径（不含扩展名）
            format_type: 音频格式 ('wav', 'mp3', 'flac')
            quality: 音频质量 ('low', 'medium', 'high', 'lossless')
            samplerate: 采样率
        """
        try:
            # 获取质量设置
            quality_settings = self.config.AUDIO_QUALITY_SETTINGS.get(quality, 
                                                                     self.config.AUDIO_QUALITY_SETTINGS['high'])
            
            # 根据质量调整采样率
            actual_samplerate = quality_settings.get('sample_rate', samplerate)
            
            # 处理无损质量和格式的冲突
            if quality == 'lossless' and format_type == 'mp3':
                logger.warning("MP3格式不支持无损质量，降级为高质量")
                quality = 'high'
                quality_settings = self.config.AUDIO_QUALITY_SETTINGS['high']
            
            # 构建最终文件路径
            final_output_path = f"{output_path}.{format_type}"
            
            if format_type == 'wav' or (format_type == 'flac' and quality == 'lossless'):
                # 对于WAV和无损FLAC，直接使用demucs的save_audio
                self.save_audio(audio_tensor, final_output_path, samplerate=actual_samplerate)
                logger.info(f"保存{format_type.upper()}文件: {final_output_path}")
                
            elif format_type in ['mp3', 'flac']:
                # 对于MP3和有损FLAC，先保存为临时WAV，再转换
                temp_wav_path = f"{output_path}_temp.wav"
                
                try:
                    # 保存临时WAV文件
                    self.save_audio(audio_tensor, temp_wav_path, samplerate=actual_samplerate)
                    
                    # 使用ffmpeg转换格式和质量
                    self._convert_audio_format(temp_wav_path, final_output_path, 
                                             format_type, quality_settings)
                    
                    logger.info(f"保存{format_type.upper()}文件: {final_output_path} (质量: {quality})")
                    
                finally:
                    # 清理临时文件
                    if os.path.exists(temp_wav_path):
                        os.remove(temp_wav_path)
            else:
                raise ValueError(f"不支持的音频格式: {format_type}")
                
            return final_output_path
            
        except Exception as e:
            logger.error(f"保存音频文件失败: {str(e)}")
            raise
    
    def _convert_audio_format(self, input_path, output_path, format_type, quality_settings):
        """使用ffmpeg转换音频格式和质量"""
        try:
            cmd = ['ffmpeg', '-i', input_path, '-y']  # -y 覆盖现有文件
            
            if format_type == 'mp3':
                # MP3编码设置
                bitrate = quality_settings.get('mp3_bitrate', '192k')
                cmd.extend(['-codec:a', 'libmp3lame', '-b:a', bitrate])
                
            elif format_type == 'flac':
                # FLAC编码设置
                cmd.extend(['-codec:a', 'flac'])
                
            cmd.append(output_path)
            
            # 执行转换
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  check=True)
            
            logger.debug(f"ffmpeg转换成功: {' '.join(cmd)}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg转换失败: {e.stderr}")
            raise RuntimeError(f"音频格式转换失败: {e.stderr}")
        except FileNotFoundError:
            logger.error("ffmpeg未找到，请确保已安装ffmpeg")
            raise RuntimeError("ffmpeg未找到，无法转换音频格式")
    
    def get_supported_formats(self):
        """获取支持的音频格式列表"""
        return self.config.SUPPORTED_OUTPUT_FORMATS.copy()
    
    def get_quality_options(self):
        """获取音频质量选项"""
        return {k: v['description'] for k, v in self.config.AUDIO_QUALITY_SETTINGS.items()} 