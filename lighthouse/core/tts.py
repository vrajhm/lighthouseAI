"""Text-to-Speech module using Coqui TTS for Lighthouse.ai"""

import os
import time
import threading
import queue
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import numpy as np
import sounddevice as sd
import pyttsx3
try:
    import objc
except ImportError:
    objc = None

from lighthouse.utils.logging import get_logger, LoggerMixin
from lighthouse.config.settings import get_settings


@dataclass
class TTSConfig:
    """TTS configuration parameters"""
    model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"
    speaker_id: int = 0
    speed: float = 1.0
    sample_rate: int = 22050
    device: str = "auto"


@dataclass
class SpeechResult:
    """Result of text-to-speech synthesis"""
    audio_data: np.ndarray
    sample_rate: int
    duration: float
    text: str
    success: bool
    error: Optional[str] = None


class TTSQueue:
    """Thread-safe queue for TTS audio playback"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.stop_event = threading.Event()
        self.playback_thread = None
        self.logger = get_logger(self.__class__.__name__)
    
    def add_audio(self, audio_data: np.ndarray) -> None:
        """Add audio data to playback queue"""
        self.audio_queue.put(audio_data)
        self.logger.debug("Added audio to queue", queue_size=self.audio_queue.qsize())
    
    def start_playback(self) -> None:
        """Start audio playback thread"""
        if self.is_playing:
            return
        
        self.is_playing = True
        self.stop_event.clear()
        self.playback_thread = threading.Thread(target=self._playback_worker)
        self.playback_thread.daemon = True
        self.playback_thread.start()
        self.logger.info("Started TTS playback")
    
    def stop_playback(self) -> None:
        """Stop audio playback"""
        if not self.is_playing:
            return
        
        self.stop_event.set()
        self.is_playing = False
        
        if self.playback_thread:
            self.playback_thread.join(timeout=1.0)
        
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        self.logger.info("Stopped TTS playback")
    
    def _playback_worker(self) -> None:
        """Audio playback worker thread"""
        try:
            while not self.stop_event.is_set():
                try:
                    # Get audio data with timeout
                    audio_data = self.audio_queue.get(timeout=0.1)
                    
                    if audio_data is not None:
                        # Play audio
                        sd.play(audio_data, samplerate=self.sample_rate)
                        sd.wait()  # Wait for playback to complete
                    
                    self.audio_queue.task_done()
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.error("Playback error", error=str(e))
                    
        except Exception as e:
            self.logger.error("Playback worker error", error=str(e))
        finally:
            self.is_playing = False


class PyTTSX3Service(LoggerMixin):
    """Text-to-Speech service using pyttsx3"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        self.settings = get_settings()
        self.config = config or TTSConfig(
            model_name="pyttsx3",
            speaker_id=0,
            speed=self.settings.tts_speed
        )
        
        # Initialize TTS engine
        self.tts_engine = None
        self._load_engine()
    
    def _load_engine(self) -> None:
        """Load the TTS engine"""
        try:
            self.logger.info("Loading TTS engine")
            
            # Initialize pyttsx3 engine
            self.tts_engine = pyttsx3.init()
            
            # Set properties
            self.tts_engine.setProperty('rate', int(200 * self.config.speed))  # Speed
            self.tts_engine.setProperty('volume', 0.9)  # Volume
            
            self.logger.info("TTS engine loaded successfully")
            
        except Exception as e:
            self.logger.error("Failed to load TTS engine", error=str(e))
            # Don't raise - allow the service to continue without TTS
            self.tts_engine = None
    
    def synthesize(self, text: str, speaker_id: Optional[int] = None) -> SpeechResult:
        """Synthesize text to speech"""
        if not self.tts_engine:
            return SpeechResult(
                audio_data=np.array([]),
                sample_rate=22050,
                duration=0.0,
                text=text,
                success=False,
                error="TTS engine not available"
            )
        
        start_time = time.time()
        
        try:
            # Clean and prepare text
            clean_text = self._clean_text(text)
            
            if not clean_text:
                return SpeechResult(
                    audio_data=np.array([]),
                    sample_rate=22050,  # Default sample rate
                    duration=0.0,
                    text=text,
                    success=False,
                    error="Empty text after cleaning"
                )
            
            # For pyttsx3, we'll just return success since it plays directly
            duration = time.time() - start_time
            
            result = SpeechResult(
                audio_data=np.array([]),  # pyttsx3 doesn't return audio data
                sample_rate=22050,
                duration=duration,
                text=clean_text,
                success=True
            )
            
            self.logger.info(
                "Speech synthesis completed",
                text_length=len(clean_text),
                synthesis_time=duration
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Speech synthesis failed", error=str(e))
            return SpeechResult(
                audio_data=np.array([]),
                sample_rate=22050,
                duration=time.time() - start_time,
                text=text,
                success=False,
                error=str(e)
            )
    
    def speak(self, text: str, speaker_id: Optional[int] = None, blocking: bool = True) -> SpeechResult:
        """Synthesize and play speech"""
        if not self.tts_engine:
            raise RuntimeError("TTS engine not loaded")
        
        start_time = time.time()
        
        try:
            # Clean and prepare text
            clean_text = self._clean_text(text)
            
            if not clean_text:
                return SpeechResult(
                    audio_data=np.array([]),
                    sample_rate=22050,
                    duration=0.0,
                    text=text,
                    success=False,
                    error="Empty text after cleaning"
                )
            
            # Speak the text
            self.tts_engine.say(clean_text)
            
            if blocking:
                self.tts_engine.runAndWait()
            
            duration = time.time() - start_time
            
            result = SpeechResult(
                audio_data=np.array([]),
                sample_rate=22050,
                duration=duration,
                text=clean_text,
                success=True
            )
            
            self.logger.info(
                "Speech completed",
                text_length=len(clean_text),
                duration=duration
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Speech failed", error=str(e))
            return SpeechResult(
                audio_data=np.array([]),
                sample_rate=22050,
                duration=time.time() - start_time,
                text=text,
                success=False,
                error=str(e)
            )
    
    def speak_async(self, text: str, speaker_id: Optional[int] = None) -> SpeechResult:
        """Synthesize and play speech asynchronously"""
        return self.speak(text, speaker_id, blocking=False)
    
    def _clean_text(self, text: str) -> str:
        """Clean text for TTS synthesis"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Handle common abbreviations
        abbreviations = {
            "Dr.": "Doctor",
            "Mr.": "Mister",
            "Mrs.": "Misses",
            "Ms.": "Miss",
            "Prof.": "Professor",
            "etc.": "etcetera",
            "vs.": "versus",
            "e.g.": "for example",
            "i.e.": "that is",
            "etc.": "etcetera"
        }
        
        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)
        
        # Remove special characters that might cause issues
        import re
        text = re.sub(r'[^\w\s.,!?;:\-()]', '', text)
        
        return text.strip()
    
    def _adjust_speed(self, audio_data: np.ndarray, speed: float) -> np.ndarray:
        """Adjust speech speed using simple resampling"""
        if speed == 1.0:
            return audio_data
        
        try:
            # Simple speed adjustment by resampling
            from scipy import signal
            
            # Calculate new length
            new_length = int(len(audio_data) / speed)
            
            # Resample
            resampled = signal.resample(audio_data, new_length)
            
            return resampled.astype(audio_data.dtype)
            
        except ImportError:
            self.logger.warning("scipy not available, skipping speed adjustment")
            return audio_data
        except Exception as e:
            self.logger.error("Speed adjustment failed", error=str(e))
            return audio_data
    
    def get_available_models(self) -> List[str]:
        """Get list of available TTS models"""
        try:
            return self.model_manager.list_models()
        except Exception as e:
            self.logger.error("Failed to list models", error=str(e))
            return []
    
    def get_available_speakers(self) -> List[int]:
        """Get list of available speakers for current model"""
        try:
            if hasattr(self.tts_model, 'speakers') and self.tts_model.speakers:
                return list(range(len(self.tts_model.speakers)))
            return [0]  # Default speaker
        except Exception as e:
            self.logger.error("Failed to get speakers", error=str(e))
            return [0]
    
    def cleanup(self) -> None:
        """Clean up TTS resources"""
        try:
            self.audio_queue.stop_playback()
            self.logger.info("TTS service cleaned up")
        except Exception as e:
            self.logger.error("TTS cleanup failed", error=str(e))


class CloudTTSProvider:
    """Abstract base class for cloud TTS providers"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def synthesize(self, text: str, voice: str = "default") -> SpeechResult:
        """Synthesize text to speech"""
        raise NotImplementedError
    
    def get_available_voices(self) -> List[str]:
        """Get available voices"""
        raise NotImplementedError


class AzureTTSProvider(CloudTTSProvider):
    """Azure Cognitive Services TTS provider"""
    
    def __init__(self, api_key: str, region: str):
        super().__init__()
        self.api_key = api_key
        self.region = region
        # Implementation would go here
    
    def synthesize(self, text: str, voice: str = "default") -> SpeechResult:
        # Implementation would go here
        raise NotImplementedError("Azure TTS not implemented yet")


class TTSManager:
    """Manager for TTS operations with local and cloud support"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.settings = get_settings()
        
        # Initialize local TTS
        self.local_tts = None
        self.cloud_providers = {}
        
        self._initialize_local_tts()
        self._initialize_cloud_providers()
    
    def _initialize_local_tts(self) -> None:
        """Initialize local TTS service"""
        try:
            self.local_tts = PyTTSX3Service()
            self.logger.info("Local TTS initialized")
        except Exception as e:
            self.logger.error("Failed to initialize local TTS", error=str(e))
    
    def _initialize_cloud_providers(self) -> None:
        """Initialize cloud TTS providers if configured"""
        if self.settings.azure_speech_key and self.settings.azure_speech_region:
            try:
                self.cloud_providers['azure'] = AzureTTSProvider(
                    self.settings.azure_speech_key,
                    self.settings.azure_speech_region
                )
                self.logger.info("Azure TTS provider initialized")
            except Exception as e:
                self.logger.error("Failed to initialize Azure TTS", error=str(e))
    
    def speak(self, text: str, use_cloud: bool = False, provider: str = "azure") -> SpeechResult:
        """Synthesize and play speech"""
        if use_cloud and provider in self.cloud_providers:
            return self.cloud_providers[provider].synthesize(text)
        elif self.local_tts:
            return self.local_tts.speak(text)
        else:
            raise RuntimeError("No TTS service available")
    
    def speak_async(self, text: str, use_cloud: bool = False, provider: str = "azure") -> SpeechResult:
        """Synthesize and play speech asynchronously"""
        if use_cloud and provider in self.cloud_providers:
            return self.cloud_providers[provider].synthesize(text)
        elif self.local_tts:
            return self.local_tts.speak_async(text)
        else:
            raise RuntimeError("No TTS service available")
    
    def cleanup(self) -> None:
        """Clean up TTS manager"""
        if self.local_tts:
            self.local_tts.cleanup()
        self.logger.info("TTS manager cleaned up")


# Global TTS manager instance
tts_manager = TTSManager()
