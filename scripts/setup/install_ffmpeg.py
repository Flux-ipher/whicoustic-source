"""
FFmpeg Installation Helper for Windows

This script checks if FFmpeg is available and provides instructions to install it.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def check_ffmpeg():
    """Check if FFmpeg is available in PATH"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg is already installed and available!")
            print(f"Version info: {result.stdout.split('ffmpeg version')[1].split('Copyright')[0].strip()}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print("❌ FFmpeg not found in PATH")
    return False

def check_choco():
    """Check if Chocolatey is available"""
    try:
        result = subprocess.run(['choco', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def install_ffmpeg_choco():
    """Install FFmpeg using Chocolatey"""
    try:
        print("🔄 Installing FFmpeg using Chocolatey...")
        result = subprocess.run(['choco', 'install', 'ffmpeg', '-y'], 
                              capture_output=True, 
                              text=True, 
                              timeout=300)
        
        if result.returncode == 0:
            print("✅ FFmpeg installed successfully via Chocolatey!")
            return True
        else:
            print(f"❌ Chocolatey installation failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out")
        return False
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def provide_manual_instructions():
    """Provide manual installation instructions"""
    print("\n📋 Manual Installation Options:")
    print("\n1. Using Chocolatey (Recommended):")
    print("   First install Chocolatey from: https://chocolatey.org/install")
    print("   Then run: choco install ffmpeg")
    
    print("\n2. Using Scoop:")
    print("   First install Scoop from: https://scoop.sh/")
    print("   Then run: scoop install ffmpeg")
    
    print("\n3. Manual Download:")
    print("   1. Download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/")
    print("   2. Extract the zip file")
    print("   3. Add the 'bin' folder to your system PATH")
    print("   4. Restart your terminal/IDE")
    
    print("\n4. Using winget (Windows 10/11):")
    print("   Run: winget install Gyan.FFmpeg")

def main():
    print("🎬 FFmpeg Installation Helper")
    print("=" * 40)
    
    # Check current status
    if check_ffmpeg():
        print("\n🎉 No action needed - FFmpeg is working!")
        return
    
    # Check if we're on Windows
    if platform.system() != "Windows":
        print("❌ This script is designed for Windows only")
        print("Please install FFmpeg using your system's package manager")
        return
    
    # Try automatic installation
    if check_choco():
        print("\n🍫 Chocolatey found - attempting automatic installation...")
        if install_ffmpeg_choco():
            # Verify installation
            if check_ffmpeg():
                print("\n🎉 Installation complete and verified!")
                return
            else:
                print("\n⚠️ Installation completed but FFmpeg still not found in PATH")
                print("You may need to restart your terminal or add FFmpeg to PATH manually")
        else:
            print("\n❌ Automatic installation failed")
    else:
        print("\n📦 Chocolatey not found - manual installation required")
    
    provide_manual_instructions()
    
    print("\n💡 After installing FFmpeg, restart your terminal and run this script again to verify")
    print("\n🔧 Note: FFmpeg is optional for basic functionality but recommended for")
    print("   advanced audio processing features in the voice cloning platform")

if __name__ == "__main__":
    main()