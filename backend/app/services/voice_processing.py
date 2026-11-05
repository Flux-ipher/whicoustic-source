import os
import io
import asyncio
import librosa
import soundfile as sf
import numpy as np
import torch
import torchaudio
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from pydub import AudioSegment
import uuid
from datetime import datetime

from app.core.config import settings
from app.models import VoiceSample, VoiceStatus, VoiceQuality
from sqlalchemy.ext.asyncio import AsyncSession


class AudioProcessor:
    """Audio processing utilities for voice samples"""
    
    @staticmethod
    def clean_audio(audio_path: str, output_path: str) -> Dict[str, Any]:
        """Clean and preprocess audio file"""
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=settings.SAMPLE_RATE)
            
            # Noise reduction using spectral subtraction
            audio_cleaned = AudioProcessor._spectral_subtraction(audio, sr)
            
            # Normalize audio
            audio_normalized = librosa.util.normalize(audio_cleaned)
            
            # Remove silence
            audio_trimmed, _ = librosa.effects.trim(
                audio_normalized,
                top_db=20,
                frame_length=2048,
                hop_length=512
            )
            
            # Save processed audio
            sf.write(output_path, audio_trimmed, sr)
            
            # Calculate quality metrics
            duration = len(audio_trimmed) / sr
            snr = AudioProcessor._calculate_snr(audio_trimmed)
            
            return {
                "success": True,
                "duration": duration,
                "sample_rate": sr,
                "channels": 1,
                "snr": snr,
                "output_path": output_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def _spectral_subtraction(audio: np.ndarray, sr: int, alpha: float = 2.0) -> np.ndarray:
        """Apply spectral subtraction for noise reduction"""
        # Compute STFT
        stft = librosa.stft(audio, hop_length=settings.HOP_LENGTH, n_fft=settings.N_FFT)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise from first few frames
        noise_frames = magnitude[:, :10]
        noise_spectrum = np.mean(noise_frames, axis=1, keepdims=True)
        
        # Spectral subtraction
        enhanced_magnitude = magnitude - alpha * noise_spectrum
        enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)
        
        # Reconstruct audio
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        enhanced_audio = librosa.istft(enhanced_stft, hop_length=settings.HOP_LENGTH)
        
        return enhanced_audio
    
    @staticmethod
    def _calculate_snr(audio: np.ndarray) -> float:
        """Calculate Signal-to-Noise Ratio"""
        # Simple SNR estimation
        signal_power = np.mean(audio ** 2)
        noise_power = np.var(audio - np.mean(audio))
        
        if noise_power > 0:
            snr = 10 * np.log10(signal_power / noise_power)
        else:
            snr = 100  # Very high SNR if no noise detected
            
        return float(snr)
    
    @staticmethod
    def extract_features(audio_path: str) -> Dict[str, Any]:
        """Extract audio features for voice analysis"""
        try:
            audio, sr = librosa.load(audio_path, sr=settings.SAMPLE_RATE)
            
            # Extract features
            features = {}
            
            # Mel-frequency cepstral coefficients
            mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            features['mfcc_mean'] = np.mean(mfccs, axis=1).tolist()
            features['mfcc_std'] = np.std(mfccs, axis=1).tolist()
            
            # Spectral features
            features['spectral_centroid'] = float(np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr)))
            features['spectral_bandwidth'] = float(np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=sr)))
            features['spectral_rolloff'] = float(np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sr)))
            features['zero_crossing_rate'] = float(np.mean(librosa.feature.zero_crossing_rate(audio)))
            
            # Pitch features
            pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                features['pitch_mean'] = float(np.mean(pitch_values))
                features['pitch_std'] = float(np.std(pitch_values))
            else:
                features['pitch_mean'] = 0.0
                features['pitch_std'] = 0.0
            
            return features
            
        except Exception as e:
            return {"error": str(e)}


class VoiceTrainer:
    """Voice training and model management"""
    
    def __init__(self):
        self.model_path = Path(settings.TTS_MODEL_PATH)
        self.model_path.mkdir(parents=True, exist_ok=True)
    
    async def train_voice_model(self, voice_sample: VoiceSample, audio_path: str) -> Dict[str, Any]:
        """Train a voice model from audio sample"""
        try:
            # Create model directory for this voice
            model_dir = self.model_path / f"voice_{voice_sample.id}"
            model_dir.mkdir(exist_ok=True)
            
            # Extract features
            features = AudioProcessor.extract_features(audio_path)
            if "error" in features:
                return {"success": False, "error": features["error"]}
            
            # For demo purposes, we'll simulate training
            # In a real implementation, you would integrate with Coqui TTS, FastSpeech2, etc.
            await asyncio.sleep(2)  # Simulate training time
            
            # Calculate quality score based on features
            quality_score = self._calculate_quality_score(features)
            quality_level = self._get_quality_level(quality_score)
            
            # Save model metadata
            model_config = {
                "voice_id": str(voice_sample.id),
                "features": features,
                "quality_score": quality_score,
                "training_config": {
                    "sample_rate": settings.SAMPLE_RATE,
                    "n_mels": settings.N_MELS,
                    "hop_length": settings.HOP_LENGTH,
                    "win_length": settings.WIN_LENGTH,
                    "n_fft": settings.N_FFT
                },
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Save config
            import json
            config_path = model_dir / "config.json"
            with open(config_path, 'w') as f:
                json.dump(model_config, f, indent=2)
            
            return {
                "success": True,
                "model_path": str(model_dir),
                "quality_score": quality_score,
                "quality_level": quality_level.value,
                "features": features
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_quality_score(self, features: Dict[str, Any]) -> float:
        """Calculate voice quality score from features"""
        score = 50.0  # Base score
        
        # Boost score based on spectral richness
        if features.get('spectral_bandwidth', 0) > 1000:
            score += 20
        
        # Boost score based on pitch stability
        pitch_std = features.get('pitch_std', 100)
        if pitch_std < 50:
            score += 20
        
        # Penalize high zero crossing rate (indicates noise)
        zcr = features.get('zero_crossing_rate', 0)
        if zcr < 0.1:
            score += 10
        
        return min(100.0, max(0.0, score))
    
    def _get_quality_level(self, score: float) -> VoiceQuality:
        """Convert quality score to quality level enum"""
        if score >= 90:
            return VoiceQuality.EXCELLENT
        elif score >= 70:
            return VoiceQuality.GOOD
        elif score >= 50:
            return VoiceQuality.FAIR
        else:
            return VoiceQuality.POOR


class TTSEngine:
    """Text-to-Speech engine integration"""
    
    def __init__(self):
        self.output_path = Path(settings.TTS_OUTPUT_PATH)
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    async def generate_speech(
        self,
        text: str,
        voice_model_path: str,
        output_filename: str,
        emotional_tags: Optional[list] = None,
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> Dict[str, Any]:
        """Generate speech from text using trained voice model"""
        try:
            output_file = self.output_path / output_filename
            
            # For demo purposes, we'll create a simple sine wave as placeholder
            # In a real implementation, you would use Coqui TTS, FastSpeech2, etc.
            sample_rate = settings.SAMPLE_RATE
            duration = len(text) * 0.1  # Rough estimate: 0.1s per character
            
            # Generate a simple tone (placeholder for actual TTS)
            t = np.linspace(0, duration, int(sample_rate * duration))
            frequency = 440 * pitch  # Base frequency adjusted by pitch
            audio = 0.3 * np.sin(2 * np.pi * frequency * t / speed)
            
            # Add some variation to make it more speech-like
            modulation = 0.1 * np.sin(2 * np.pi * 5 * t)  # 5Hz modulation
            audio = audio * (1 + modulation)
            
            # Apply emotional modifications
            if emotional_tags:
                audio = self._apply_emotional_modifications(audio, emotional_tags)
            
            # Save audio file
            sf.write(str(output_file), audio, sample_rate)
            
            # Get file size
            file_size = output_file.stat().st_size
            
            return {
                "success": True,
                "output_path": str(output_file),
                "duration": duration,
                "file_size": file_size,
                "sample_rate": sample_rate
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _apply_emotional_modifications(self, audio: np.ndarray, emotions: list) -> np.ndarray:
        """Apply emotional modifications to audio"""
        modified_audio = audio.copy()
        
        for emotion in emotions:
            if emotion.lower() == "happy":
                # Increase pitch slightly and add brightness
                modified_audio *= 1.1
            elif emotion.lower() == "sad":
                # Decrease amplitude and add slight delay
                modified_audio *= 0.8
            elif emotion.lower() == "angry":
                # Add some distortion and increase volume
                modified_audio = np.tanh(modified_audio * 1.5)
            elif emotion.lower() == "calm":
                # Smooth the audio
                from scipy.signal import savgol_filter
                if len(modified_audio) > 51:  # Minimum window size for savgol
                    modified_audio = savgol_filter(modified_audio, 51, 3)
        
        return modified_audio


class VoiceProcessingService:
    """Main voice processing service"""
    
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.voice_trainer = VoiceTrainer()
        self.tts_engine = TTSEngine()
    
    async def process_voice_upload(
        self,
        db: AsyncSession,
        voice_sample: VoiceSample,
        audio_file_path: str
    ) -> Dict[str, Any]:
        """Process uploaded voice sample"""
        try:
            # Update status to processing
            voice_sample.status = VoiceStatus.PROCESSING
            await db.commit()
            
            # Clean and preprocess audio
            processed_audio_path = f"{audio_file_path}_processed.wav"
            cleanup_result = self.audio_processor.clean_audio(audio_file_path, processed_audio_path)
            
            if not cleanup_result["success"]:
                voice_sample.status = VoiceStatus.FAILED
                await db.commit()
                return cleanup_result
            
            # Update voice sample with audio properties
            voice_sample.duration = cleanup_result["duration"]
            voice_sample.sample_rate = cleanup_result["sample_rate"]
            voice_sample.channels = cleanup_result["channels"]
            
            # Start training
            voice_sample.status = VoiceStatus.TRAINING
            await db.commit()
            
            # Train voice model
            training_result = await self.voice_trainer.train_voice_model(
                voice_sample, processed_audio_path
            )
            
            if not training_result["success"]:
                voice_sample.status = VoiceStatus.FAILED
                await db.commit()
                return training_result
            
            # Update voice sample with training results
            voice_sample.status = VoiceStatus.TRAINED
            voice_sample.quality_score = training_result["quality_score"]
            voice_sample.quality_level = VoiceQuality(training_result["quality_level"])
            voice_sample.model_path = training_result["model_path"]
            voice_sample.file_path = processed_audio_path  # Update to processed version
            
            await db.commit()
            
            return {
                "success": True,
                "voice_sample_id": str(voice_sample.id),
                "quality_score": training_result["quality_score"],
                "status": "trained"
            }
            
        except Exception as e:
            voice_sample.status = VoiceStatus.FAILED
            await db.commit()
            return {"success": False, "error": str(e)}
    
    async def generate_tts(
        self,
        text: str,
        voice_model_path: str,
        emotional_tags: Optional[list] = None,
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> Dict[str, Any]:
        """Generate text-to-speech audio"""
        output_filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
        
        return await self.tts_engine.generate_speech(
            text=text,
            voice_model_path=voice_model_path,
            output_filename=output_filename,
            emotional_tags=emotional_tags,
            speed=speed,
            pitch=pitch
        )


# Global service instance
voice_processing_service = VoiceProcessingService()
