
import requests
import numpy as np
import soundfile as sf
import io

# Create dummy wav file
def create_dummy_wav():
    sr = 22050
    duration = 1.0
    audio = np.random.uniform(-0.5, 0.5, int(sr * duration))
    buffer = io.BytesIO()
    sf.write(buffer, audio, sr, format='WAV')
    buffer.seek(0)
    return buffer

def test_spectral():
    url = "http://localhost:8001/api/v1/verify/spectral-graphs"
    
    files = {'file': ('test_spectral.wav', create_dummy_wav(), 'audio/wav')}
    
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
        else:
            print("Response: <Success - JSON data received>")
            # print keys to verify
            print(response.json().keys())
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_spectral()
