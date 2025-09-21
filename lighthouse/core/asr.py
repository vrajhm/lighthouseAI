"""Speech-to-Text module using faster-whisper for Lighthouse.ai"""

import os
import time
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from faster_whisper import WhisperModel
from dataclasses import dataclass

from lighthouse.utils.logging import get_logger, LoggerMixin
from lighthouse.utils.audio import AudioCapture, AudioConfig, AudioProcessor
from lighthouse.config.settings import get_settings


@dataclass
class TranscriptionResult:
    """Result of speech transcription"""
    text: str
    confidence: float
    language: str
    duration: float
    segments: List[Dict[str, Any]]


class ASRService(LoggerMixin):
    """Speech-to-Text service using faster-whisper"""
    
    def __init__(self, model_size: str = "base", device: str = "auto"):
        self.settings = get_settings()
        self.model_size = model_size or self.settings.whisper_model
        self.device = device
        
        # Initialize audio capture
        self.audio_config = AudioConfig(
            sample_rate=self.settings.sample_rate,
            chunk_size=self.settings.chunk_size,
            vad_aggressiveness=self.settings.vad_aggressiveness,
            silence_threshold=self.settings.silence_threshold
        )
        self.audio_capture = AudioCapture(self.audio_config)
        self.audio_processor = AudioProcessor()
        
        # Initialize Whisper model
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the Whisper model"""
        try:
            self.logger.info("Loading Whisper model", model_size=self.model_size)
            
            # Determine device
            if self.device == "auto":
                device = "cuda" if self._has_cuda() else "cpu"
            else:
                device = self.device
            
            # Load model
            self.model = WhisperModel(
                self.model_size,
                device=device,
                compute_type="float16" if device == "cuda" else "int8"
            )
            
            self.logger.info("Whisper model loaded successfully", device=device)
            
        except Exception as e:
            self.logger.error("Failed to load Whisper model", error=str(e))
            raise
    
    def _has_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def transcribe_audio(self, audio_data: bytes, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio data to text"""
        if not self.model:
            raise RuntimeError("Whisper model not loaded")
        
        start_time = time.time()
        
        try:
            # Convert audio bytes to numpy array
            audio_array = self.audio_processor.bytes_to_numpy(
                audio_data, 
                self.audio_config.sample_rate
            )
            
            # Normalize audio
            audio_array = self.audio_processor.normalize_audio(audio_array)
            
            # Transcribe with Whisper
            segments, info = self.model.transcribe(
                audio_array,
                language=language or self.settings.whisper_language,
                task=self.settings.whisper_task,
                beam_size=5,
                best_of=5,
                temperature=0.0,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200
                )
            )
            
            # Process segments
            text_segments = []
            full_text = ""
            total_confidence = 0.0
            
            for segment in segments:
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": getattr(segment, 'avg_logprob', 0.0)
                }
                text_segments.append(segment_data)
                full_text += segment.text.strip() + " "
                total_confidence += segment_data["confidence"]
            
            # Calculate average confidence
            avg_confidence = total_confidence / len(text_segments) if text_segments else 0.0
            
            # Convert confidence from log probability to percentage
            confidence_percent = min(100.0, max(0.0, (avg_confidence + 1.0) * 50.0))
            
            duration = time.time() - start_time
            
            result = TranscriptionResult(
                text=full_text.strip(),
                confidence=confidence_percent,
                language=info.language,
                duration=duration,
                segments=text_segments
            )
            
            self.logger.info(
                "Transcription completed",
                text_length=len(result.text),
                confidence=result.confidence,
                language=result.language,
                duration=duration
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Transcription failed", error=str(e))
            raise
    
    def transcribe_file(self, file_path: str, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio from file"""
        try:
            # Load audio file
            audio_bytes, sample_rate = self.audio_processor.load_wav(file_path)
            
            # Transcribe
            return self.transcribe_audio(audio_bytes, language)
            
        except Exception as e:
            self.logger.error("File transcription failed", file_path=file_path, error=str(e))
            raise
    
    def listen_and_transcribe(self, max_duration: float = 10.0, language: Optional[str] = None) -> TranscriptionResult:
        """Listen for speech and transcribe in real-time"""
        try:
            self.logger.info("Starting real-time transcription", max_duration=max_duration)
            
            # Record audio until silence
            audio_data = self.audio_capture.record_until_silence(max_duration)
            
            if not audio_data:
                return TranscriptionResult(
                    text="",
                    confidence=0.0,
                    language=language or self.settings.whisper_language,
                    duration=0.0,
                    segments=[]
                )
            
            # Transcribe the recorded audio
            return self.transcribe_audio(audio_data, language)
            
        except Exception as e:
            self.logger.error("Real-time transcription failed", error=str(e))
            raise
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "th", "vi", "tr", "pl", "nl", "sv", "da", "no"
        ]
    
    def is_language_supported(self, language: str) -> bool:
        """Check if language is supported"""
        return language in self.get_supported_languages()
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self.audio_capture.cleanup()
            self.logger.info("ASR service cleaned up")
        except Exception as e:
            self.logger.error("ASR cleanup failed", error=str(e))


class ASRManager:
    """Manager for ASR operations with session handling"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.asr_service = None
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """Initialize ASR service"""
        try:
            self.asr_service = ASRService()
            self.logger.info("ASR manager initialized")
        except Exception as e:
            self.logger.error("Failed to initialize ASR service", error=str(e))
            raise
    
    def transcribe(self, audio_data: bytes, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio data"""
        if not self.asr_service:
            raise RuntimeError("ASR service not initialized")
        
        return self.asr_service.transcribe_audio(audio_data, language)
    
    def listen(self, max_duration: float = 10.0, language: Optional[str] = None) -> TranscriptionResult:
        """Listen and transcribe"""
        if not self.asr_service:
            raise RuntimeError("ASR service not initialized")
        
        return self.asr_service.listen_and_transcribe(max_duration, language)
    
    def cleanup(self) -> None:
        """Clean up ASR manager"""
        if self.asr_service:
            self.asr_service.cleanup()
        self.logger.info("ASR manager cleaned up")


# Global ASR manager instance
asr_manager = ASRManager()
