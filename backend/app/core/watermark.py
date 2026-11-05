"""
Whicoustic Watermarking System - Core Implementation

This module implements both MVP (sine-based) and production (spread-spectrum) 
watermarking for audio files with cryptographic verification.
"""

import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from typing import Optional, Tuple, Dict, Any
import hashlib
import hmac
import json
from datetime import datetime
import logging
import os
try:
    import reedsolo
except ImportError:
    reedsolo = None

logger = logging.getLogger(__name__)

class WatermarkEncoder:
    """Handles embedding watermarks into audio files."""
    
    def __init__(self, secret_key: str = "whicoustic_default_key"):
        self.secret_key = secret_key.encode('utf-8')
        self.sample_rate = 44100  # Standard sample rate for processing
        
    def embed_mvp_watermark(
        self,
        audio_path: str,
        watermark_id: str,
        output_path: str,
        frequency: float = 19000.0,
        amplitude: float = 0.001
    ) -> str:
        """
        Embed MVP watermark using high-frequency sine tone.
        
        Args:
            audio_path: Path to input audio file
            watermark_id: Unique watermark identifier
            output_path: Path for watermarked output
            frequency: Watermark frequency in Hz (default 19kHz)
            amplitude: Watermark amplitude (very low to be inaudible)
            
        Returns:
            Path to watermarked audio file
        """
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = len(audio) / sr
            
            # Generate time array
            t = np.linspace(0, duration, len(audio), False)
            
            # Create watermark signal with encoded ID
            watermark_signal = self._encode_id_in_sine(
                t, watermark_id, frequency, amplitude
            )
            
            # Embed watermark
            watermarked_audio = audio + watermark_signal
            
            # Ensure no clipping
            watermarked_audio = np.clip(watermarked_audio, -0.99, 0.99)
            
            # Save watermarked audio
            sf.write(output_path, watermarked_audio, sr)
            
            logger.info(f"MVP watermark embedded: {watermark_id} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"MVP watermark embedding failed: {e}")
            raise
    
    def embed_robust_watermark(
        self,
        audio_path: str,
        watermark_id: str,
        license_id: Optional[str],
        output_path: str
    ) -> str:
        """
        Embed robust spread-spectrum watermark with error correction.
        
        Args:
            audio_path: Path to input audio file
            watermark_id: Unique watermark identifier
            license_id: License identifier (optional)
            output_path: Path for watermarked output
            
        Returns:
            Path to watermarked audio file
        """
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Create watermark payload with HMAC signature
            payload = self._create_payload(watermark_id, license_id)
            
            # Apply spread-spectrum watermarking
            watermarked_audio = self._spread_spectrum_embed(audio, payload)
            
            # Save watermarked audio
            sf.write(output_path, watermarked_audio, sr)
            
            logger.info(f"Robust watermark embedded: {watermark_id} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Robust watermark embedding failed: {e}")
            raise
    
    def _encode_id_in_sine(
        self, 
        t: np.ndarray, 
        watermark_id: str, 
        base_freq: float, 
        amplitude: float
    ) -> np.ndarray:
        """Encode watermark ID in sine wave using frequency modulation."""
        
        # Create hash of watermark_id for consistent encoding
        id_hash = hashlib.md5(watermark_id.encode()).hexdigest()
        
        # Convert hash to binary representation
        binary_data = ''.join(format(ord(c), '08b') for c in id_hash[:8])  # Use first 8 chars
        
        # Modulate frequency based on binary data
        watermark_signal = np.zeros_like(t)
        bit_duration = len(t) / len(binary_data)
        
        for i, bit in enumerate(binary_data):
            start_idx = int(i * bit_duration)
            end_idx = int((i + 1) * bit_duration)
            
            # Use different frequencies for 0 and 1
            freq = base_freq if bit == '1' else base_freq - 100
            watermark_signal[start_idx:end_idx] = amplitude * np.sin(
                2 * np.pi * freq * t[start_idx:end_idx]
            )
        
        return watermark_signal
    
    def _create_payload(self, watermark_id: str, license_id: Optional[str]) -> bytes:
        """Create watermark payload with error correction."""
        
        # Create payload dictionary
        payload_data = {
            'watermark_id': watermark_id,
            'license_id': license_id,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
        
        # Convert to JSON bytes
        json_payload = json.dumps(payload_data, separators=(',', ':')).encode('utf-8')
        
        # Add HMAC signature for verification
        signature = hmac.new(self.secret_key, json_payload, hashlib.sha256).digest()
        
        # Combine payload and signature
        full_payload = json_payload + signature
        
        return full_payload
    
    def _spread_spectrum_embed(self, audio: np.ndarray, payload: bytes) -> np.ndarray:
        """Embed payload using Echo Hiding for robust extraction with repetition and ECC."""
        # Add ECC
        rs = reedsolo.RSCodec(10)
        encoded_payload = bytes(rs.encode(payload))
        
        # Convert payload to bits
        payload_with_marker = encoded_payload + b'\xff\x00'
        binary_payload = ''.join(format(b, '08b') for b in payload_with_marker)
        
        # Echo delays for 0 and 1 bits (in seconds)
        delay_0 = int(0.020 * self.sample_rate)
        delay_1 = int(0.025 * self.sample_rate)
        
        # Segment length (e.g. 50ms)
        segment_length = int(0.05 * self.sample_rate)
        
        required_bits = len(binary_payload)
        watermark_duration = required_bits * segment_length
        
        watermarked_audio = audio.copy()
        
        # Calculate global RMS for psychoacoustic scaling
        global_rms = np.sqrt(np.mean(audio**2)) + 1e-6
        
        # Repeat the payload across the audio
        num_repeats = max(1, len(audio) // watermark_duration)
        
        for repeat_idx in range(num_repeats):
            offset = repeat_idx * watermark_duration
            
            for i, bit in enumerate(binary_payload):
                start = offset + i * segment_length
                end = start + segment_length
                
                if end > len(audio):
                    break
                    
                delay = delay_1 if bit == '1' else delay_0
                
                # Embed echo in this segment
                segment = audio[start:end]
                
                # Psychoacoustic shaping: scale alpha based on local RMS vs global RMS
                local_rms = np.sqrt(np.mean(segment**2)) + 1e-6
                # Range 0.3 to 0.7 depending on relative loudness
                alpha = np.clip(0.3 + 0.4 * (local_rms / global_rms), 0.3, 0.7)
                
                echo = np.zeros_like(segment)
                if delay < len(segment):
                    echo[delay:] = segment[:-delay]
                    
                # Add echo to original audio
                watermarked_audio[start:end] = segment + alpha * echo
                
        return np.clip(watermarked_audio, -0.99, 0.99)


class WatermarkDecoder:
    """Handles detection and extraction of watermarks from audio files."""
    
    def __init__(self, secret_key: str = "whicoustic_default_key"):
        self.secret_key = secret_key.encode('utf-8')
        self.sample_rate = 44100
    
    def detect_mvp_watermark(
        self, 
        audio_path: str, 
        frequency: float = 19000.0,
        threshold: float = 1e-9
    ) -> Optional[Dict[str, Any]]:
        """
        Detect MVP watermark and extract watermark ID.

        This detector must be conservative: real human speech contains natural high-frequency
        content and mic/room noise, so a tiny spectral peak is not enough to classify audio as
        synthetic. Only strong, stable spectral energy around the expected watermark frequency
        with a valid decoded ID qualifies as a positive match.
        """
        try:
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            fft = np.fft.fft(audio)
            freqs = np.fft.fftfreq(len(audio), 1/sr)

            target_bin = np.argmin(np.abs(freqs - frequency))
            magnitude = float(np.abs(fft[target_bin]) / len(audio))

            # Use a local median around the target bin so incidental hum/noise does not
            # trigger a false positive on normal human speech.
            half_window = max(5, int(len(freqs) * 0.0005))
            start = max(0, target_bin - half_window)
            end = min(len(freqs), target_bin + half_window + 1)
            local_magnitudes = np.abs(fft[start:end]) / len(audio)
            local_baseline = float(np.median(local_magnitudes)) if local_magnitudes.size else 0.0
            detection_threshold = max(float(threshold), 5.0 * max(local_baseline, 1e-12))

            if magnitude <= detection_threshold:
                return {'found': False, 'confidence': 0.0, 'magnitude': magnitude, 'threshold': detection_threshold}

            watermark_id = self._decode_id_from_sine(audio, frequency)
            if watermark_id == 'unknown_id':
                return {'found': False, 'confidence': 0.0, 'magnitude': magnitude, 'threshold': detection_threshold}

            confidence = float(min(1.0, 0.85 + 0.15 * (magnitude / max(detection_threshold * 2.0, 1e-12))))
            if confidence < 0.85:
                return {'found': False, 'confidence': round(confidence, 4), 'magnitude': magnitude, 'threshold': detection_threshold}

            print(f"MVP Detection: ID={watermark_id}, Magnitude={magnitude}, Threshold={detection_threshold}, Confidence={confidence}")

            return {
                'found': True,
                'watermark_id': watermark_id,
                'confidence': round(confidence, 4),
                'detection_method': 'mvp_sine',
                'frequency': float(frequency),
                'magnitude': float(magnitude),
                'threshold': float(detection_threshold)
            }

        except Exception as e:
            logger.error(f"MVP watermark detection failed: {e}")
            return {'found': False, 'error': str(e)}

    def detect_robust_watermark(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Detect robust spread-spectrum watermark with repetition support.

        Only return positive results when a payload survives verification and remains strong
        enough to be credible; weak or unverified candidates are treated as absent.
        """
        try:
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            payloads = self._spread_spectrum_extract(audio)

            for payload in payloads:
                result = self._verify_and_parse_payload(payload)
                if result and float(result.get('confidence', 0.0)) >= 0.85:
                    result['detection_method'] = 'robust_echo_hiding'
                    return result

            print("Robust Detection: No valid watermark found in any candidate payloads")
            return {'found': False, 'confidence': 0.0}

        except Exception as e:
            logger.error(f"Robust watermark detection failed: {e}")
            return {'found': False, 'error': str(e)}
    
    def _decode_id_from_sine(self, audio: np.ndarray, base_freq: float) -> str:
        """Decode watermark ID from frequency-modulated sine wave."""
        # Find the dominant frequencies over time windows using STFT
        # We encoded 8 bytes (64 bits) of MD5 hash
        n_bits = 64
        bit_duration = len(audio) / n_bits
        
        binary_data = ""
        # The two frequencies used in encoding
        freq_1 = base_freq
        freq_0 = base_freq - 100
        
        # Calculate FFT for each bit window
        for i in range(n_bits):
            start_idx = int(i * bit_duration)
            end_idx = int((i + 1) * bit_duration)
            
            # Extract window
            window = audio[start_idx:end_idx]
            if len(window) == 0:
                binary_data += "0"
                continue
                
            # Compute FFT
            fft = np.fft.fft(window)
            freqs = np.fft.fftfreq(len(window), 1/self.sample_rate)
            
            # Find the bins for freq_1 and freq_0
            bin_1 = np.argmin(np.abs(freqs - freq_1))
            bin_0 = np.argmin(np.abs(freqs - freq_0))
            
            # Compare magnitudes
            mag_1 = np.abs(fft[bin_1])
            mag_0 = np.abs(fft[bin_0])
            
            if mag_1 > mag_0:
                binary_data += "1"
            else:
                binary_data += "0"
                
        # Try to infer the ID from the 8 extracted characters (which match the first 8 of the MD5 hash)
        # Note: The original ID can only be cryptographically matched, but for the MVP proof-of-concept,
        # we will just return the hex representation of the identified bits since we hash the original ID!
        try:
            # Convert binary string to hex
            hex_id = hex(int(binary_data, 2))[2:].zfill(16)
            return hex_id
        except Exception:
            return "unknown_id"
    
    def _spread_spectrum_extract(self, audio: np.ndarray) -> list[bytes]:
        """Extract all candidate payloads from Echo Hiding watermark using sliding-window cepstrum analysis."""
        try:
            delay_0 = int(0.020 * self.sample_rate)
            delay_1 = int(0.025 * self.sample_rate)
            segment_length = int(0.05 * self.sample_rate)
            
            all_candidates = []
            
            # Sliding window offsets: try every 10ms (0 to 40ms)
            step_samples = int(0.01 * self.sample_rate)
            offsets = list(range(0, segment_length, step_samples))
            
            rs = reedsolo.RSCodec(10)
            
            for offset in offsets:
                max_bits = (len(audio) - offset) // segment_length
                binary_payload = ""
                
                for i in range(max_bits):
                    start = offset + i * segment_length
                    end = start + segment_length
                    segment = audio[start:end]
                    
                    if len(segment) < segment_length:
                        break
                    
                    # Compute real cepstrum
                    spectrum = np.fft.fft(segment)
                    log_spectrum = np.log(np.abs(spectrum) + 1e-10)
                    cepstrum = np.real(np.fft.ifft(log_spectrum))
                    
                    # Check for peaks near delay_0 and delay_1
                    peak_0 = max(cepstrum[delay_0-1:delay_0+2])
                    peak_1 = max(cepstrum[delay_1-1:delay_1+2])
                    
                    if peak_1 > peak_0:
                        binary_payload += '1'
                    else:
                        binary_payload += '0'
                        
                byte_array = bytearray()
                for i in range(0, len(binary_payload) - 7, 8):
                    byte_str = binary_payload[i:i+8]
                    byte_val = int(byte_str, 2)
                    byte_array.append(byte_val)
                    
                # Split byte array by the marker \xff\x00 to get all candidate payloads
                candidates = byte_array.split(b'\xff\x00')
                
                for c in candidates:
                    if not c:
                        continue
                    try:
                        decoded = bytes(rs.decode(c)[0])
                        all_candidates.append(decoded)
                    except reedsolo.ReedSolomonError:
                        # Also append raw in case it wasn't ECC encoded (backward compatibility)
                        all_candidates.append(bytes(c))
                        
            return all_candidates
            
        except Exception as e:
            logger.error(f"Echo Hiding extraction error: {e}")
            return []
    
    def _verify_and_parse_payload(self, payload: bytes) -> Optional[Dict[str, Any]]:
        """Verify HMAC signature and parse payload from padded byte array."""
        try:
            # Find the JSON structure ending based on finding '}'
            # Then the next 32 bytes are the signature. But what if there's noise at the end?
            # It's safer to just search for the last '}' and assume the signature immediately follows.
            
            end_idx = payload.rfind(b'}')
            if end_idx == -1:
                return None
                
            json_payload = payload[:end_idx+1]
            signature = payload[end_idx+1:end_idx+33]
            
            if len(signature) < 32:
                logger.warning("Missing signature bytes")
                return None
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key, json_payload, hashlib.sha256
            ).digest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("Watermark signature verification failed")
                return None
            
            # Parse JSON payload
            payload_data = json.loads(json_payload.decode('utf-8'))
            
            return {
                'found': True,
                'watermark_id': payload_data['watermark_id'],
                'license_id': payload_data.get('license_id'),
                'timestamp': payload_data['timestamp'],
                'version': payload_data['version'],
                'confidence': 1.0,
                'signature_valid': True
            }
            
        except Exception as e:
            logger.error(f"Payload verification failed: {e}")
            return None


class WatermarkService:
    """High-level watermarking service interface."""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv('WATERMARK_SECRET_KEY', 'whicoustic_default_key')
        self.encoder = WatermarkEncoder(self.secret_key)
        self.decoder = WatermarkDecoder(self.secret_key)
    
    async def embed_watermark(
        self,
        audio_path: str,
        watermark_id: str,
        license_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        method: str = 'mvp'
    ) -> str:
        """
        Embed watermark in audio file.
        
        Args:
            audio_path: Input audio file path
            watermark_id: Unique watermark identifier
            license_id: License identifier (optional)
            voice_id: Voice identifier for tracking
            method: Watermarking method ('mvp' or 'robust')
            
        Returns:
            Path to watermarked audio file
        """
        # Generate output path
        base_name = os.path.splitext(audio_path)[0]
        output_path = f"{base_name}_watermarked.wav"
        
        if method == 'mvp':
            return self.encoder.embed_mvp_watermark(
                audio_path, watermark_id, output_path
            )
        elif method == 'robust':
            return self.encoder.embed_robust_watermark(
                audio_path, watermark_id, license_id, output_path
            )
        else:
            raise ValueError(f"Unknown watermarking method: {method}")
    
    async def detect_watermark(
        self, 
        audio_path: str, 
        method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect watermark in audio file.
        
        Args:
            audio_path: Audio file path to analyze
            method: Detection method ('mvp', 'robust', or None for auto-detect)
            
        Returns:
            Detection results
        """
        if method == 'mvp':
            return self.decoder.detect_mvp_watermark(audio_path)
        elif method == 'robust':
            return self.decoder.detect_robust_watermark(audio_path)
        else:
            # Try both methods
            mvp_result = self.decoder.detect_mvp_watermark(audio_path)
            if mvp_result.get('found'):
                return mvp_result
            
            robust_result = self.decoder.detect_robust_watermark(audio_path)
            return robust_result if robust_result.get('found') else mvp_result

    async def detect_watermark_array(
        self,
        audio: np.ndarray,
        sr: int = 44100,
        method: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detect watermark directly from an in-memory numpy array.

        Streaming variant (Phase 4): StreamSession calls this with a snapshot
        of its circular buffer rather than a file path. Internally writes a
        temporary WAV then delegates to detect_watermark(), preserving all
        existing decode logic.

        Args:
            audio: 1-D int16 or float32 numpy array of audio samples, mono.
            sr: Sample rate of the audio (default 44100 to match WatermarkEncoder).
            method: Detection method ('mvp', 'robust', or None for auto-detect).

        Returns:
            Same dict as detect_watermark().
        """
        import tempfile
        import soundfile as sf  # type: ignore

        # Normalise to float32 [-1, 1] for soundfile
        if audio.dtype == np.int16:
            audio_f = audio.astype(np.float32) / 32768.0
        else:
            audio_f = np.asarray(audio, dtype=np.float32)

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            sf.write(tmp_path, audio_f, sr)
            result = await self.detect_watermark(tmp_path, method=method)
            return result
        except Exception as exc:
            logger.error("detect_watermark_array failed: %s", exc)
            return {"found": False, "error": str(exc)}
        finally:
            try:
                import os as _os
                _os.unlink(tmp_path)
            except Exception:
                pass
