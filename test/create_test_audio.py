#!/usr/bin/env python3
"""创建测试音频文件"""

import wave
import struct
import os
import math

def create_test_audio():
    """创建一个简单的测试音频文件"""
    sample_rate = 44100
    duration = 1  # 1秒
    frequency = 440  # A音符
    
    # 创建fixtures目录
    os.makedirs('fixtures', exist_ok=True)
    
    # 生成正弦波数据
    samples = []
    for i in range(int(sample_rate * duration)):
        # 生成正弦波
        t = i / sample_rate
        value = int(32767 * 0.1 * math.sin(2 * math.pi * frequency * t))
        samples.append(struct.pack('<h', value))
    
    # 写入WAV文件
    wav_path = 'fixtures/test_audio.wav'
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # 单声道
        wav_file.setsampwidth(2)  # 16位
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(samples))
    
    print(f'✅ 创建了测试音频文件: {wav_path}')
    
    # 检查文件大小
    size = os.path.getsize(wav_path)
    print(f'文件大小: {size} bytes')
    
    return wav_path

if __name__ == "__main__":
    create_test_audio() 