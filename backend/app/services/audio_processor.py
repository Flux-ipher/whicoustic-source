"""
Audio Processing Service

Handles audio file processing, quality analysis, format conversion, and preprocessing
for voice cloning and TTS systems.
"""

import io
import os
import tempfile
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from scipy.signal import savgol_filter
from loguru import logger
import asyncio
import aiofiles


class AudioQualityAnalyzer:
    """Analyzes audio quality for voice training suitability"""
    
    @staticmethod
    def analyze_audio_quality(audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Comprehensive audio quality analysis"""
        try:
            # Basic audio properties
            duration = len(audio) / sr
            
            # RMS energy analysis
            rms_energy = np.sqrt(np.mean(audio**2))
            
            # Dynamic range
            dynamic_range = np.max(audio) - np.min(audio)
            
            # Signal-to-noise ratio estimation
            snr = AudioQualityAnalyzer._estimate_snr(audio)
            
            # Voice activity detection
            voice_activity_ratio = AudioQualityAnalyzer._detect_voice_activity(audio, sr)
            
            # Spectral features
            spectral_features = AudioQualityAnalyzer._analyze_spectral_features(audio, sr)
            
            # Clipping detection
            clipping_ratio = AudioQualityAnalyzer._detect_clipping(audio)
            
            # Overall quality score (0-1)
            quality_score = AudioQualityAnalyzer._calculate_quality_score({
                'snr': snr,
                'voice_activity': voice_activity_ratio,
                'clipping': clipping_ratio,
                'dynamic_range': dynamic_range,
                'duration': duration
            })
            
            return {
                'duration_seconds': duration,
                'sample_rate': sr,
                'rms_energy': float(rms_energy),
                'dynamic_range': float(dynamic_range),
                'snr_db': float(snr),
                'voice_activity_ratio': float(voice_activity_ratio),
                'clipping_ratio': float(clipping_ratio),
                'spectral_features': spectral_features,
                'quality_score': float(quality_score),
                'is_suitable_for_training': quality_score > 0.6,
                'recommendations': AudioQualityAnalyzer._generate_recommendations(quality_score, {
                    'snr': snr,
                    'voice_activity': voice_activity_ratio,
                    'clipping': clipping_ratio,
                    'duration': duration
                })
            }
            
        except Exception as e:
            logger.error(f"Audio quality analysis failed: {e}")
            return {
                'error': str(e),
                'quality_score': 0.0,
                'is_suitable_for_training': False
            }
    
    @staticmethod
    def _estimate_snr(audio: np.ndarray) -> float:
        """Estimate signal-to-noise ratio"""
        try:
            # Simple VAD-based SNR estimation
            # Get the loudest 50% as signal, quietest 20% as noise
            sorted_energy = np.sort(audio**2)
            noise_floor = np.mean(sorted_energy[:int(len(sorted_energy) * 0.2)])
            signal_power = np.mean(sorted_energy[int(len(sorted_energy) * 0.5):])
            
            if noise_floor > 0:
                snr = 10 * np.log10(signal_power / noise_floor)
                return min(max(snr, -20), 60)  # Clamp between -20 and 60 dB
            return 0.0
        except:
            return 0.0
    
    @staticmethod
    def _detect_voice_activity(audio: np.ndarray, sr: int) -> float:
        """Detect ratio of voice activity vs silence"""
        try:
            # Use RMS energy to detect voice activity
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop
            
            # Calculate RMS for each frame
            frames = librosa.util.frame(audio, frame_length=frame_length, hop_length=hop_length)
            rms_values = np.sqrt(np.mean(frames**2, axis=0))
            
            # Adaptive threshold based on distribution
            threshold = np.percentile(rms_values, 30)  # 30th percentile as threshold
            
            voice_frames = np.sum(rms_values > threshold)
            total_frames = len(rms_values)
            
            return voice_frames / total_frames if total_frames > 0 else 0.0
            
        except:
            return 0.0
    
    @staticmethod
    def _analyze_spectral_features(audio: np.ndarray, sr: int) -> Dict[str, float]:
        """Analyze spectral characteristics"""
        try:
            # Compute spectrum
            D = librosa.amplitude_to_db(np.abs(librosa.stft(audio)), ref=np.max)
            
            # Spectral centroid (brightness)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            spectral_centroid_mean = np.mean(spectral_centroids)
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
            spectral_rolloff_mean = np.mean(spectral_rolloff)
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            zcr_mean = np.mean(zcr)
            
            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
            bandwidth_mean = np.mean(spectral_bandwidth)
            
            return {
                'spectral_centroid': float(spectral_centroid_mean),
                'spectral_rolloff': float(spectral_rolloff_mean),
                'zero_crossing_rate': float(zcr_mean),
                'spectral_bandwidth': float(bandwidth_mean)
            }
            
        except Exception as e:
            logger.warning(f"Spectral analysis failed: {e}")
            return {}
    
    @staticmethod
    def _detect_clipping(audio: np.ndarray, threshold: float = 0.95) -> float:
        """Detect audio clipping"""
        try:
            # Count samples near maximum amplitude
            clipped_samples = np.sum(np.abs(audio) > threshold)
            total_samples = len(audio)
            return clipped_samples / total_samples
        except:
            return 0.0
    
    @staticmethod
    def _calculate_quality_score(metrics: Dict[str, float]) -> float:
        """Calculate overall quality score from metrics"""
        try:
            score = 1.0
            
            # SNR component (0-1)
            snr_score = min(max((metrics['snr'] + 10) / 30, 0), 1)  # -10dB to 20dB range
            score *= (0.3 * snr_score + 0.7)  # Weight SNR
            
            # Voice activity component
            va_score = min(metrics['voice_activity'] / 0.8, 1.0)  # Target 80% voice activity
            score *= (0.2 * va_score + 0.8)
            
            # Clipping penalty
            clipping_penalty = 1.0 - min(metrics['clipping'] * 10, 0.5)  # Max 50% penalty
            score *= clipping_penalty
            
            # Duration component
            if metrics['duration'] < 3.0:  # Less than 3 seconds
                score *= 0.3
            elif metrics['duration'] < 10.0:  # Less than 10 seconds
                score *= 0.8
            
            # Dynamic range component
            if metrics['dynamic_range'] < 0.1:  # Very low dynamic range
                score *= 0.5
            
            return min(max(score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Quality score calculation failed: {e}")
            return 0.0
    
    @staticmethod
    def _generate_recommendations(quality_score: float, metrics: Dict[str, float]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if quality_score < 0.3:
            recommendations.append("Audio quality is too poor for voice training")
        elif quality_score < 0.6:
            recommendations.append("Audio quality needs improvement for best results")
        
        if metrics.get('snr', 0) < 10:
            recommendations.append("Reduce background noise - record in a quieter environment")
        
        if metrics.get('voice_activity', 0) < 0.5:
            recommendations.append("Include more speech content - reduce silent portions")
        
        if metrics.get('clipping', 0) > 0.01:
            recommendations.append("Reduce recording volume to avoid clipping/distortion")
        
        if metrics.get('duration', 0) < 10:
            recommendations.append("Longer samples (30+ seconds) produce better voice models")
        
        if not recommendations:
            recommendations.append("Audio quality is good for voice training")
        
        return recommendations


class AudioProcessor:
    """Main audio processing service"""
    
    def __init__(self):
        self.supported_formats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.aac']
        self.target_sample_rate = 22050
        self.target_format = 'wav'

    async def get_audio_info_from_path(self, path: str) -> Dict[str, Any]:
        """Lightweight audio info by reading a file path."""
        try:
            # Load minimal portion to get sample rate
            audio, sr = librosa.load(path, sr=None, mono=True, duration=0.1)
            duration = float(librosa.get_duration(path=path))
            file_size_bytes = os.path.getsize(path)
            ext = os.path.splitext(path)[1].lower()
            return {
                'filename': os.path.basename(path),
                'format': ext,
                'duration': duration,
                'estimated_duration': duration,
                'sample_rate': sr,
                'file_size_bytes': file_size_bytes,
                'file_size_mb': file_size_bytes / (1024 * 1024),
                'is_supported': ext in self.supported_formats,
                'quality_score': 0.85,
            }
        except Exception as e:
            logger.error(f"Audio info read failed for {path}: {e}")
            return {
                'filename': os.path.basename(path),
                'error': str(e),
                'file_size_bytes': os.path.getsize(path) if os.path.exists(path) else 0,
            }
    
    async def process_audio_file(
        self, 
        audio_data: bytes, 
        original_filename: str,
        target_sr: Optional[int] = None,
        normalize: bool = True,
        trim_silence: bool = True
    ) -> Dict[str, Any]:
        """Process uploaded audio file"""
        try:
            target_sr = target_sr or self.target_sample_rate
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Load audio
                audio, sr = librosa.load(temp_path, sr=target_sr, mono=True)
                
                # Apply preprocessing
                if trim_silence:
                    audio = self._trim_silence(audio, sr)
                
                if normalize:
                    audio = self._normalize_audio(audio)
                
                # Quality analysis
                quality_analysis = AudioQualityAnalyzer.analyze_audio_quality(audio, sr)
                
                # Convert to target format
                processed_audio_bytes = self._audio_to_bytes(audio, sr, self.target_format)
                
                return {
                    'audio_data': processed_audio_bytes,
                    'sample_rate': sr,
                    'duration_seconds': len(audio) / sr,
                    'channels': 1,
                    'format': self.target_format,
                    'quality_analysis': quality_analysis,
                    'file_size_bytes': len(processed_audio_bytes),
                    'preprocessing_applied': {
                        'trimmed_silence': trim_silence,
                        'normalized': normalize,
                        'resampled': sr != librosa.load(temp_path, sr=None)[1]
                    }
                }
                
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Audio processing failed for {original_filename}: {e}")
            raise ValueError(f"Audio processing failed: {e}")
    
    def _trim_silence(self, audio: np.ndarray, sr: int, threshold: float = 0.01) -> np.ndarray:
        """Trim silence from beginning and end"""
        try:
            # Find non-silent regions
            non_silent = librosa.effects.split(audio, top_db=20, frame_length=1024, hop_length=256)
            
            if len(non_silent) == 0:
                return audio  # Return original if no non-silent parts found
            
            # Trim to first and last non-silent regions
            start_sample = max(0, non_silent[0][0] - int(0.1 * sr))  # Keep 0.1s before
            end_sample = min(len(audio), non_silent[-1][1] + int(0.1 * sr))  # Keep 0.1s after
            
            return audio[start_sample:end_sample]
            
        except Exception as e:
            logger.warning(f"Silence trimming failed: {e}")
            return audio
    
    def _normalize_audio(self, audio: np.ndarray, target_level: float = -20.0) -> np.ndarray:
        """Normalize audio to target dB level"""
        try:
            # Calculate current RMS
            current_rms = np.sqrt(np.mean(audio**2))
            
            if current_rms > 0:
                # Calculate target RMS from dB
                target_rms = 10**(target_level/20)
                
                # Apply normalization
                normalized_audio = audio * (target_rms / current_rms)
                
                # Ensure no clipping
                peak = np.max(np.abs(normalized_audio))
                if peak > 0.95:
                    normalized_audio = normalized_audio * (0.95 / peak)
                
                return normalized_audio
            
            return audio
            
        except Exception as e:
            logger.warning(f"Audio normalization failed: {e}")
            return audio
    
    def _audio_to_bytes(self, audio: np.ndarray, sr: int, format: str = 'wav') -> bytes:
        """Convert numpy audio to bytes"""
        try:
            # Create in-memory buffer
            buffer = io.BytesIO()
            
            # Write audio to buffer
            sf.write(buffer, audio, sr, format=format.upper())
            
            # Get bytes
            buffer.seek(0)
            return buffer.read()
            
        except Exception as e:
            logger.error(f"Audio to bytes conversion failed: {e}")
            raise
    
    async def enhance_audio_for_training(self, audio_data: bytes) -> bytes:
        """Enhanced preprocessing specifically for voice training"""
        try:
            # Load audio
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                audio, sr = librosa.load(temp_path, sr=22050, mono=True)
                
                # Advanced preprocessing pipeline
                audio = self._remove_background_noise(audio, sr)
                audio = self._enhance_speech(audio, sr)
                audio = self._normalize_audio(audio, target_level=-12.0)  # Higher level for training
                
                return self._audio_to_bytes(audio, sr)
                
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Audio enhancement failed: {e}")
            raise
    
    def _remove_background_noise(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Simple noise reduction using spectral gating"""
        try:
            # Estimate noise floor from quietest 10%
            sorted_power = np.sort(audio**2)
            noise_floor = np.mean(sorted_power[:int(len(sorted_power) * 0.1)])
            
            # Apply spectral gating
            threshold = noise_floor * 3  # 3x noise floor
            mask = audio**2 > threshold
            
            # Smooth the mask to avoid artifacts
            mask_smooth = savgol_filter(mask.astype(float), window_length=51, polyorder=3)
            mask_smooth = np.clip(mask_smooth, 0.1, 1.0)  # Minimum 10% of signal
            
            return audio * mask_smooth
            
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return audio
    
    def _enhance_speech(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Enhance speech clarity"""
        try:
            # Simple pre-emphasis filter to boost high frequencies
            pre_emphasis = 0.97
            emphasized_audio = np.append(audio[0], audio[1:] - pre_emphasis * audio[:-1])
            
            return emphasized_audio
            
        except Exception as e:
            logger.warning(f"Speech enhancement failed: {e}")
            return audio
    
    def validate_audio_format(self, filename: str, audio_data: bytes) -> Dict[str, Any]:
        """Validate if audio file is in supported format"""
        try:
            # Check file extension
            file_ext = os.path.splitext(filename.lower())[1]
            
            if file_ext not in self.supported_formats:
                return {
                    'valid': False,
                    'reason': f'Unsupported format: {file_ext}',
                    'supported_formats': self.supported_formats
                }
            
            # Try to load the file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Attempt to load audio
                audio, sr = librosa.load(temp_path, sr=None, duration=1.0)  # Load first second only
                
                # Basic validation
                if len(audio) == 0:
                    return {'valid': False, 'reason': 'Audio file is empty or corrupted'}
                
                if sr < 8000:
                    return {'valid': False, 'reason': 'Sample rate too low (minimum 8kHz required)'}
                
                return {
                    'valid': True,
                    'detected_format': file_ext,
                    'sample_rate': sr,
                    'estimated_duration': len(audio) / sr,
                    'mono_converted': True
                }
                
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            return {
                'valid': False,
                'reason': f'Audio validation failed: {str(e)}',
                'error_type': type(e).__name__
            }
    
    async def batch_process_samples(
        self, 
        audio_samples: List[Tuple[bytes, str]]  # List of (audio_data, filename)
    ) -> List[Dict[str, Any]]:
        """Process multiple audio samples in batch"""
        results = []
        
        for audio_data, filename in audio_samples:
            try:
                result = await self.process_audio_file(audio_data, filename)
                result['filename'] = filename
                result['status'] = 'success'
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch processing failed for {filename}: {e}")
                results.append({
                    'filename': filename,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results
    
    def get_audio_info(self, audio_data: bytes, filename: str) -> Dict[str, Any]:
        """Get basic audio file information without full processing"""
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Load metadata only
                audio, sr = librosa.load(temp_path, sr=None, duration=0.1)  # Load tiny portion
                
                # Get file size and format
                file_ext = os.path.splitext(filename.lower())[1]
                
                # Estimate full duration
                total_frames = librosa.get_duration(path=temp_path)
                
                return {
                    'filename': filename,
                    'format': file_ext,
                    'duration': total_frames,  # For backward compatibility
                    'estimated_duration': total_frames,
                    'sample_rate': sr,
                    'file_size_bytes': len(audio_data),
                    'file_size_mb': len(audio_data) / (1024 * 1024),
                    'is_supported': file_ext in self.supported_formats
                }
                
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Audio info extraction failed for {filename}: {e}")
            return {
                'filename': filename,
                'error': str(e),
                'file_size_bytes': len(audio_data)
            }


# Global audio processor instance
audio_processor = AudioProcessor()