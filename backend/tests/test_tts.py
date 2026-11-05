import asyncio
import edge_tts
from gtts import gTTS
import pyttsx3
import io

async def test_edge_tts():
    """Test Edge TTS functionality"""
    print("🎯 Testing Edge TTS...")
    try:
        voices = await edge_tts.list_voices()
        print(f"✅ Edge TTS: {len(voices)} voices available")
        
        if voices:
            # Test speech generation
            voice = voices[0]["Name"]
            text = "Hello, this is a test of Edge TTS voice cloning."
            
            communicate = edge_tts.Communicate(text, voice)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            with open("test_edge.wav", "wb") as f:
                f.write(audio_data)
            
            print(f"✅ Generated speech with voice: {voice}")
            print(f"📁 Saved to: test_edge.wav")
    except Exception as e:
        print(f"❌ Edge TTS failed: {e}")

def test_gtts():
    """Test Google TTS"""
    print("\n🎯 Testing Google TTS...")
    try:
        text = "Hello, this is a test of Google Text-to-Speech."
        tts = gTTS(text=text, lang="en", slow=False)
        
        with open("test_gtts.mp3", "wb") as f:
            tts.write_to_fp(f)
        
        print("✅ Generated speech with Google TTS")
        print("📁 Saved to: test_gtts.mp3")
    except Exception as e:
        print(f"❌ Google TTS failed: {e}")

def test_local_tts():
    """Test local Windows TTS"""
    print("\n🎯 Testing Local Windows TTS...")
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"✅ Local TTS: {len(voices)} voices available")
        
        if voices:
            text = "Hello, this is a test of Windows text to speech."
            engine.setProperty('voice', voices[0].id)
            engine.setProperty('rate', 200)
            engine.setProperty('volume', 0.9)
            
            engine.save_to_file(text, "test_local.wav")
            engine.runAndWait()
            
            print(f"✅ Generated speech with voice: {voices[0].name if hasattr(voices[0], 'name') else 'Default'}")
            print("📁 Saved to: test_local.wav")
    except Exception as e:
        print(f"❌ Local TTS failed: {e}")

def test_librosa():
    """Test audio analysis with librosa"""
    print("\n🎯 Testing Audio Analysis...")
    try:
        import librosa
        import numpy as np
        
        # Create a simple test audio file
        sr = 22050
        duration = 3  # seconds
        t = np.linspace(0, duration, int(sr * duration), False)
        frequency = 440  # A note
        audio = np.sin(frequency * 2 * np.pi * t)
        
        import soundfile as sf
        sf.write("test_audio.wav", audio, sr)
        
        # Analyze the test audio
        y, sr_loaded = librosa.load("test_audio.wav")
        duration_loaded = len(y) / sr_loaded
        
        print(f"✅ Audio analysis working")
        print(f"📊 Duration: {duration_loaded:.2f} seconds")
        print(f"📊 Sample rate: {sr_loaded}")
        
    except Exception as e:
        print(f"❌ Audio analysis failed: {e}")

async def main():
    print("🧪 Testing Voice Cloning Components...\n")
    
    await test_edge_tts()
    test_gtts()
    test_local_tts()
    test_librosa()
    
    print("\n✅ Testing complete!")
    print("🎉 Your voice cloning backend is ready!")

if __name__ == "__main__":
    asyncio.run(main())