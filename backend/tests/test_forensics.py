
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

def test_forensics():
    url = "http://localhost:8001/api/v1/verify/forensics"
    # We might need a token. If auth is enabled, this might fail with 401.
    # But let's see the response code first.
    
    files = {'file': ('test.wav', create_dummy_wav(), 'audio/wav')}
    data = {'analysis_depth': 'standard'}
    
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_forensics()
