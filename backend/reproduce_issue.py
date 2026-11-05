
import numpy as np
import librosa
import sys

def test_spectral_analysis():
    print(f"Testing librosa version: {librosa.__version__}")
    
    # Create dummy audio: 1 second of white noise at 22050 Hz
    sr = 22050
    duration = 1.0
    audio = np.random.randn(int(sr * duration))
    
    print("Generated dummy audio.")
    
    try:
        print("Testing stft...")
        stft = librosa.stft(audio)
        print("stft success.")
        
        print("Testing spectral_centroid...")
        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
        print("spectral_centroid success.")
        
        print("Testing spectral_bandwidth...")
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)
        print("spectral_bandwidth success.")
        
        print("Testing spectral_rolloff...")
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
        print("spectral_rolloff success.")
        
        print("ALL TESTS PASSED.")
        
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_spectral_analysis()
