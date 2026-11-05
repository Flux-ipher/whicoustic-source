#!/usr/bin/env python3
"""
Simple test script to verify the backend API is working
"""
import subprocess
import time
import requests
import sys
import os

def test_backend():
    """Test the backend API"""
    print("🧪 Testing Whicoustic Backend...")
    
    # Start the backend server
    print("📡 Starting backend server...")
    backend_process = subprocess.Popen([
        sys.executable, "backend/main_simple.py"
    ], 
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE,
    cwd=os.getcwd()
    )
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test root endpoint
        print("🔍 Testing root endpoint...")
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Root endpoint working:", response.json())
        else:
            print("❌ Root endpoint failed:", response.status_code)
            return False
        
        # Test health endpoint  
        print("🔍 Testing health endpoint...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working:", response.json())
        else:
            print("❌ Health endpoint failed:", response.status_code)
            return False
            
        # Test API docs
        print("🔍 Testing API documentation...")
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API documentation accessible")
        else:
            print("❌ API documentation failed:", response.status_code)
            return False
        
        # Test mock API endpoints
        print("🔍 Testing mock API endpoints...")
        
        # Test auth endpoint
        response = requests.get("http://localhost:8000/api/auth/me", timeout=5)
        if response.status_code == 200:
            print("✅ Auth endpoint working:", response.json())
        else:
            print("❌ Auth endpoint failed:", response.status_code)
            
        # Test voice samples endpoint
        response = requests.get("http://localhost:8000/api/voice/samples", timeout=5)
        if response.status_code == 200:
            print("✅ Voice samples endpoint working:", response.json())
        else:
            print("❌ Voice samples endpoint failed:", response.status_code)
            
        # Test TTS voices endpoint
        response = requests.get("http://localhost:8000/api/tts/voices", timeout=5)
        if response.status_code == 200:
            print("✅ TTS voices endpoint working:", response.json())
        else:
            print("❌ TTS voices endpoint failed:", response.status_code)
            
        print("\n🎉 Backend API test completed successfully!")
        print("📋 You can access:")
        print("   • API Root: http://localhost:8000/")
        print("   • API Documentation: http://localhost:8000/docs")
        print("   • Health Check: http://localhost:8000/health")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("💡 Make sure the backend server is running")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Stop the backend server
        print("🛑 Stopping backend server...")
        backend_process.terminate()
        backend_process.wait()

if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)
