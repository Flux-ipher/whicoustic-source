"""
Streaming Latency Benchmark

Simulates sending chunks of raw PCM audio to StreamSession and measures the Real-Time Factor (RTF)
and latency of the fast-path (Layers 1, 3, 4, 2) and async path (Layer 5, 6).
"""

import asyncio
import time
import numpy as np
import sys
import os

# Add backend directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.stream_session import StreamSession

async def main():
    print("Starting Latency Benchmark for Real-Time Streaming...")
    
    sample_rate = 16000
    chunk_duration_ms = 30  # 30ms chunks
    chunk_samples = int((chunk_duration_ms / 1000.0) * sample_rate)
    
    # Generate 15 seconds of synthetic audio (sine wave + noise)
    duration_s = 15.0
    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    audio_data = 0.5 * np.sin(2 * np.pi * 300 * t) + np.random.normal(0, 0.05, len(t))
    audio_int16 = (audio_data * 32767).astype(np.int16)
    
    session = StreamSession(sample_rate=sample_rate)
    
    print(f"Feeding {duration_s}s of synthetic audio in {chunk_duration_ms}ms chunks...")
    
    start_time = time.time()
    total_chunks = len(audio_int16) // chunk_samples
    processed_count = 0
    
    latencies = []
    
    for i in range(total_chunks):
        chunk = audio_int16[i * chunk_samples : (i + 1) * chunk_samples].tobytes()
        
        chunk_start = time.perf_counter()
        result = await session.process_chunk(chunk)
        chunk_time_ms = (time.perf_counter() - chunk_start) * 1000
        
        if result is not None:
            latencies.append(chunk_time_ms)
            processed_count += 1
            if processed_count % 50 == 0:
                print(f"Processed {processed_count} frames. Avg latency: {np.mean(latencies):.2f}ms. Latest: {chunk_time_ms:.2f}ms")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Wait a bit for async tasks (Whisper, Watermark) to finish
    print("Waiting 5s for async tasks to complete...")
    await asyncio.sleep(5.0)
    
    print("\n=== Benchmark Results ===")
    print(f"Total audio duration: {duration_s}s")
    print(f"Total processing time: {total_time:.2f}s")
    print(f"Real-Time Factor (RTF): {total_time / duration_s:.4f} (lower is better, <1 is realtime)")
    print(f"Fast-path frames processed: {processed_count}")
    
    if latencies:
        print(f"Average fast-path latency per frame: {np.mean(latencies):.2f}ms")
        print(f"Max fast-path latency per frame: {np.max(latencies):.2f}ms")
        print(f"99th percentile latency: {np.percentile(latencies, 99):.2f}ms")
    
    session.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
