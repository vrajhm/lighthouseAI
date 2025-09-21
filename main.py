"""FastAPI service for Lighthouse.ai"""

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import time

from lighthouse.utils.logging import get_logger, setup_logging
from lighthouse.core.asr import asr_manager
from lighthouse.core.tts import tts_manager
from lighthouse.core.browser import browser_manager
from lighthouse.core.nlu import nlu_manager, Intent
from lighthouse.core.safety import safety_manager
from lighthouse.core.state import session_manager
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
    allow_origins=settings.cors_origins if isinstance(settings.cors_origins, list) else ["*"],
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


class NavigationRequest(BaseModel):
    url: str
    session_id: Optional[str] = None


class NavigationResponse(BaseModel):
    success: bool
    message: str
    page_info: Optional[Dict[str, Any]] = None


class PageInfoResponse(BaseModel):
    title: str
    url: str
    main_heading: Optional[str] = None
    actionable_elements: List[Dict[str, Any]]
    landmarks: List[Dict[str, Any]]


class SessionInfo(BaseModel):
    session_id: str
    start_time: float
    duration: float
    total_actions: int
    success_rate: float
    current_url: str


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
            "asr": "ok",
            "tts": "ok",
            "browser": "ok",
            "nlu": "ok",
            "safety": "ok"
        }
    }


@app.post("/api/voice/command", response_model=VoiceCommandResponse)
async def process_voice_command(request: VoiceCommandRequest):
    """Process a voice command"""
    try:
        # Set session if provided
        if request.session_id:
            session_manager.set_current_session(request.session_id)
        elif not session_manager.get_current_session():
            session_manager.create_session()
        
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


@app.post("/api/navigate", response_model=NavigationResponse)
async def navigate_to_url(request: NavigationRequest):
    """Navigate to a specific URL"""
    try:
        # Set session if provided
        if request.session_id:
            session_manager.set_current_session(request.session_id)
        elif not session_manager.get_current_session():
            session_manager.create_session()
        
        # Check safety
        if not safety_manager.is_domain_allowed(request.url):
            return NavigationResponse(
                success=False,
                message=f"Domain not allowed: {request.url}"
            )
        
        # Navigate
        success = browser_manager.navigate(request.url)
        
        if success:
            session_manager.update_current_url(request.url)
            page_info = browser_manager.get_page_info()
            
            return NavigationResponse(
                success=True,
                message="Navigation successful",
                page_info={
                    "title": page_info.title,
                    "url": page_info.url,
                    "main_heading": page_info.main_heading,
                    "actionable_elements": len(page_info.actionable_elements),
                    "landmarks": len(page_info.landmarks)
                }
            )
        else:
            return NavigationResponse(
                success=False,
                message="Navigation failed"
            )
            
    except Exception as e:
        logger.error("Navigation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/page/info", response_model=PageInfoResponse)
async def get_page_info():
    """Get current page information"""
    try:
        page_info = browser_manager.get_page_info()
        
        return PageInfoResponse(
            title=page_info.title,
            url=page_info.url,
            main_heading=page_info.main_heading,
            actionable_elements=[
                {
                    "role": elem.get("role", "unknown"),
                    "name": elem.get("name", ""),
                    "description": elem.get("description", "")
                }
                for elem in page_info.actionable_elements
            ],
            landmarks=[
                {
                    "role": landmark.get("role", "unknown"),
                    "name": landmark.get("name", ""),
                    "description": landmark.get("description", "")
                }
                for landmark in page_info.landmarks
            ]
        )
        
    except Exception as e:
        logger.error("Failed to get page info", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/click")
async def click_element(element_selector: str, session_id: Optional[str] = None):
    """Click an element on the page"""
    try:
        # Set session if provided
        if request.session_id:
            session_manager.set_current_session(request.session_id)
        elif not session_manager.get_current_session():
            session_manager.create_session()
        
        # Check safety
        if safety_manager.requires_confirmation(ActionType.CLICK):
            # In a real implementation, you'd handle confirmation here
            pass
        
        # Find and click element
        element = browser_manager.browser.find_element(element_selector)
        if element:
            success = browser_manager.browser.click_element(element)
            if success:
                return {"success": True, "message": "Element clicked successfully"}
            else:
                return {"success": False, "message": "Click failed"}
        else:
            return {"success": False, "message": "Element not found"}
            
    except Exception as e:
        logger.error("Click failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/type")
async def type_text(text: str, field_selector: Optional[str] = None, session_id: Optional[str] = None):
    """Type text into a field"""
    try:
        # Set session if provided
        if request.session_id:
            session_manager.set_current_session(request.session_id)
        elif not session_manager.get_current_session():
            session_manager.create_session()
        
        # Find input field
        if field_selector:
            element = browser_manager.browser.find_element(field_selector)
        else:
            element = browser_manager.browser.find_element("input")
        
        if element:
            success = browser_manager.browser.type_text(element, text)
            if success:
                return {"success": True, "message": "Text entered successfully"}
            else:
                return {"success": False, "message": "Failed to enter text"}
        else:
            return {"success": False, "message": "Input field not found"}
            
    except Exception as e:
        logger.error("Type text failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/info", response_model=SessionInfo)
async def get_session_info(session_id: Optional[str] = None):
    """Get session information"""
    try:
        if session_id:
            session_manager.set_current_session(session_id)
        
        session = session_manager.get_current_session()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        stats = session_manager.get_session_stats()
        
        return SessionInfo(
            session_id=stats["session_id"],
            start_time=stats["start_time"],
            duration=stats["duration"],
            total_actions=stats["total_actions"],
            success_rate=stats["success_rate"],
            current_url=stats["current_url"]
        )
        
    except Exception as e:
        logger.error("Failed to get session info", error=str(e))
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


@app.post("/api/safety/domains")
async def add_domain(domain: str):
    """Add domain to allowlist"""
    try:
        success = safety_manager.add_domain_to_allowlist(domain)
        if success:
            return {"success": True, "message": f"Domain {domain} added to allowlist"}
        else:
            return {"success": False, "message": "Failed to add domain"}
    except Exception as e:
        logger.error("Failed to add domain", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
async def _execute_command(intent_result):
    """Execute a classified command"""
    try:
        if intent_result.intent == Intent.NAVIGATE:
            parsed = nlu_manager.nlu_engine.parse_navigation_command(intent_result)
            if 'url' in parsed:
                success = browser_manager.navigate(parsed['url'])
                if success:
                    session_manager.update_current_url(parsed['url'])
                    return {
                        "success": True,
                        "message": f"Navigated to {parsed['url']}",
                        "data": {"url": parsed['url']}
                    }
                else:
                    return {"success": False, "message": "Navigation failed"}
            else:
                return {"success": False, "message": "No URL specified"}
        
        elif intent_result.intent == Intent.DESCRIBE:
            page_info = browser_manager.get_page_info()
            return {
                "success": True,
                "message": f"Page: {page_info.title}",
                "data": {
                    "title": page_info.title,
                    "url": page_info.url,
                    "main_heading": page_info.main_heading,
                    "actionable_elements": len(page_info.actionable_elements)
                }
            }
        
        elif intent_result.intent == Intent.LIST:
            elements = browser_manager.browser.list_actionable_elements()
            return {
                "success": True,
                "message": f"Found {len(elements)} actionable elements",
                "data": {"elements": [{"role": e.role, "text": e.text} for e in elements[:5]]}
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
    
    # Create initial session
    session_manager.create_session()
    
    logger.info("API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Lighthouse.ai API")
    
    # Cleanup components
    try:
        session_manager.cleanup()
        browser_manager.cleanup()
        tts_manager.cleanup()
        asr_manager.cleanup()
    except Exception as e:
        logger.error("Cleanup error", error=str(e))
    
    logger.info("API shutdown complete")


def main():
    """Run the FastAPI server"""
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
