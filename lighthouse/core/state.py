"""Session state management for Lighthouse.ai"""

import time
import json
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from lighthouse.utils.logging import get_logger, LoggerMixin
from lighthouse.config.settings import get_settings


@dataclass
class Action:
    """Represents a user action"""
    timestamp: float
    action_type: str
    target: str
    result: str
    success: bool
    duration: float
    error: Optional[str] = None


@dataclass
class Session:
    """Represents a user session"""
    session_id: str
    start_time: float
    last_activity: float
    current_url: str
    actions: List[Action]
    page_history: List[str]
    is_active: bool = True
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []
        if self.page_history is None:
            self.page_history = []


class SessionManager(LoggerMixin):
    """Manages user sessions and action history"""
    
    def __init__(self):
        self.settings = get_settings()
        self.sessions: Dict[str, Session] = {}
        self.current_session: Optional[Session] = None
        self.lock = threading.Lock()
        
        # Session settings
        self.session_timeout = self.settings.session_timeout
        self.max_sessions = self.settings.max_sessions
        self.cleanup_interval = self.settings.cleanup_interval
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        
        self.logger.info("Session manager initialized")
    
    def create_session(self, session_id: Optional[str] = None) -> Session:
        """Create a new session"""
        with self.lock:
            if not session_id:
                session_id = f"session_{int(time.time())}"
            
            # Clean up old sessions if we're at the limit
            if len(self.sessions) >= self.max_sessions:
                self._cleanup_old_sessions()
            
            session = Session(
                session_id=session_id,
                start_time=time.time(),
                last_activity=time.time(),
                current_url="",
                actions=[],
                page_history=[]
            )
            
            self.sessions[session_id] = session
            self.current_session = session
            
            self.logger.info("Session created", session_id=session_id)
            return session
    
    def get_current_session(self) -> Optional[Session]:
        """Get the current active session"""
        return self.current_session
    
    def set_current_session(self, session_id: str) -> bool:
        """Set the current session"""
        with self.lock:
            if session_id in self.sessions:
                self.current_session = self.sessions[session_id]
                self.logger.info("Current session set", session_id=session_id)
                return True
            return False
    
    def add_action(self, action_type: str, target: str, result: str, success: bool, duration: float, error: Optional[str] = None) -> None:
        """Add an action to the current session"""
        if not self.current_session:
            self.logger.warning("No current session, creating new one")
            self.create_session()
        
        action = Action(
            timestamp=time.time(),
            action_type=action_type,
            target=target,
            result=result,
            success=success,
            duration=duration,
            error=error
        )
        
        with self.lock:
            self.current_session.actions.append(action)
            self.current_session.last_activity = time.time()
        
        self.logger.debug(
            "Action added",
            action_type=action_type,
            success=success,
            duration=duration
        )
    
    def update_current_url(self, url: str) -> None:
        """Update the current URL in the session"""
        if not self.current_session:
            return
        
        with self.lock:
            if self.current_session.current_url != url:
                self.current_session.current_url = url
                self.current_session.page_history.append(url)
                self.current_session.last_activity = time.time()
                
                self.logger.debug("URL updated", url=url)
    
    def get_action_history(self, limit: Optional[int] = None) -> List[Action]:
        """Get action history for current session"""
        if not self.current_session:
            return []
        
        actions = self.current_session.actions
        if limit:
            actions = actions[-limit:]
        
        return actions
    
    def get_page_history(self) -> List[str]:
        """Get page history for current session"""
        if not self.current_session:
            return []
        
        return self.current_session.page_history.copy()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for current session"""
        if not self.current_session:
            return {}
        
        session = self.current_session
        actions = session.actions
        
        total_actions = len(actions)
        successful_actions = sum(1 for action in actions if action.success)
        failed_actions = total_actions - successful_actions
        
        total_duration = sum(action.duration for action in actions)
        avg_duration = total_duration / total_actions if total_actions > 0 else 0
        
        session_duration = time.time() - session.start_time
        
        return {
            'session_id': session.session_id,
            'start_time': session.start_time,
            'duration': session_duration,
            'total_actions': total_actions,
            'successful_actions': successful_actions,
            'failed_actions': failed_actions,
            'success_rate': successful_actions / total_actions if total_actions > 0 else 0,
            'average_action_duration': avg_duration,
            'current_url': session.current_url,
            'pages_visited': len(session.page_history)
        }
    
    def end_session(self) -> Optional[Session]:
        """End the current session"""
        if not self.current_session:
            return None
        
        with self.lock:
            session = self.current_session
            session.is_active = False
            self.current_session = None
            
            self.logger.info("Session ended", session_id=session.session_id)
            return session
    
    def _cleanup_old_sessions(self) -> None:
        """Clean up old inactive sessions"""
        current_time = time.time()
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            # Remove sessions that are inactive and past timeout
            if not session.is_active or (current_time - session.last_activity) > self.session_timeout:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            self.logger.debug("Cleaned up old session", session_id=session_id)
    
    def _cleanup_worker(self) -> None:
        """Background worker for session cleanup"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                with self.lock:
                    self._cleanup_old_sessions()
            except Exception as e:
                self.logger.error("Session cleanup worker error", error=str(e))
    
    def export_session_data(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Export session data for analysis"""
        if session_id:
            session = self.sessions.get(session_id)
        else:
            session = self.current_session
        
        if not session:
            return {}
        
        return {
            'session': asdict(session),
            'stats': self.get_session_stats()
        }
    
    def import_session_data(self, data: Dict[str, Any]) -> bool:
        """Import session data (for testing/recovery)"""
        try:
            session_data = data.get('session', {})
            if not session_data:
                return False
            
            session = Session(**session_data)
            self.sessions[session.session_id] = session
            
            self.logger.info("Session data imported", session_id=session.session_id)
            return True
            
        except Exception as e:
            self.logger.error("Failed to import session data", error=str(e))
            return False
    
    def get_all_sessions(self) -> List[Session]:
        """Get all active sessions"""
        with self.lock:
            return [session for session in self.sessions.values() if session.is_active]
    
    def cleanup(self) -> None:
        """Clean up session manager"""
        # End current session
        if self.current_session:
            self.end_session()
        
        # Clear all sessions
        with self.lock:
            self.sessions.clear()
        
        self.logger.info("Session manager cleaned up")


# Global session manager instance
session_manager = SessionManager()
