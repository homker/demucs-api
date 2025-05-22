#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的Demucs音频分离功能

这个脚本演示了如何修复demucs中"not enough values to unpack (expected 3, got 2)"错误，
通过确保输入张量具有正确的batch维度 [batch, channels, length]。
"""

import os
import sys
import torch
import logging
import argparse
from pathlib import Path

# 设置基本日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 添加项目根目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

# 导入Demucs相关模块
try:
    from demucs import pretrained
    from demucs.apply import apply_model
    from demucs.audio import AudioFile, save_audio
except ImportError:
    logger.error("无法导入demucs模块。请确保已安装: pip install demucs")
    sys.exit(1)

def process_audio(input_file, output_dir, model_name="htdemucs", device="cpu", debug=False):
    """
    处理音频文件并分离音轨
    
    参数:
        input_file: 输入音频文件路径
        output_dir: 输出目录
        model_name: 模型名称
        device: 设备 (cpu/cuda)
        debug: 是否输出调试信息
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 配置参数
    sample_rate = 44100
    channels = 2
    shifts = 1  # 使用更多shifts可提高质量但增加处理时间
    split = True  # 对于长音频使用拆分处理
    overlap = 0.25  # 拆分重叠率
    
    # 打印参数
    if debug:
        logger.info(f"Processing: {input_file}")
        logger.info(f"Model: {model_name}")
        logger.info(f"Device: {device}")
    
    # 加载模型
    logger.info("Loading model...")
    model = pretrained.get_model(model_name)
    model.to(device)
    
    # 加载音频
    logger.info("Loading audio...")
    wav = AudioFile(input_file).read(
        streams=0,
        samplerate=sample_rate,
        channels=channels
    )
    
    # 获取基本文件名(不含扩展名)
    basename = os.path.basename(input_file).rsplit(".", 1)[0]
    
    try:
        # 修复解包错误: 确保输入张量有批次维度 [batch, channels, length]
        if len(wav.shape) == 2:  # [channels, length]
            input_wav = wav.to(device).unsqueeze(0)  # 添加batch维度
            if debug:
                logger.info(f"添加batch维度，新形状: {input_wav.shape}")
        else:
            input_wav = wav.to(device)
        
        # 应用模型
        logger.info("Applying model...")
        sources = apply_model(
            model=model,
            mix=input_wav,
            shifts=shifts,
            split=split,
            overlap=overlap,
            progress=True,
            device=device
        )
        
        # 将结果移回CPU
        sources = sources.cpu()
        
        # 如果结果有四个维度 [batch, sources, channels, time]，移除batch维度
        if sources.dim() == 4 and sources.shape[0] == 1:
            sources = sources.squeeze(0)  # 移除batch维度
            if debug:
                logger.info(f"移除batch维度，最终形状: {sources.shape}")
        
        # 获取源轨道名称
        source_names = model.sources
        
        # 保存每个分离的轨道
        logger.info("Saving separated tracks...")
        for i, source_name in enumerate(source_names):
            source_path = os.path.join(output_dir, f"fixed_test_{source_name}.wav")
            
            # 使用正确的参数名称: samplerate (而非sample_rate)
            save_audio(sources[i], source_path, samplerate=sample_rate)
            logger.info(f"Saved {source_name} to {source_path}")
        
        return True, "处理成功"
    
    except Exception as e:
        logger.error(f"处理过程中出错: {str(e)}")
        return False, str(e)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试修复后的Demucs音频分离")
    parser.add_argument("--input", "-i", type=str, default=os.path.join(SCRIPT_DIR, "test.mp3"),
                        help="输入音频文件路径")
    parser.add_argument("--output", "-o", type=str, default=os.path.join(SCRIPT_DIR, "output"),
                        help="输出目录")
    parser.add_argument("--model", "-m", type=str, default="htdemucs",
                        help="Demucs模型名称")
    parser.add_argument("--device", "-d", type=str, default="cpu",
                        choices=["cpu", "cuda"], help="处理设备")
    parser.add_argument("--debug", action="store_true", help="输出调试信息")
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.isfile(args.input):
        logger.error(f"输入文件不存在: {args.input}")
        return 1
    
    # 处理音频
    success, message = process_audio(
        args.input, 
        args.output, 
        args.model, 
        args.device, 
        args.debug
    )
    
    if success:
        logger.info("处理成功完成!")
        return 0
    else:
        logger.error(f"处理失败: {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 