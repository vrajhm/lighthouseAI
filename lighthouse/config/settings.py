"""Configuration settings for Lighthouse.ai"""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Domain Security
    allowed_domains: List[str] = Field(
        default=["google.com", "amazon.com", "github.com", "wikipedia.org", "example.com"],
        description="List of allowed domains for navigation"
    )
    restricted_actions: List[str] = Field(
        default=["delete", "purchase", "payment", "account_change"],
        description="Actions that require confirmation"
    )
    
    # Browser Settings
    headless_mode: bool = Field(default=False, description="Run browser in headless mode")
    browser_timeout: int = Field(default=10, description="Browser timeout in seconds")
    browser_width: int = Field(default=1280, description="Browser window width")
    browser_height: int = Field(default=720, description="Browser window height")
    user_agent: str = Field(
        default="Lighthouse.ai/1.0",
        description="User agent string for browser"
    )
    
    # Audio Settings
    audio_device: str = Field(default="default", description="Audio device name")
    sample_rate: int = Field(default=16000, description="Audio sample rate")
    chunk_size: int = Field(default=1024, description="Audio chunk size")
    vad_aggressiveness: int = Field(default=2, description="VAD aggressiveness (0-3)")
    silence_threshold: float = Field(default=0.5, description="Silence threshold for VAD")
    
    # Speech Recognition (Whisper)
    whisper_model: str = Field(default="base", description="Whisper model size")
    whisper_language: str = Field(default="en", description="Whisper language")
    whisper_task: str = Field(default="transcribe", description="Whisper task type")
    
    # Text-to-Speech (Coqui TTS)
    tts_model: str = Field(
        default="tts_models/en/ljspeech/tacotron2-DDC",
        description="Coqui TTS model"
    )
    tts_speaker_id: int = Field(default=0, description="TTS speaker ID")
    tts_speed: float = Field(default=1.0, description="TTS speech rate")
    
    # Natural Language Understanding
    nlu_confidence_threshold: float = Field(
        default=0.7,
        description="Minimum confidence for NLU intent recognition"
    )
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries")
    
    # Privacy & Security
    local_processing: bool = Field(default=True, description="Use local processing only")
    log_level: str = Field(default="INFO", description="Logging level")
    redact_pii: bool = Field(default=True, description="Redact PII in logs")
    encrypt_logs: bool = Field(default=True, description="Encrypt log files")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=1, description="Number of API workers")
    cors_origins: str = Field(default="*", description="CORS allowed origins")
    
    # Session Management
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    max_sessions: int = Field(default=10, description="Maximum concurrent sessions")
    cleanup_interval: int = Field(default=300, description="Cleanup interval in seconds")
    
    # Development
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on changes")
    test_mode: bool = Field(default=False, description="Test mode")
    
    # Optional Cloud Services
    azure_speech_key: Optional[str] = Field(default=None, description="Azure Speech API key")
    azure_speech_region: Optional[str] = Field(default=None, description="Azure Speech region")
    google_cloud_credentials_path: Optional[str] = Field(
        default=None, description="Google Cloud credentials path"
    )
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret key")
    aws_region: Optional[str] = Field(default=None, description="AWS region")
    
    @field_validator('allowed_domains', mode='before')
    @classmethod
    def parse_allowed_domains(cls, v):
        """Parse comma-separated domains string"""
        if isinstance(v, str):
            return [domain.strip() for domain in v.split(',')]
        return v
    
    @field_validator('restricted_actions', mode='before')
    @classmethod
    def parse_restricted_actions(cls, v):
        """Parse comma-separated actions string"""
        if isinstance(v, str):
            return [action.strip() for action in v.split(',')]
        return v
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins"""
        if isinstance(v, str) and v != "*":
            return [origin.strip() for origin in v.split(',')]
        return v
    
    model_config = {
        "env_file": None,  # Temporarily disable .env file
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment"""
    global settings
    settings = Settings()
    return settings
