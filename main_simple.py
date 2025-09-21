"""Simplified FastAPI service for Lighthouse.ai (without heavy dependencies)"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time

from lighthouse.utils.logging import get_logger, setup_logging
from lighthouse.core.nlu import nlu_manager, Intent
from lighthouse.core.safety import safety_manager
from lighthouse.config.settings import get_settings


# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Lighthouse.ai API",
    description="Voice-driven web navigator for blind and low-vision users",
    version="1.0.0"
)

# Add CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class VoiceCommandRequest(BaseModel):
    text: str
    session_id: Optional[str] = None


class VoiceCommandResponse(BaseModel):
    intent: str
    confidence: float
    success: bool
    message: str
    result: Optional[Dict[str, Any]] = None


# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Lighthouse.ai API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "nlu": "ok",
            "safety": "ok"
        }
    }


@app.post("/api/voice/command", response_model=VoiceCommandResponse)
async def process_voice_command(request: VoiceCommandRequest):
    """Process a voice command"""
    try:
        # Classify intent
        intent_result = nlu_manager.process_command(request.text)
        
        if intent_result.intent == Intent.UNKNOWN:
            return VoiceCommandResponse(
                intent="unknown",
                confidence=0.0,
                success=False,
                message="Unknown command"
            )
        
        # Execute command based on intent
        result = await _execute_command(intent_result)
        
        return VoiceCommandResponse(
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
            success=result["success"],
            message=result["message"],
            result=result.get("data")
        )
        
    except Exception as e:
        logger.error("Voice command processing failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/safety/domains")
async def get_allowed_domains():
    """Get allowed domains list"""
    try:
        return {
            "allowed_domains": safety_manager.get_allowlist(),
            "restricted_actions": safety_manager.get_restricted_actions()
        }
    except Exception as e:
        logger.error("Failed to get safety info", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commands/help")
async def get_help():
    """Get available commands"""
    try:
        commands = nlu_manager.get_command_help()
        return {
            "commands": commands,
            "supported_intents": [intent.value for intent in Intent if intent != Intent.UNKNOWN]
        }
    except Exception as e:
        logger.error("Failed to get help", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
async def _execute_command(intent_result):
    """Execute a classified command"""
    try:
        if intent_result.intent == Intent.DESCRIBE:
            return {
                "success": True,
                "message": "Page description requested",
                "data": {
                    "intent": intent_result.intent.value,
                    "text": intent_result.processed_text
                }
            }
        
        elif intent_result.intent == Intent.HELP:
            commands = nlu_manager.get_command_help()
            return {
                "success": True,
                "message": "Help information provided",
                "data": {
                    "commands": commands,
                    "intent": intent_result.intent.value
                }
            }
        
        elif intent_result.intent == Intent.STOP:
            return {
                "success": True,
                "message": "Stop command received",
                "data": {
                    "intent": intent_result.intent.value
                }
            }
        
        else:
            return {
                "success": True,
                "message": f"Command '{intent_result.intent.value}' received",
                "data": {"intent": intent_result.intent.value}
            }
            
    except Exception as e:
        logger.error("Command execution failed", error=str(e))
        return {"success": False, "message": str(e)}


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    logger.info("Starting Lighthouse.ai API")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Lighthouse.ai API")


def main():
    """Run the FastAPI server"""
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
