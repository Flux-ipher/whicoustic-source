import asyncio
import os
import sys

# Ensure backend module is in path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.watermark import WatermarkService
import soundfile as sf
import numpy as np

async def test():
    wm = WatermarkService()
    
    # Generate mock audio (2 seconds)
    sr = 44100
    t = np.linspace(0, 2.0, int(sr * 2.0), endpoint=False)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    
    # Save mock audio
    sf.write('test_audio.wav', audio, sr)
    
    # Embed watermark
    print("Embedding watermark...")
    out_path = await wm.embed_watermark('test_audio.wav', 'wm_123456789abc', method='mvp')
    
    # Extract watermark
    print("Extracting watermark...")
    res = await wm.detect_watermark(out_path, method='mvp')
    
    print(res)
    
asyncio.run(test())
