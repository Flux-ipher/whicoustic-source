import numpy as np
import soundfile as sf
import os
import sys

# Create test audio file
def create_test_audio(filename="test_audio.wav"):
    sample_rate = 16000
    duration = 3  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(filename, audio_data, sample_rate)
    return filename

def test_layers():
    print("Testing 6-layer defense mechanism directly...")
    audio_file = create_test_audio()
    
    try:
        print("\n--- Layer 1: AntiSpoof ---")
        from app.services.antispoof import AntiSpoofDetector
        try:
            detector = AntiSpoofDetector()
            res = detector.detect(audio_file)
            print(f"Layer 1 AntiSpoof Result: {res}")
        except Exception as e:
            print(f"Layer 1 Error: {e}")

        print("\n--- Layer 2: Speaker Verification & Biometric Consistency ---")
        from app.services.speaker_verification import SpeakerVerifier
        try:
            spk = SpeakerVerifier()
            res_consistency = spk.analyze_consistency(audio_file)
            print(f"Layer 2 Consistency Result: {res_consistency}")
            res_verify = spk.verify(audio_file, audio_file)
            print(f"Layer 2 Self-Verify Result: {res_verify}")
        except Exception as e:
            print(f"Layer 2 Error: {e}")

        print("\n--- Layer 3: Prosody ---")
        from app.services.prosody_service import ProsodyService
        try:
            prosody = ProsodyService()
            res = prosody.analyse(audio_file)
            print(f"Layer 3 Prosody Result: {res}")
        except Exception as e:
            print(f"Layer 3 Error: {e}")

        print("\n--- Layer 4: Paralinguistic ---")
        from app.services.paralinguistic_service import ParalinguisticService
        try:
            para = ParalinguisticService()
            res = para.analyse(audio_file)
            print(f"Layer 4 Paralinguistic Result: {res}")
        except Exception as e:
            print(f"Layer 4 Error: {e}")

        print("\n--- Layer 5: Semantic ---")
        from app.services.semantic_service import SemanticService
        try:
            sem = SemanticService()
            res = sem.analyse(audio_file)
            print(f"Layer 5 Semantic Result: {res}")
        except Exception as e:
            print(f"Layer 5 Error: {e}")

    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)

if __name__ == "__main__":
    test_layers()
