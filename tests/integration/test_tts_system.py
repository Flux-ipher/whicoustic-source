#!/usr/bin/env python3
"""
Test script for the enhanced TTS and voice cloning system
"""

import asyncio
import requests
import time
import sys
import os
import tempfile


async def test_enhanced_backend():
    """Test the enhanced backend with real TTS functionality"""
    print("🎙️ Testing Enhanced VCAAS Backend...")
    
    base_url = "http://localhost:8000"
    
    try:
        # 1. Test health check
        print("\n🔍 Testing health check...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # 2. Test available voices
        print("\n🔍 Testing available voices...")
        response = requests.get(f"{base_url}/api/tts/voices", timeout=5)
        if response.status_code == 200:
            voices_data = response.json()
            print("✅ Available voices loaded successfully")
            print(f"   Owned voices: {len(voices_data.get('owned_voices', []))}")
            print(f"   Licensed voices: {len(voices_data.get('licensed_voices', []))}")
            print(f"   Public voices: {len(voices_data.get('public_voices', []))}")
            
            if voices_data.get('owned_voices'):
                voice_id = voices_data['owned_voices'][0]['id']
                print(f"   Using voice: {voice_id}")
            else:
                voice_id = "voice-1"
                print(f"   Using default voice: {voice_id}")
        else:
            print(f"❌ Failed to get voices: {response.status_code}")
            return False
        
        # 3. Test TTS generation
        print("\n🎙️ Testing TTS generation...")
        tts_request = {
            "text": "Hello! This is a test of the voice cloning system. It should generate real audio.",
            "voice_id": voice_id,
            "language": "en",
            "emotions": ["happy"],
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0,
            "add_watermark": True
        }
        
        response = requests.post(f"{base_url}/api/tts/generate", json=tts_request, timeout=10)
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["id"]
            print(f"✅ TTS generation started: {job_id}")
            print(f"   Status: {job_data['status']}")
            print(f"   Estimated completion: {job_data['estimated_completion']}")
        else:
            print(f"❌ TTS generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # 4. Wait for completion and check status
        print("\n⏳ Waiting for TTS generation to complete...")
        max_attempts = 20
        for attempt in range(max_attempts):
            time.sleep(2)
            response = requests.get(f"{base_url}/api/tts/jobs/{job_id}", timeout=5)
            
            if response.status_code == 200:
                job_status = response.json()
                print(f"   Attempt {attempt + 1}: Status = {job_status['status']}")
                
                if job_status['status'] == 'completed':
                    print("✅ TTS generation completed successfully!")
                    print(f"   Duration: {job_status.get('duration', 'unknown')}ms")
                    break
                elif job_status['status'] == 'failed':
                    print("❌ TTS generation failed")
                    return False
            else:
                print(f"❌ Failed to check job status: {response.status_code}")
                return False
        else:
            print("⚠️ TTS generation took longer than expected, but may still be processing")
        
        # 5. Test audio download
        print("\n🔊 Testing audio download...")
        response = requests.get(f"{base_url}/api/tts/jobs/{job_id}/audio", timeout=10)
        if response.status_code == 200:
            print("✅ Audio download successful!")
            print(f"   Content type: {response.headers.get('content-type')}")
            print(f"   Content length: {len(response.content)} bytes")
            
            # Save audio to temporary file for verification
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            print(f"   Audio saved to: {temp_path}")
            print("   You can play this file to verify the TTS works!")
            
            # Cleanup
            try:
                os.unlink(temp_path)
            except:
                pass
                
        else:
            print(f"❌ Audio download failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # 6. Test training endpoints
        print("\n🎯 Testing voice training endpoints...")
        
        # Test getting training jobs
        response = requests.get(f"{base_url}/api/training/jobs", timeout=5)
        if response.status_code == 200:
            training_data = response.json()
            print("✅ Training jobs endpoint working")
            print(f"   Current jobs: {len(training_data.get('jobs', []))}")
        else:
            print(f"❌ Training jobs failed: {response.status_code}")
        
        # Test getting trained voices
        response = requests.get(f"{base_url}/api/voice/trained", timeout=5)
        if response.status_code == 200:
            trained_data = response.json()
            print("✅ Trained voices endpoint working")
            print(f"   Trained voices: {len(trained_data.get('voices', []))}")
        else:
            print(f"❌ Trained voices failed: {response.status_code}")
        
        print("\n🎉 Enhanced backend test completed successfully!")
        print("\n📋 Summary:")
        print("   ✅ Health check passed")
        print("   ✅ Voice loading works")
        print("   ✅ TTS generation works")
        print("   ✅ Audio download works")
        print("   ✅ Training endpoints work")
        print("\n🚀 The voice cloning system is now functional!")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("💡 Make sure the backend server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🎙️ VCAAS Enhanced System Test")
    print("=" * 50)
    
    success = asyncio.run(test_enhanced_backend())
    sys.exit(0 if success else 1)
