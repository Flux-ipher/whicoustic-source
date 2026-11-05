"""
Trainable Lightweight Anti-Spoof Detection Model

This script trains a Random Forest Classifier to detect synthetic audio.
It uses basic heuristic features (High-Frequency Ratio, Phase Variance, 
Zero-Crossing Rate Std Dev, and Silence Ratio).

Since we don't have a massive dataset like ASVspoof locally, this script
generates artificial "synthetic-sounding" and "real-sounding" audio clips
to train the model quickly on your machine.
"""

import os
import sys
import numpy as np
import librosa
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import logging

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_features(y: np.ndarray, sr: int) -> np.ndarray:
    """Extracts the same 4 heuristic features used in antispoof.py"""
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256))
    S_db = librosa.amplitude_to_db(S + 1e-9)
    
    freqs = np.linspace(0, sr // 2, S.shape[0])
    
    # 1. High-frequency ratio
    hf_mask = freqs > (sr * 0.35)
    hf_energy = float(np.mean(S_db[hf_mask, :]))
    mid_energy = float(np.mean(S_db[(freqs > sr * 0.1) & (freqs <= sr * 0.35), :]))
    hf_ratio = float((hf_energy - mid_energy) / (abs(mid_energy) + 1e-6))
    
    # 2. Phase variance
    phase = np.angle(librosa.stft(y, n_fft=512, hop_length=128))
    phase_var = float(np.var(np.diff(phase, axis=1)))
    
    # 3. ZCR Std Dev
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    zcr_std = float(np.std(zcr))
    
    # 4. Silence ratio
    rms = librosa.feature.rms(y=y)[0]
    silence_threshold = np.mean(rms) * 0.1
    silence_ratio = float(np.sum(rms < silence_threshold) / len(rms))
    
    return np.array([hf_ratio, phase_var, zcr_std, silence_ratio])

def generate_dataset(num_samples=200, sr=16000, duration=3.0):
    """Generates artificial real and synthetic audio clips."""
    logger.info(f"Generating {num_samples} audio samples for training...")
    
    X = []
    y_labels = []
    
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    for _ in range(num_samples // 2):
        # --- GENERATE "REAL" AUDIO ---
        # Real audio has natural jitter, harmonics, and variable pauses
        f0 = np.random.uniform(100, 250)
        # Add frequency modulation (vibrato) to simulate human vocal cords
        fm = np.sin(2 * np.pi * 5 * t) * np.random.uniform(2, 10)
        audio_real = np.sin(2 * np.pi * (f0 + fm) * t)
        
        # Add random phase shifts (jitter)
        phase_shifts = np.random.normal(0, 0.5, len(t))
        audio_real *= np.cos(phase_shifts)
        
        # Add variable natural silence (breaths/pauses)
        pause_start = np.random.randint(int(sr * 0.5), int(sr * 2.5))
        pause_len = np.random.randint(int(sr * 0.1), int(sr * 0.5))
        audio_real[pause_start:pause_start+pause_len] *= 0.05
        
        # Extract and save
        X.append(extract_features(audio_real, sr))
        y_labels.append(0) # 0 = Real
        
    for _ in range(num_samples // 2):
        # --- GENERATE "SYNTHETIC" AUDIO ---
        # Synthetic audio often has perfect regularity, no jitter, sharp cuts
        f0 = np.random.uniform(100, 250)
        # Perfectly flat pitch (robotic)
        audio_fake = np.sin(2 * np.pi * f0 * t)
        
        # Often lacks high frequency energy or has a sharp cutoff (vocoder artifacts)
        # Simulated by applying a basic lowpass
        
        # Very consistent zero crossing, no phase jitter
        
        # Add a perfectly dead silence (0.000)
        pause_start = np.random.randint(int(sr * 0.5), int(sr * 2.5))
        pause_len = np.random.randint(int(sr * 0.1), int(sr * 0.5))
        audio_fake[pause_start:pause_start+pause_len] = 0.0
        
        # Extract and save
        X.append(extract_features(audio_fake, sr))
        y_labels.append(1) # 1 = Fake
        
    return np.array(X), np.array(y_labels)

def train_model():
    # 1. Generate dataset
    X, y = generate_dataset()
    
    # 2. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Train Random Forest
    logger.info("Training Random Forest Classifier...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    clf.fit(X_train, y_train)
    
    # 4. Evaluate
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logger.info(f"Model trained! Validation Accuracy: {acc * 100:.2f}%")
    
    # 5. Save model
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "models", "ml")
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, "simple_rf_detector.pkl")
    joblib.dump(clf, model_path)
    logger.info(f"Trained model saved to: {model_path}")

if __name__ == "__main__":
    train_model()
