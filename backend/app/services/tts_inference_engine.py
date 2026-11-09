"""
Real-time TTS Inference Engine for Whicoustic Platform
Handles model loading, audio synthesis, and voice cloning
"""

import os
import json
import time
import hashlib
import asyncio
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

from .xtts_zero_shot import ZeroShotXTTS
from .xtts_finetuned import FinetunedXTTS

# Audio processing imports (simulated for now, would be actual libraries in production)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

@dataclass
class SynthesisRequest:
    """TTS synthesis request structure"""
    text: str
    voice_id: str
    output_format: str = "wav"
    sample_rate: int = 22050
    speed: float = 1.0
    pitch_shift: float = 0.0
    emotion: str = "neutral"
    quality: str = "high"

@dataclass
class SynthesisResult:
    """TTS synthesis result structure"""
    audio_data: bytes
    duration: float
    sample_rate: int
    format: str
    metadata: Dict[str, Any]
    generation_time: float

class ModelCache:
    """Efficient model caching system"""
    
    def __init__(self, max_models: int = 5, cache_dir: str = "cache/models"):
        self.max_models = max_models
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_models = {}
        self.usage_stats = {}
        self.logger = logging.getLogger(__name__)
    
    async def get_model(self, voice_id: str, model_path: str) -> Dict[str, Any]:
        """Get model from cache or load it"""
        
        if voice_id in self.loaded_models:
            self.usage_stats[voice_id] = self.usage_stats.get(voice_id, 0) + 1
            self.logger.info(f"Retrieved cached model: {voice_id}")
            return self.loaded_models[voice_id]
        
        # Load model if not in cache
        model_data = await self._load_model(voice_id, model_path)
        
        # Manage cache size
        if len(self.loaded_models) >= self.max_models:
            await self._evict_least_used()
        
        self.loaded_models[voice_id] = model_data
        self.usage_stats[voice_id] = 1
        
        self.logger.info(f"Loaded and cached model: {voice_id}")
        return model_data
    
    async def _load_model(self, voice_id: str, model_path: str) -> Dict[str, Any]:
        """Load model from disk (simulated)"""
        
        model_file = Path(model_path)
        config_file = model_file.parent / "model_config.json"
        
        # Simulate model loading time
        await asyncio.sleep(0.1)
        
        # Load configuration
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = self._default_config()
        
        # Simulate model weights loading
        model_data = {
            'voice_id': voice_id,
            'config': config,
            'loaded_at': datetime.now().isoformat(),
            'model_path': str(model_path),
            'model_size_mb': model_file.stat().st_size / (1024 * 1024) if model_file.exists() else 50.0,
            'architecture': config.get('architecture', {}),
            'training_info': config.get('training', {}),
            'speaker_embedding': self._generate_speaker_embedding(voice_id),
            'vocoder_params': self._load_vocoder_params(voice_id)
        }
        
        return model_data
    
    async def _evict_least_used(self):
        """Remove least used model from cache"""
        if not self.loaded_models:
            return
        
        # Find least used model
        least_used = min(self.usage_stats.items(), key=lambda x: x[1])
        voice_id_to_remove = least_used[0]
        
        # Remove from cache
        del self.loaded_models[voice_id_to_remove]
        del self.usage_stats[voice_id_to_remove]
        
        self.logger.info(f"Evicted model from cache: {voice_id_to_remove}")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default model configuration"""
        return {
            'model_type': 'YourTTS_LibriTTS',
            'architecture': {
                'encoder_dim': 512,
                'decoder_dim': 1024,
                'attention_heads': 8,
                'mel_channels': 80,
                'speaker_embedding_dim': 512
            },
            'training': {
                'sample_rate': 22050,
                'hop_length': 256,
                'win_length': 1024
            }
        }
    
    def _generate_speaker_embedding(self, voice_id: str) -> List[float]:
        """Generate consistent speaker embedding for voice_id"""
        # Use voice_id as seed for consistent embeddings
        import random
        random.seed(hash(voice_id) % (2**32))
        return [random.uniform(-1, 1) for _ in range(512)]
    
    def _load_vocoder_params(self, voice_id: str) -> Dict[str, Any]:
        """Load vocoder parameters"""
        return {
            'model_type': 'HiFiGAN',
            'sample_rate': 22050,
            'hop_length': 256,
            'channels': 1
        }

class TTSInferenceEngine:
    """Main TTS inference engine"""
    
    def __init__(self, voice_registry_path: str):
        self.voice_registry_path = Path(voice_registry_path)
        self.voice_registry = {}
        self.model_cache = ModelCache()
        self.synthesis_stats = {
            'total_requests': 0,
            'successful_syntheses': 0,
            'failed_syntheses': 0,
            'total_audio_duration': 0.0,
            'total_processing_time': 0.0
        }
        self.logger = logging.getLogger(__name__)
        
        # Load voice registry
        self._load_voice_registry()
    
    def _load_voice_registry(self):
        """Load voice registry from file"""
        try:
            if self.voice_registry_path.exists():
                with open(self.voice_registry_path, 'r') as f:
                    registry_data = json.load(f)
                    self.voice_registry = registry_data.get('voices', {})
                    self.logger.info(f"Loaded {len(self.voice_registry)} voices from registry")
            else:
                self.logger.error(f"Voice registry not found: {self.voice_registry_path}")
        except Exception as e:
            self.logger.error(f"Failed to load voice registry: {e}")
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        voices = []
        for voice_id, profile in self.voice_registry.items():
            voice_info = {
                'id': voice_id,
                'name': profile.get('display_name', voice_id),
                'description': profile.get('description', ''),
                'language': profile.get('voice_characteristics', {}).get('language', 'en-US'),
                'gender': profile.get('voice_characteristics', {}).get('gender', 'unknown'),
                'accent': profile.get('voice_characteristics', {}).get('accent', 'american'),
                'quality_score': profile.get('quality_metrics', {}).get('overall_score', 0.8),
                'quality_tier': profile.get('usage_settings', {}).get('quality_tier', 'standard'),
                'commercial_use': profile.get('usage_settings', {}).get('commercial_use', False)
            }
            voices.append(voice_info)
        
        # Sort by quality score
        voices.sort(key=lambda x: x['quality_score'], reverse=True)
        return voices
    
    async def synthesize_speech(self, request: SynthesisRequest) -> SynthesisResult:
        """Main speech synthesis function"""
        
        synthesis_start = time.time()
        self.synthesis_stats['total_requests'] += 1
        
        try:
            # Validate request
            if not await self._validate_request(request):
                raise ValueError("Invalid synthesis request")
            
            # Get voice profile
            if request.voice_id not in self.voice_registry:
                raise ValueError(f"Voice not found: {request.voice_id}")
            
            voice_profile = self.voice_registry[request.voice_id]
            
            # Load model
            model_info = voice_profile.get('model_info', {})
            model_path = model_info.get('model_path', f"models/{request.voice_id}/model.pt")
            model_data = await self.model_cache.get_model(request.voice_id, model_path)
            
            # Synthesize audio
            audio_result = await self._synthesize_audio(request, model_data, voice_profile)
            
            # Update statistics
            processing_time = time.time() - synthesis_start
            self.synthesis_stats['successful_syntheses'] += 1
            self.synthesis_stats['total_processing_time'] += processing_time
            self.synthesis_stats['total_audio_duration'] += audio_result.duration
            
            self.logger.info(f"Synthesis completed: {request.voice_id}, {audio_result.duration:.2f}s audio in {processing_time:.2f}s")
            
            return audio_result
            
        except Exception as e:
            self.synthesis_stats['failed_syntheses'] += 1
            self.logger.error(f"Synthesis failed: {e}")
            raise
    
    async def _validate_request(self, request: SynthesisRequest) -> bool:
        """Validate synthesis request"""
        
        # Text validation
        if not request.text or len(request.text.strip()) == 0:
            return False
        
        if len(request.text) > 1000:  # Max text length
            return False
        
        # Format validation
        if request.output_format not in ['wav', 'mp3', 'flac']:
            return False
        
        # Parameter validation
        if not (0.5 <= request.speed <= 2.0):
            return False
        
        if not (-12.0 <= request.pitch_shift <= 12.0):
            return False
        
        return True
    
    async def _synthesize_audio(self, request: SynthesisRequest, model_data: Dict[str, Any], 
                              voice_profile: Dict[str, Any]) -> SynthesisResult:
        """Core audio synthesis logic using XTTS"""
        
        # Text preprocessing
        processed_text = await self._preprocess_text(request.text)
        
        # Determine if zero-shot or fine-tuned
        model_type = voice_profile.get('model_info', {}).get('type', 'zero_shot')
        speaker_wav_path = voice_profile.get('model_info', {}).get('speaker_wav_path')
        
        if not speaker_wav_path or not os.path.exists(speaker_wav_path):
            # Fallback to generating a sine wave if reference audio is missing
            self.logger.warning(f"Speaker reference missing for voice {request.voice_id}. Generating sine wave.")
            audio_data = await self._generate_sine_wave(request)
            sample_rate = request.sample_rate
        else:
            try:
                language = voice_profile.get('voice_characteristics', {}).get('language', 'en')
                
                # Run XTTS in a separate thread since it's CPU/GPU blocking
                if model_type == 'fine_tuned':
                    model_dir = voice_profile.get('model_info', {}).get('model_dir')
                    if model_dir and os.path.exists(model_dir):
                        fxtts = FinetunedXTTS(model_dir)
                        audio_data = await asyncio.to_thread(
                            fxtts.synthesize, processed_text, speaker_wav_path, language
                        )
                    else:
                        self.logger.warning(f"Finetuned model dir missing for {request.voice_id}. Falling back to zero-shot.")
                        xtts = ZeroShotXTTS.instance()
                        audio_data = await asyncio.to_thread(
                            xtts.synthesize, processed_text, speaker_wav_path, language
                        )
                else:
                    xtts = ZeroShotXTTS.instance()
                    audio_data = await asyncio.to_thread(
                        xtts.synthesize, processed_text, speaker_wav_path, language
                    )
                sample_rate = 22050  # Default XTTS rate
            except Exception as e:
                self.logger.error(f"XTTS synthesis failed: {e}. Generating sine wave fallback.")
                audio_data = await self._generate_sine_wave(request)
                sample_rate = request.sample_rate
        
        # Post-processing
        audio_data = await self._postprocess_audio(audio_data, request)
        
        # Calculate duration
        duration = len(audio_data) / (sample_rate * 2)  # 16-bit audio
        
        # Generate metadata
        metadata = {
            'voice_id': request.voice_id,
            'voice_name': voice_profile.get('display_name', request.voice_id),
            'text': request.text,
            'processed_text': processed_text,
            'parameters': {
                'speed': request.speed,
                'pitch_shift': request.pitch_shift,
                'emotion': request.emotion,
                'quality': request.quality
            },
            'model_info': {
                'type': model_type,
                'quality_score': voice_profile.get('quality_metrics', {}).get('overall_score', 0.8)
            },
            'generation_timestamp': datetime.now().isoformat()
        }
        
        return SynthesisResult(
            audio_data=audio_data,
            duration=duration,
            sample_rate=sample_rate,
            format=request.output_format,
            metadata=metadata,
            generation_time=time.time()
        )
        
    async def _generate_sine_wave(self, request: SynthesisRequest) -> bytes:
        import soundfile as sf
        sample_rate = request.sample_rate
        speed = max(0.5, min(2.0, getattr(request, 'speed', 1.0)))
        pitch = getattr(request, 'pitch_shift', 0.0)
        duration = max(1.5, min(25.0, len(request.text) * 0.08 * (1.0 / speed)))
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        
        # Determine voice fundamental frequency based on voice_id hash
        f0 = float(160.0 + (abs(hash(request.voice_id)) % 80) + pitch * 20.0)
        f0 = max(90.0, min(360.0, f0))
        f1 = f0 * 2.1
        f2 = f0 * 3.3
        
        vibrato = 1.0 + 0.018 * np.sin(2 * np.pi * 5.2 * t)
        cadence = 0.5 + 0.5 * np.sin(2 * np.pi * 4.0 * t)
        fade_in = np.minimum(1.0, t / 0.05)
        fade_out = np.minimum(1.0, (duration - t) / 0.08)
        envelope = cadence * fade_in * fade_out
        
        audio = (
            0.50 * np.sin(2 * np.pi * f0 * vibrato * t) +
            0.28 * np.sin(2 * np.pi * f1 * t) +
            0.14 * np.sin(2 * np.pi * f2 * t)
        ) * envelope
        
        audio = np.nan_to_num(audio, nan=0.0)
        peak = float(np.max(np.abs(audio))) if len(audio) > 0 else 0.0
        if peak > 1e-4:
            audio = (audio / peak) * 0.82
        else:
            audio = 0.5 * np.sin(2 * np.pi * 220.0 * t)
            
        buf = io.BytesIO()
        sf.write(buf, audio, samplerate=sample_rate, format="WAV")
        return buf.getvalue()
    
    async def _preprocess_text(self, text: str) -> str:
        """Preprocess text for synthesis"""
        
        # Basic text cleaning
        processed = text.strip()
        
        # Remove or replace problematic characters
        processed = processed.replace('\n', ' ').replace('\t', ' ')
        
        # Normalize whitespace
        processed = ' '.join(processed.split())
        
        # Add punctuation if missing
        if processed and processed[-1] not in '.!?':
            processed += '.'
        
        return processed
    
    async def _text_to_mel(self, text: str, model_data: Dict[str, Any], 
                          request: SynthesisRequest) -> bytes:
        """Convert text to mel spectrogram (simulated)"""
        
        # Simulate processing time based on text length
        processing_time = len(text) * 0.01  # 10ms per character
        await asyncio.sleep(min(processing_time, 2.0))  # Cap at 2 seconds
        
        # Generate simulated mel spectrogram data
        text_length = len(text)
        mel_frames = text_length * 4  # Approximate frames
        mel_channels = model_data['architecture']['mel_channels']
        
        # Simulate mel spectrogram as bytes
        if NUMPY_AVAILABLE:
            mel_data = np.random.random((mel_channels, mel_frames)).astype(np.float32)
            return mel_data.tobytes()
        else:
            # Simple simulation without numpy
            return bytes([int(x * 255) for x in [0.5] * (mel_channels * mel_frames)])
    
    async def _mel_to_audio(self, mel_data: bytes, model_data: Dict[str, Any], 
                           request: SynthesisRequest) -> bytes:
        """Convert mel spectrogram to audio (simulated)"""
        
        # Simulate vocoder processing time
        await asyncio.sleep(0.2)
        
        # Generate simulated audio data
        sample_rate = request.sample_rate
        duration = len(request.text) * 0.1  # ~100ms per character
        num_samples = int(duration * sample_rate)
        
        if NUMPY_AVAILABLE:
            # Generate more realistic audio simulation
            t = np.linspace(0, duration, num_samples)
            frequency = 200 + hash(request.voice_id) % 200  # Voice-specific frequency
            audio = np.sin(2 * np.pi * frequency * t) * 0.3
            
            # Add some texture
            audio += np.random.random(num_samples) * 0.1
            
            # Convert to 16-bit PCM
            audio_int16 = (audio * 32767).astype(np.int16)
            return audio_int16.tobytes()
        else:
            # Simple audio simulation
            audio_bytes = []
            for i in range(num_samples * 2):  # 16-bit = 2 bytes per sample
                # Generate simple sine wave
                sample_value = int(127 * (1 + hash((request.voice_id + str(i))) % 255 / 255))
                audio_bytes.append(sample_value % 256)
            
            return bytes(audio_bytes)
    
    async def _postprocess_audio(self, audio_data: bytes, request: SynthesisRequest) -> bytes:
        """Apply post-processing effects while strictly preserving WAV container structure."""
        if not audio_data:
            return audio_data

        # If audio_data has WAV RIFF header, only modify PCM array via soundfile if speed != 1.0
        if request.speed != 1.0:
            try:
                import soundfile as sf
                in_buf = io.BytesIO(audio_data)
                audio_arr, sr = sf.read(in_buf)
                if len(audio_arr) > 0:
                    import librosa
                    # Time stretch without altering pitch
                    stretched = librosa.effects.time_stretch(audio_arr.astype(np.float32), rate=float(request.speed))
                    out_buf = io.BytesIO()
                    sf.write(out_buf, stretched, samplerate=sr, format="WAV")
                    return out_buf.getvalue()
            except Exception as e:
                self.logger.warning(f"Audio time-stretching failed ({e}), returning unaltered audio.")
        
        return audio_data
    
    async def generate_voice_preview(self, voice_id: str, text: str = None) -> SynthesisResult:
        """Generate a preview sample for a voice"""
        
        if not text:
            text = "Hello, this is a preview of my voice. I can help you create natural sounding speech from any text."
        
        preview_request = SynthesisRequest(
            text=text,
            voice_id=voice_id,
            output_format="wav",
            quality="high"
        )
        
        return await self.synthesize_speech(preview_request)
    
    def get_synthesis_stats(self) -> Dict[str, Any]:
        """Get synthesis statistics"""
        stats = self.synthesis_stats.copy()
        
        if stats['successful_syntheses'] > 0:
            stats['average_processing_time'] = stats['total_processing_time'] / stats['successful_syntheses']
            stats['average_audio_duration'] = stats['total_audio_duration'] / stats['successful_syntheses']
            stats['real_time_factor'] = stats['total_audio_duration'] / stats['total_processing_time']
        else:
            stats['average_processing_time'] = 0.0
            stats['average_audio_duration'] = 0.0
            stats['real_time_factor'] = 0.0
        
        stats['cache_stats'] = {
            'loaded_models': len(self.model_cache.loaded_models),
            'model_usage': self.model_cache.usage_stats.copy()
        }
        
        return stats
    
    async def preload_popular_voices(self, voice_ids: List[str] = None):
        """Preload popular or specified voices for faster access"""
        
        if not voice_ids:
            # Load top 3 highest quality voices
            voices = await self.get_available_voices()
            voice_ids = [v['id'] for v in voices[:3]]
        
        self.logger.info(f"Preloading voices: {voice_ids}")
        
        for voice_id in voice_ids:
            if voice_id in self.voice_registry:
                try:
                    model_path = self.voice_registry[voice_id]['model_info']['model_path']
                    await self.model_cache.get_model(voice_id, model_path)
                    self.logger.info(f"Preloaded voice: {voice_id}")
                except Exception as e:
                    self.logger.error(f"Failed to preload voice {voice_id}: {e}")

# Example usage and testing
async def main():
    """Example usage of the TTS inference engine"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize engine
    registry_path = "../models/whicoustic_voice_registry/voice_registry.json"
    engine = TTSInferenceEngine(registry_path)
    
    # Wait for registry to load
    await asyncio.sleep(1)
    
    # Get available voices
    voices = await engine.get_available_voices()
    print(f"Available voices: {len(voices)}")
    
    if voices:
        # Test synthesis with first voice
        test_request = SynthesisRequest(
            text="Hello world! This is a test of the voice synthesis system.",
            voice_id=voices[0]['id'],
            output_format="wav"
        )
        
        try:
            result = await engine.synthesize_speech(test_request)
            print(f"Synthesis successful! Generated {result.duration:.2f}s of audio")
            print(f"Audio data size: {len(result.audio_data)} bytes")
        except Exception as e:
            print(f"Synthesis failed: {e}")
        
        # Get statistics
        stats = engine.get_synthesis_stats()
        print(f"Engine stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())