"""
Voice processing service for Whicoustic platform.
Handles voice upload, preprocessing, VAD, denoising, and speaker embedding extraction.
"""

import librosa
import soundfile as sf
import numpy as np
from typing import Dict, Any, Optional, Tuple
import os
import tempfile
import logging
from pathlib import Path
import asyncio
import subprocess

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """
    Handles voice preprocessing pipeline for Whicoustic platform.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.target_sample_rate = self.config.get('target_sample_rate', 22050)
        self.max_duration = self.config.get('max_duration', 300)  # 5 minutes
        self.min_duration = self.config.get('min_duration', 5)   # 5 seconds
        self.quality_threshold = self.config.get('quality_threshold', 0.7)
        
        # Audio processing settings
        self.vad_threshold = self.config.get('vad_threshold', 0.01)
        self.noise_reduce_strength = self.config.get('noise_reduce_strength', 0.5)
        
        # Model paths (would be loaded from config in production)
        self.speaker_encoder_path = self.config.get('speaker_encoder_path')
        
    async def preprocess_audio(self, input_path: str, voice_id: str) -> str:
        """
        Complete preprocessing pipeline for uploaded audio.
        
        Args:
            input_path: Path to uploaded audio file
            voice_id: Unique voice identifier
            
        Returns:
            Path to processed audio file
        """
        try:
            logger.info(f"Starting audio preprocessing for voice {voice_id}")
            
            # Load and validate audio
            audio, sr = librosa.load(input_path, sr=None)
            
            # Basic validation
            if len(audio) / sr < self.min_duration:
                raise ValueError(f"Audio too short: {len(audio) / sr:.1f}s < {self.min_duration}s")
            
            if len(audio) / sr > self.max_duration:
                raise ValueError(f"Audio too long: {len(audio) / sr:.1f}s > {self.max_duration}s")
            
            # Step 1: Resample to target sample rate
            if sr != self.target_sample_rate:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sample_rate)
                sr = self.target_sample_rate
                logger.debug(f"Resampled audio to {sr}Hz")
            
            # Step 2: Voice Activity Detection and trimming
            audio_trimmed = await self._apply_vad(audio, sr)
            logger.debug(f"Applied VAD: {len(audio)} -> {len(audio_trimmed)} samples")
            
            # Step 3: Noise reduction
            audio_denoised = await self._reduce_noise(audio_trimmed, sr)
            logger.debug("Applied noise reduction")
            
            # Step 4: Normalize audio
            audio_normalized = await self._normalize_audio(audio_denoised)
            logger.debug("Normalized audio")
            
            # Step 5: Quality assessment
            quality_score = await self._assess_audio_quality(audio_normalized, sr)
            logger.info(f"Audio quality score: {quality_score:.3f}")
            
            if quality_score < self.quality_threshold:
                logger.warning(f"Low quality audio detected: {quality_score:.3f}")
            
            # Save processed audio
            output_dir = Path("data/processed_voices")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{voice_id}_processed.wav"
            
            sf.write(str(output_path), audio_normalized, sr)
            logger.info(f"Processed audio saved to {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed for {voice_id}: {e}")
            raise
    
    async def _apply_vad(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply Voice Activity Detection to remove silence."""
        try:
            # Use librosa's built-in trimming
            audio_trimmed, _ = librosa.effects.trim(
                audio,
                top_db=20,  # Trim silence below -20dB
                frame_length=512,
                hop_length=64
            )
            
            # Additional VAD using energy-based detection
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.01 * sr)     # 10ms hop
            
            frames = librosa.util.frame(
                audio_trimmed, 
                frame_length=frame_length, 
                hop_length=hop_length
            )
            
            # Calculate energy per frame
            energy = np.sum(frames ** 2, axis=0)
            
            # Adaptive threshold based on audio statistics
            threshold = np.percentile(energy, 20) + self.vad_threshold * np.max(energy)
            
            # Find voice activity
            voice_frames = energy > threshold
            
            # Convert frame indices back to sample indices
            voice_samples = np.zeros_like(audio_trimmed, dtype=bool)
            for i, is_voice in enumerate(voice_frames):
                start = i * hop_length
                end = start + frame_length
                voice_samples[start:end] |= is_voice
            
            # Extract voice segments
            voice_audio = audio_trimmed[voice_samples]
            
            return voice_audio if len(voice_audio) > sr else audio_trimmed
            
        except Exception as e:
            logger.warning(f"VAD failed, using original audio: {e}")
            return audio
    
    async def _reduce_noise(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply noise reduction using spectral subtraction."""
        try:
            # Simple spectral subtraction
            stft = librosa.stft(audio)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise from the first and last 10% of the signal
            noise_frames = int(0.1 * magnitude.shape[1])
            noise_spectrum = np.mean(
                np.concatenate([
                    magnitude[:, :noise_frames],
                    magnitude[:, -noise_frames:]
                ], axis=1),
                axis=1,
                keepdims=True
            )
            
            # Apply spectral subtraction
            alpha = self.noise_reduce_strength
            clean_magnitude = magnitude - alpha * noise_spectrum
            clean_magnitude = np.maximum(
                clean_magnitude,
                0.1 * magnitude  # Don't over-subtract
            )
            
            # Reconstruct audio
            clean_stft = clean_magnitude * np.exp(1j * phase)
            clean_audio = librosa.istft(clean_stft, length=len(audio))
            
            return clean_audio
            
        except Exception as e:
            logger.warning(f"Noise reduction failed, using original audio: {e}")
            return audio
    
    async def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio amplitude and apply dynamic range compression."""
        try:
            # RMS normalization
            rms = np.sqrt(np.mean(audio ** 2))
            if rms > 0:
                target_rms = 0.1  # Target RMS level
                audio = audio * (target_rms / rms)
            
            # Peak normalization
            peak = np.max(np.abs(audio))
            if peak > 0.95:
                audio = audio * (0.95 / peak)
            
            # Apply soft compression
            threshold = 0.7
            ratio = 4.0
            
            above_threshold = np.abs(audio) > threshold
            compressed = np.where(
                above_threshold,
                np.sign(audio) * (
                    threshold + (np.abs(audio) - threshold) / ratio
                ),
                audio
            )
            
            return compressed
            
        except Exception as e:
            logger.warning(f"Audio normalization failed: {e}")
            return audio
    
    async def _assess_audio_quality(self, audio: np.ndarray, sr: int) -> float:
        """Assess audio quality using multiple metrics."""
        try:
            # SNR estimation
            signal_power = np.mean(audio ** 2)
            
            # Estimate noise from quiet segments
            energy = librosa.feature.rms(y=audio, frame_length=512, hop_length=256)[0]
            noise_power = np.mean(energy[energy < np.percentile(energy, 20)]) ** 2
            
            snr = 10 * np.log10(signal_power / max(noise_power, 1e-10))
            snr_score = min(snr / 20, 1.0)  # Normalize to 0-1
            
            # Spectral clarity
            stft = librosa.stft(audio)
            magnitude = np.abs(stft)
            
            # Measure spectral rolloff consistency
            rolloff = librosa.feature.spectral_rolloff(S=magnitude, sr=sr)[0]
            rolloff_std = np.std(rolloff) / np.mean(rolloff)
            clarity_score = max(0, 1 - rolloff_std * 2)
            
            # Dynamic range
            dynamic_range = np.max(audio) - np.min(audio)
            dr_score = min(dynamic_range / 0.8, 1.0)
            
            # Zero crossing rate (voice naturalness)
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            zcr_score = 1 - min(np.std(zcr) * 1000, 1.0)
            
            # Combined quality score
            quality_score = (
                0.4 * snr_score +
                0.3 * clarity_score +
                0.2 * dr_score +
                0.1 * zcr_score
            )
            
            return float(np.clip(quality_score, 0, 1))
            
        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
            return 0.5  # Default neutral score
    
    async def extract_speaker_embedding(self, audio_path: str) -> np.ndarray:
        """
        Extract speaker embedding from processed audio.
        
        This is a placeholder implementation. In production, you would use
        a pretrained speaker encoder like those from Coqui TTS or SpeechBrain.
        """
        try:
            logger.info(f"Extracting speaker embedding from {audio_path}")
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.target_sample_rate)
            
            # Extract features for speaker embedding
            # This is a simplified example - in production use a proper speaker encoder
            
            # Extract MFCCs
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            
            # Extract spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)
            
            # Extract rhythmic features
            tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
            
            # Combine features
            features = np.concatenate([
                np.mean(mfcc, axis=1),
                np.std(mfcc, axis=1),
                [np.mean(spectral_centroid)],
                [np.mean(spectral_rolloff)],
                [np.mean(spectral_bandwidth)],
                [tempo]
            ])
            
            # Normalize features
            features = features / (np.linalg.norm(features) + 1e-8)
            
            # In production, this would be replaced with a proper neural network
            # that produces a high-dimensional embedding (e.g., 256 or 512 dimensions)
            
            # Create a mock embedding for demonstration
            embedding_dim = 256
            np.random.seed(hash(audio_path) % 2**32)  # Consistent seed for same audio
            embedding = features[:min(len(features), embedding_dim)]
            
            # Pad or truncate to desired dimension
            if len(embedding) < embedding_dim:
                padding = np.random.normal(0, 0.01, embedding_dim - len(embedding))
                embedding = np.concatenate([embedding, padding])
            else:
                embedding = embedding[:embedding_dim]
            
            logger.info(f"Extracted speaker embedding with dimension {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Speaker embedding extraction failed: {e}")
            raise
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        speaker_embedding: np.ndarray,
        voice_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Synthesize speech using the voice model.
        
        This is a placeholder implementation. In production, this would use
        Coqui TTS or another TTS system with the speaker embedding.
        """
        try:
            logger.info(f"Synthesizing speech for voice {voice_id}")
            
            voice_params = voice_params or {}
            speed = voice_params.get('speed', 1.0)
            pitch = voice_params.get('pitch', 0.0)
            
            # For now, generate a simple synthetic audio for demonstration
            # In production, this would use the actual TTS model
            
            duration = len(text) * 0.1 * speed  # Approximate duration
            sr = self.target_sample_rate
            t = np.linspace(0, duration, int(sr * duration))
            
            # Generate a simple synthetic voice based on embedding
            base_freq = 150 + np.mean(speaker_embedding) * 100  # Use embedding for variation
            pitch_shift = pitch * 50  # Convert pitch parameter to Hz
            
            # Create a simple synthetic voice
            audio = (
                0.3 * np.sin(2 * np.pi * (base_freq + pitch_shift) * t) +
                0.2 * np.sin(2 * np.pi * (base_freq + pitch_shift) * 2 * t) +
                0.1 * np.sin(2 * np.pi * (base_freq + pitch_shift) * 3 * t)
            )
            
            # Add some envelope and modulation based on text
            envelope = np.exp(-t * 0.1)  # Simple decay
            audio *= envelope
            
            # Add some noise for realism
            noise = np.random.normal(0, 0.01, len(audio))
            audio += noise
            
            # Normalize
            audio = audio / np.max(np.abs(audio)) * 0.8
            
            # Save synthesized audio
            output_dir = Path("data/synthesized")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"synthesis_{voice_id}_{hash(text) % 10000}.wav"
            
            sf.write(str(output_path), audio, sr)
            
            logger.info(f"Synthesized audio saved to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            raise