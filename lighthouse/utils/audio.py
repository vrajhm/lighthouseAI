"""Audio processing utilities for Lighthouse.ai"""

import io
import wave
import numpy as np
import pyaudio
import sounddevice as sd
from typing import Optional, Callable, List, Tuple
import webrtcvad
from dataclasses import dataclass

from lighthouse.utils.logging import get_logger, LoggerMixin
from lighthouse.config.settings import get_settings


@dataclass
class AudioConfig:
    """Audio configuration parameters"""
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    format: int = pyaudio.paInt16
    vad_aggressiveness: int = 2
    silence_threshold: float = 0.5
    min_silence_duration: float = 0.5
    min_speech_duration: float = 0.3


class AudioCapture(LoggerMixin):
    """Audio capture with voice activity detection"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.settings = get_settings()
        
        # Initialize VAD
        self.vad = webrtcvad.Vad(self.config.vad_aggressiveness)
        
        # Audio buffer
        self.audio_buffer: List[bytes] = []
        self.is_recording = False
        
        # Initialize PyAudio
        try:
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            self.logger.error("Failed to initialize PyAudio", error=str(e))
            raise
    
    def list_audio_devices(self) -> List[dict]:
        """List available audio devices"""
        devices = []
        try:
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:  # Input device
                    devices.append({
                        'index': i,
                        'name': info['name'],
                        'channels': info['maxInputChannels'],
                        'sample_rate': info['defaultSampleRate']
                    })
        except Exception as e:
            self.logger.error("Failed to list audio devices", error=str(e))
        
        return devices
    
    def get_default_input_device(self) -> Optional[int]:
        """Get the default input device index"""
        try:
            default_device = self.audio.get_default_input_device_info()
            return default_device['index']
        except Exception as e:
            self.logger.error("Failed to get default input device", error=str(e))
            return None
    
    def start_recording(self, callback: Optional[Callable[[bytes], None]] = None) -> None:
        """Start audio recording with VAD"""
        if self.is_recording:
            self.logger.warning("Already recording")
            return
        
        self.is_recording = True
        self.audio_buffer = []
        
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=self.config.format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                frames_per_buffer=self.config.chunk_size,
                stream_callback=self._audio_callback if callback else None
            )
            
            if not callback:
                self.stream.start_stream()
            
            self.logger.info("Started audio recording")
            
        except Exception as e:
            self.logger.error("Failed to start recording", error=str(e))
            self.is_recording = False
            raise
    
    def stop_recording(self) -> bytes:
        """Stop recording and return audio data"""
        if not self.is_recording:
            self.logger.warning("Not currently recording")
            return b""
        
        self.is_recording = False
        
        try:
            if hasattr(self, 'stream'):
                self.stream.stop_stream()
                self.stream.close()
            
            # Combine all audio chunks
            audio_data = b''.join(self.audio_buffer)
            self.audio_buffer = []
            
            self.logger.info("Stopped audio recording", audio_length=len(audio_data))
            return audio_data
            
        except Exception as e:
            self.logger.error("Failed to stop recording", error=str(e))
            return b""
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback for real-time processing"""
        if status:
            self.logger.warning("Audio callback status", status=status)
        
        if self.is_recording:
            self.audio_buffer.append(in_data)
        
        return (in_data, pyaudio.paContinue)
    
    def detect_speech(self, audio_data: bytes) -> bool:
        """Detect if audio contains speech using VAD"""
        if len(audio_data) < 320:  # Minimum frame size for VAD
            return False
        
        try:
            # VAD expects 10ms, 20ms, or 30ms frames
            frame_duration = 20  # 20ms
            frame_size = int(self.config.sample_rate * frame_duration / 1000)
            
            # Process audio in frames
            for i in range(0, len(audio_data) - frame_size, frame_size):
                frame = audio_data[i:i + frame_size]
                if self.vad.is_speech(frame, self.config.sample_rate):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error("VAD detection failed", error=str(e))
            return False
    
    def record_until_silence(self, max_duration: float = 10.0) -> bytes:
        """Record audio until silence is detected or max duration reached"""
        self.start_recording()
        
        import time
        start_time = time.time()
        last_speech_time = start_time
        
        try:
            while self.is_recording:
                # Read audio chunk
                chunk = self.stream.read(self.config.chunk_size, exception_on_overflow=False)
                
                # Check for speech
                if self.detect_speech(chunk):
                    last_speech_time = time.time()
                    self.audio_buffer.append(chunk)
                else:
                    # Check if we've been silent long enough
                    silence_duration = time.time() - last_speech_time
                    if silence_duration > self.config.min_silence_duration:
                        break
                
                # Check max duration
                if time.time() - start_time > max_duration:
                    break
            
            return self.stop_recording()
            
        except Exception as e:
            self.logger.error("Recording failed", error=str(e))
            self.stop_recording()
            return b""
    
    def cleanup(self):
        """Clean up audio resources"""
        if hasattr(self, 'stream'):
            try:
                self.stream.close()
            except:
                pass
        
        try:
            self.audio.terminate()
        except:
            pass


class AudioProcessor:
    """Audio processing utilities"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    @staticmethod
    def bytes_to_numpy(audio_bytes: bytes, sample_rate: int = 16000) -> np.ndarray:
        """Convert audio bytes to numpy array"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Normalize to float32
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            return audio_float
            
        except Exception as e:
            raise ValueError(f"Failed to convert audio bytes: {e}")
    
    @staticmethod
    def numpy_to_bytes(audio_array: np.ndarray) -> bytes:
        """Convert numpy array to audio bytes"""
        try:
            # Convert float32 to int16
            audio_int16 = (audio_array * 32767).astype(np.int16)
            
            # Convert to bytes
            return audio_int16.tobytes()
            
        except Exception as e:
            raise ValueError(f"Failed to convert numpy array: {e}")
    
    @staticmethod
    def save_wav(audio_bytes: bytes, filename: str, sample_rate: int = 16000) -> None:
        """Save audio bytes to WAV file"""
        try:
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_bytes)
        except Exception as e:
            raise ValueError(f"Failed to save WAV file: {e}")
    
    @staticmethod
    def load_wav(filename: str) -> Tuple[bytes, int]:
        """Load WAV file and return audio bytes and sample rate"""
        try:
            with wave.open(filename, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                audio_bytes = wav_file.readframes(wav_file.getnframes())
                return audio_bytes, sample_rate
        except Exception as e:
            raise ValueError(f"Failed to load WAV file: {e}")
    
    def normalize_audio(self, audio_array: np.ndarray) -> np.ndarray:
        """Normalize audio to prevent clipping"""
        try:
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_array**2))
            
            if rms > 0:
                # Normalize to 0.1 RMS
                target_rms = 0.1
                normalized = audio_array * (target_rms / rms)
                
                # Clip to prevent overflow
                return np.clip(normalized, -1.0, 1.0)
            
            return audio_array
            
        except Exception as e:
            self.logger.error("Audio normalization failed", error=str(e))
            return audio_array
