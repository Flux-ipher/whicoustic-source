import asyncio
import os
import wave
import numpy as np

# Create a sample wav file
def create_dummy_wav(path, duration=15.0, sr=22050):
    t = np.linspace(0, duration, int(sr * duration), False)
    # Generate a mix of frequencies to simulate some complexity
    audio = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 880 * t)
    # Add some noise as realistic audio has noise
    noise = np.random.normal(0, 0.05, len(audio))
    audio += noise
    
    audio = (np.clip(audio, -0.99, 0.99) * 32767).astype(np.int16)
    with wave.open(path, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(audio.tobytes())

from app.core.watermark import WatermarkService

async def main():
    dummy_wav = "dummy_for_watermark_test.wav"
    create_dummy_wav(dummy_wav)
    print("Created dummy audio file:", dummy_wav)
    
    svc = WatermarkService("test_secret_for_watermark")
    
    print("Testing MVP Watermark:")
    try:
        out_mvp = await svc.embed_watermark(dummy_wav, "my_mvp_wm_id", method="mvp")
        print("  Embedded successfully into:", out_mvp)
        det_mvp = await svc.detect_watermark(out_mvp, method="mvp")
        print("  Detection result:", det_mvp)
    except Exception as e:
        print("  Error:", e)
        import traceback
        traceback.print_exc()
        
    print("\nTesting Robust Watermark:")
    try:
        out_robust = await svc.embed_watermark(dummy_wav, "a1b2c3d4e5f60718", method="robust")
        print("  Embedded successfully into:", out_robust)
        det_robust = await svc.detect_watermark(out_robust, method="robust")
        print("  Detection result:", det_robust)
    except Exception as e:
        print("  Error:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
