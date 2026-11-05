import httpx
import wave
import os

wav_path = "dummy.wav"
with wave.open(wav_path, "w") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(22050)
    f.writeframes(b'\x00\x00' * 22050)

with open(wav_path, "rb") as f:
    files = {'reference': ('dummy.wav', f, 'audio/wav')}
    data = {'text': 'Hello world', 'language': 'en'}
    
    r = httpx.post("http://localhost:8000/api/v1/tts/clone", data=data, files=files, timeout=120.0)
    print(f"Status: {r.status_code}")
    try:
        print(r.json())
    except:
        print(r.text)

if os.path.exists(wav_path):
    os.remove(wav_path)
