#!/usr/bin/env python3
"""
Whicoustic Deployment Script
Starts both backend API and frontend development servers
"""

import subprocess
import time
import sys
import os
import requests
from pathlib import Path

def check_requirements():
    """Check if required tools are available"""
    print("[INFO] Checking requirements...")
    
    # Check Python
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print(f"[OK] Python: {result.stdout.strip()}")
    except Exception as e:
        print(f"[ERROR] Python not found: {e}")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, shell=True)
        print(f"[OK] Node.js: {result.stdout.strip()}")
    except Exception as e:
        print(f"[ERROR] Node.js not found: {e}")
        return False
    
    # Check npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, shell=True)
        print(f"[OK] npm: {result.stdout.strip()}")
    except Exception as e:
        print(f"[ERROR] npm not found: {e}")
        return False
    
    return True

def start_backend():
    """Start the backend API server"""
    print("[INFO] Starting Whicoustic Backend API...")
    
    # Run from backend directory to ensure .env is found
    backend_dir = Path("backend")
    if not backend_dir.exists():
        if Path("main.py").exists() and Path("app").exists():
            backend_dir = Path(".") # Already in backend
        else:
            print("[ERROR] Backend directory not found!")
            return None
            
    try:
        # Start backend in a subprocess
        # Use absolute path for python to be safe, script relative to cwd
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], cwd=backend_dir)
        
        # Wait for backend to start
        print("[INFO] Waiting for backend to start...")
        for i in range(10):  # Wait up to 10 seconds
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print("[OK] Backend API is running on http://localhost:8000")
                    print("[INFO] API Documentation: http://localhost:8000/docs")
                    return process
            except requests.exceptions.RequestException:
                time.sleep(1)
        
        print("[WARN] Backend may still be starting...")
        return process
        
    except Exception as e:
        print(f"[ERROR] Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the frontend development server"""
    print("[INFO] Starting Whicoustic Frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("[ERROR] Frontend directory not found!")
        return None
    
    try:
        # Change to frontend directory and start npm dev
        process = subprocess.Popen([
            "npm", "run", "dev"
        ], cwd=frontend_dir, shell=True)
        
        print("[INFO] Starting Next.js development server...")
        print("[INFO] Frontend will be available at http://localhost:3000")
        return process
        
    except Exception as e:
        print(f"[ERROR] Failed to start frontend: {e}")
        return None

def wait_for_frontend():
    """Wait for frontend to be ready"""
    print("[INFO] Waiting for frontend to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("[OK] Frontend is ready at http://localhost:3000")
                return True
        except requests.exceptions.RequestException:
            time.sleep(1)
    
    print("[WARN] Frontend may still be compiling...")
    return False

def main():
    """Main deployment function"""
    print("[Whicoustic] AI Voice Licensing & Biometric Protocol")
    print("==================================")
    
    if not check_requirements():
        print("[ERROR] Requirements not met. Please install Python and Node.js")
        return
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("[ERROR] Failed to start backend")
        return
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("[ERROR] Failed to start frontend")
        backend_process.terminate()
        return
    
    # Wait a bit for frontend to compile
    wait_for_frontend()
    
    print("\n[SUCCESS] Whicoustic is now running!")
    print("[INFO] Access points:")
    print("   • Frontend (Main App): http://localhost:3000")
    print("   • Backend API: http://localhost:8000")
    print("   • API Documentation: http://localhost:8000/docs")
    print("   • Dashboard: http://localhost:3000/dashboard")
    print("   • Voice Training: http://localhost:3000/training")
    print("   • TTS Playground: http://localhost:3000/playground")
    
    print("\n[INFO] Press Ctrl+C to stop both servers")
    
    try:
        # Wait for user to stop
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping Whicoustic...")
        frontend_process.terminate()
        backend_process.terminate()
        
        # Wait for processes to terminate
        frontend_process.wait()
        backend_process.wait()
        
        print("[OK] Whicoustic stopped successfully")

if __name__ == "__main__":
    main()
