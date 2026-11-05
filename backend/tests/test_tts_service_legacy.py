#!/usr/bin/env python3
"""Test script for TTS inference engine"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tts_inference_engine import TTSInferenceEngine, SynthesisRequest

async def test_tts_engine():
    print("Testing TTS Inference Engine")
    print("=" * 40)
    
    # Initialize engine with correct path
    registry_path = "../../models/whicoustic_voice_registry/voice_registry.json"
    
    print(f"Registry path: {registry_path}")
    print(f"Registry exists: {Path(registry_path).exists()}")
    
    engine = TTSInferenceEngine(registry_path)
    
    # Wait for registry to load
    await asyncio.sleep(1)
    
    # Get available voices
    voices = await engine.get_available_voices()
    print(f"Available voices: {len(voices)}")
    
    if voices:
        print("\nFirst 3 voices:")
        for i, voice in enumerate(voices[:3]):
            print(f"  {i+1}. {voice['id'][:20]}... - {voice['name']} (quality: {voice['quality_score']:.3f})")
        
        # Test synthesis with first voice
        try:
            test_request = SynthesisRequest(
                text="Hello, this is a test of the voice synthesis system.",
                voice_id=voices[0]['id'],
                output_format="wav"
            )
            
            print(f"\nTesting synthesis with voice: {voices[0]['name']}")
            result = await engine.synthesize_speech(test_request)
            
            print(f"✅ Synthesis successful!")
            print(f"   Duration: {result.duration:.2f}s")
            print(f"   Audio data: {len(result.audio_data)} bytes")
            print(f"   Sample rate: {result.sample_rate}")
            print(f"   Format: {result.format}")
            
        except Exception as e:
            print(f"❌ Synthesis failed: {e}")
        
        # Get engine statistics
        stats = engine.get_synthesis_stats()
        print(f"\nEngine Statistics:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Successful: {stats['successful_syntheses']}")
        print(f"  Failed: {stats['failed_syntheses']}")
        
    else:
        print("No voices available. Check registry file.")

if __name__ == "__main__":
    asyncio.run(test_tts_engine())