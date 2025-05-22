import os
import logging
import uuid
import time
from typing import Dict, Optional, List, Tuple, Callable
import torch

logger = logging.getLogger(__name__)

class AudioSeparator:
    """Service for separating audio tracks using demucs models"""
    
    def __init__(self, config):
        self.config = config
        self.models = []
        self.models_loaded = False
        self.device = self._get_device()
        logger.info(f"Using device: {self.device}")
    
    def initialize(self):
        """Load models on demand"""
        if not self.models_loaded:
            try:
                # 导入 demucs 组件
                import demucs
                from demucs import pretrained
                from demucs.apply import apply_model
                from demucs.audio import AudioFile, save_audio
                
                # Make these methods available to other methods in the class
                self.apply_model = apply_model
                self.AudioFile = AudioFile
                self.save_audio = save_audio
                
                # 使用正确的API
                self.models = {}
                # 常用模型列表
                model_names = ["htdemucs", "htdemucs_ft", "htdemucs_6s", "mdx", "mdx_q"]
                for name in model_names:
                    try:
                        self.models[name] = pretrained.get_model(name)
                        logger.info(f"Loaded model: {name}")
                    except Exception as e:
                        logger.warning(f"Could not load model {name}: {str(e)}")
                
                self.models_loaded = True
                logger.info(f"Loaded {len(self.models)} demucs models")
            except Exception as e:
                logger.error(f"Failed to load demucs models: {str(e)}")
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
            # 执行原始apply_model函数
            result = self.apply_model(
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
                       progress_callback: Optional[Callable] = None) -> Dict:
        """
        Separate an audio track into stems
        
        Args:
            input_file: Path to input audio file
            output_dir: Directory to save separated tracks
            model_name: Name of demucs model to use
            stems: List of stems to extract (vocals, drums, bass, other)
            progress_callback: Callback function for progress updates
            
        Returns:
            Dictionary with separation results
        """
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Default stems if not specified
        if stems is None or len(stems) == 0:
            stems = ["vocals", "drums", "bass", "other"]
        
        # Create unique ID for this separation job
        job_id = str(uuid.uuid4())
        
        try:
            # Get model(s)
            models = self._get_model(model_name)
            
            # Report initial progress
            if progress_callback:
                progress_callback(0, "开始加载音频文件", "初始化")
            
            # 记录加载开始时间
            load_start_time = time.time()
            
            # Load audio file
            wav = self.AudioFile(input_file).read(
                streams=0, 
                samplerate=self.config['SAMPLE_RATE'], 
                channels=self.config['CHANNELS']
            )
            
            # 记录加载完成时间和文件信息
            load_time = time.time() - load_start_time
            logger.info(f"音频加载完成，耗时: {load_time:.2f}秒，形状: {wav.shape}")
            
            # 更新加载进度
            if progress_callback:
                progress_callback(5, f"音频加载完成，时长: {wav.shape[-1]/self.config['SAMPLE_RATE']:.1f}秒", "加载完成")
            
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
            MODEL_END = 90         # 模型处理结束进度
            SAVING_START = 90      # 保存开始进度
            SAVING_END = 100       # 保存结束进度
            
            result_files = []
            
            # Process with each model
            for i, model in enumerate(models):
                # 获取模型名称 - 处理可能没有name属性的情况
                curr_model_name = model_name
                if hasattr(model, 'name'):
                    curr_model_name = model.name
                # BagOfModels可能是模型的集合，在文件名中使用传入的名称
                
                # Report model progress
                if progress_callback:
                    # 确保进度值是整数
                    model_start_progress = MODEL_START + (i * (MODEL_END - MODEL_START) // max(1, total_models - 1))
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
                        max_progress=90  # 预留5%给保存音轨文件
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
                        if progress_callback:
                            save_progress = SAVING_START + (current_step * (SAVING_END - SAVING_START) // total_steps)
                            progress_callback(save_progress, 
                                            f"保存 {stem} 音轨 ({curr_model_name})",
                                            f"保存音轨文件")
                        
                        # Create output filename
                        filename = f"{ref}_{curr_model_name}_{stem}.wav"
                        output_path = os.path.join(output_dir, filename)
                        
                        # Save stem audio - 修复索引问题
                        stem_audio = sources[stem_idx]  # 直接使用源索引获取对应的音频数据
                        save_start = time.time()
                        self.save_audio(stem_audio, 
                                        output_path, 
                                        samplerate=self.config['SAMPLE_RATE'])
                        logger.info(f"保存 {stem} 音轨完成，耗时: {time.time() - save_start:.2f}秒，文件: {output_path}")
                        
                        result_files.append({
                            "path": output_path,
                            "name": filename,
                            "stem": stem,
                            "model": curr_model_name
                        })
            
            # Report completion
            if progress_callback:
                progress_callback(SAVING_END, "音频分离完成", "完成")
            
            # Return results
            return {
                "job_id": job_id,
                "input_file": input_file,
                "output_dir": output_dir,
                "model": model_name,
                "stems": stems,
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