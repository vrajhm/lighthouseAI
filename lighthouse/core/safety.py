"""Safety and privacy controls for Lighthouse.ai"""

import re
import yaml
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from urllib.parse import urlparse
from enum import Enum

from lighthouse.utils.logging import get_logger, LoggerMixin
from lighthouse.config.settings import get_settings


class ActionType(Enum):
    """Types of actions that can be performed"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SUBMIT = "submit"
    DELETE = "delete"
    PURCHASE = "purchase"
    PAYMENT = "payment"
    ACCOUNT_CHANGE = "account_change"
    LOGOUT = "logout"
    UNSUBSCRIBE = "unsubscribe"
    DESCRIBE = "describe"
    LIST = "list"
    STOP = "stop"
    HELP = "help"


class SafetyLevel(Enum):
    """Safety levels for actions"""
    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


@dataclass
class SafetyRule:
    """Safety rule configuration"""
    action_type: ActionType
    safety_level: SafetyLevel
    requires_confirmation: bool
    description: str
    patterns: List[str] = None
    
    def __post_init__(self):
        if self.patterns is None:
            self.patterns = []


@dataclass
class DomainRule:
    """Domain-specific safety rules"""
    domain: str
    allowed_subdomains: List[str] = None
    restricted_paths: List[str] = None
    blocked_actions: List[ActionType] = None
    custom_rules: List[SafetyRule] = None
    
    def __post_init__(self):
        if self.allowed_subdomains is None:
            self.allowed_subdomains = []
        if self.restricted_paths is None:
            self.restricted_paths = []
        if self.blocked_actions is None:
            self.blocked_actions = []
        if self.custom_rules is None:
            self.custom_rules = []


class SafetyManager(LoggerMixin):
    """Manages safety and privacy controls"""
    
    def __init__(self):
        self.settings = get_settings()
        self.allowed_domains: Set[str] = set()
        self.restricted_actions: Set[ActionType] = set()
        self.domain_rules: Dict[str, DomainRule] = {}
        self.safety_rules: List[SafetyRule] = []
        
        self._load_configuration()
        self._setup_default_rules()
    
    def _load_configuration(self) -> None:
        """Load safety configuration from settings and YAML"""
        try:
            # Load from settings
            self.allowed_domains = set(self.settings.allowed_domains)
            self.restricted_actions = set(
                ActionType(action) for action in self.settings.restricted_actions
            )
            
            # Load domain rules from YAML
            self._load_domain_rules()
            
            self.logger.info(
                "Safety configuration loaded",
                allowed_domains=len(self.allowed_domains),
                restricted_actions=len(self.restricted_actions),
                domain_rules=len(self.domain_rules)
            )
            
        except Exception as e:
            self.logger.error("Failed to load safety configuration", error=str(e))
            raise
    
    def _load_domain_rules(self) -> None:
        """Load domain-specific rules from YAML file"""
        try:
            import os
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                "config", 
                "domains.yaml"
            )
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Load domain configurations
                if 'domain_configs' in config:
                    for domain, rules in config['domain_configs'].items():
                        domain_rule = DomainRule(
                            domain=domain,
                            allowed_subdomains=rules.get('allowed_subdomains', []),
                            restricted_paths=rules.get('restricted_paths', []),
                            blocked_actions=[
                                ActionType(action) for action in rules.get('blocked_actions', [])
                            ]
                        )
                        self.domain_rules[domain] = domain_rule
                
                self.logger.info("Domain rules loaded from YAML")
            
        except Exception as e:
            self.logger.error("Failed to load domain rules", error=str(e))
    
    def _setup_default_rules(self) -> None:
        """Setup default safety rules"""
        self.safety_rules = [
            SafetyRule(
                action_type=ActionType.DELETE,
                safety_level=SafetyLevel.DANGEROUS,
                requires_confirmation=True,
                description="Delete action requires confirmation",
                patterns=["delete", "remove", "destroy", "erase"]
            ),
            SafetyRule(
                action_type=ActionType.PURCHASE,
                safety_level=SafetyLevel.DANGEROUS,
                requires_confirmation=True,
                description="Purchase action requires confirmation",
                patterns=["buy", "purchase", "order", "checkout", "pay"]
            ),
            SafetyRule(
                action_type=ActionType.PAYMENT,
                safety_level=SafetyLevel.DANGEROUS,
                requires_confirmation=True,
                description="Payment action requires confirmation",
                patterns=["payment", "billing", "credit card", "paypal"]
            ),
            SafetyRule(
                action_type=ActionType.ACCOUNT_CHANGE,
                safety_level=SafetyLevel.WARNING,
                requires_confirmation=True,
                description="Account changes require confirmation",
                patterns=["password", "email", "profile", "settings"]
            ),
            SafetyRule(
                action_type=ActionType.LOGOUT,
                safety_level=SafetyLevel.WARNING,
                requires_confirmation=True,
                description="Logout requires confirmation",
                patterns=["logout", "sign out", "exit"]
            ),
            SafetyRule(
                action_type=ActionType.UNSUBSCRIBE,
                safety_level=SafetyLevel.WARNING,
                requires_confirmation=True,
                description="Unsubscribe requires confirmation",
                patterns=["unsubscribe", "opt out", "remove subscription"]
            )
        ]
    
    def is_domain_allowed(self, url: str) -> bool:
        """Check if domain is in the allowlist"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Remove www. prefix for comparison
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check if domain is allowed
            is_allowed = domain in self.allowed_domains
            
            self.logger.debug(
                "Domain check",
                url=url,
                domain=domain,
                allowed=is_allowed
            )
            
            return is_allowed
            
        except Exception as e:
            self.logger.error("Domain check failed", url=url, error=str(e))
            return False
    
    def get_domain_rule(self, url: str) -> Optional[DomainRule]:
        """Get domain-specific rules for a URL"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return self.domain_rules.get(domain)
            
        except Exception as e:
            self.logger.error("Failed to get domain rule", url=url, error=str(e))
            return None
    
    def is_action_restricted(self, action_type: ActionType, url: str = None) -> bool:
        """Check if action is restricted"""
        # Check global restrictions
        if action_type in self.restricted_actions:
            return True
        
        # Check domain-specific restrictions
        if url:
            domain_rule = self.get_domain_rule(url)
            if domain_rule and action_type in domain_rule.blocked_actions:
                return True
        
        return False
    
    def requires_confirmation(self, action_type: ActionType, url: str = None, text: str = None) -> bool:
        """Check if action requires confirmation"""
        # Check if action is globally restricted
        if action_type in self.restricted_actions:
            return True
        
        # Check domain-specific rules
        if url:
            domain_rule = self.get_domain_rule(url)
            if domain_rule and action_type in domain_rule.blocked_actions:
                return True
        
        # Check safety rules
        for rule in self.safety_rules:
            if rule.action_type == action_type and rule.requires_confirmation:
                # Check text patterns if provided
                if text and rule.patterns:
                    text_lower = text.lower()
                    if any(pattern.lower() in text_lower for pattern in rule.patterns):
                        return True
                elif not text:
                    return True
        
        return False
    
    def get_safety_level(self, action_type: ActionType, url: str = None, text: str = None) -> SafetyLevel:
        """Get safety level for an action"""
        # Check if action is blocked
        if self.is_action_restricted(action_type, url):
            return SafetyLevel.BLOCKED
        
        # Check safety rules
        for rule in self.safety_rules:
            if rule.action_type == action_type:
                # Check text patterns if provided
                if text and rule.patterns:
                    text_lower = text.lower()
                    if any(pattern.lower() in text_lower for pattern in rule.patterns):
                        return rule.safety_level
                elif not text:
                    return rule.safety_level
        
        # Default to safe
        return SafetyLevel.SAFE
    
    def get_confirmation_message(self, action_type: ActionType, url: str = None, text: str = None) -> str:
        """Get confirmation message for an action"""
        safety_level = self.get_safety_level(action_type, url, text)
        
        if safety_level == SafetyLevel.BLOCKED:
            return f"Action '{action_type.value}' is blocked for security reasons."
        
        if safety_level == SafetyLevel.DANGEROUS:
            return f"⚠️ DANGEROUS ACTION: {action_type.value.upper()}. This action cannot be undone. Are you sure you want to continue?"
        
        if safety_level == SafetyLevel.WARNING:
            return f"⚠️ WARNING: {action_type.value.upper()} action detected. Do you want to continue?"
        
        return f"Confirm {action_type.value} action?"
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        """Validate URL against safety rules"""
        result = {
            'valid': True,
            'allowed': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check if domain is allowed
            if not self.is_domain_allowed(url):
                result['allowed'] = False
                result['errors'].append(f"Domain not in allowlist: {urlparse(url).netloc}")
                result['valid'] = False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'javascript:',
                r'data:',
                r'file:',
                r'ftp:',
                r'mailto:'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    result['warnings'].append(f"Suspicious URL pattern detected: {pattern}")
            
            # Check domain-specific rules
            domain_rule = self.get_domain_rule(url)
            if domain_rule:
                parsed_url = urlparse(url)
                path = parsed_url.path
                
                for restricted_path in domain_rule.restricted_paths:
                    if path.startswith(restricted_path):
                        result['warnings'].append(f"Restricted path: {restricted_path}")
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"URL validation failed: {str(e)}")
        
        return result
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text input to prevent injection attacks"""
        if not text:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r', '\n']
        sanitized = text
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
        
        return sanitized.strip()
    
    def log_action(self, action_type: ActionType, url: str = None, text: str = None, user_confirmed: bool = False) -> None:
        """Log action for audit trail"""
        self.logger.info(
            "Action logged",
            action_type=action_type.value,
            url=url,
            text_length=len(text) if text else 0,
            user_confirmed=user_confirmed,
            safety_level=self.get_safety_level(action_type, url, text).value
        )
    
    def add_domain_to_allowlist(self, domain: str) -> bool:
        """Add domain to allowlist"""
        try:
            # Normalize domain
            parsed = urlparse(f"https://{domain}")
            normalized_domain = parsed.netloc.lower()
            
            if normalized_domain.startswith('www.'):
                normalized_domain = normalized_domain[4:]
            
            self.allowed_domains.add(normalized_domain)
            
            self.logger.info("Domain added to allowlist", domain=normalized_domain)
            return True
            
        except Exception as e:
            self.logger.error("Failed to add domain to allowlist", domain=domain, error=str(e))
            return False
    
    def remove_domain_from_allowlist(self, domain: str) -> bool:
        """Remove domain from allowlist"""
        try:
            # Normalize domain
            parsed = urlparse(f"https://{domain}")
            normalized_domain = parsed.netloc.lower()
            
            if normalized_domain.startswith('www.'):
                normalized_domain = normalized_domain[4:]
            
            self.allowed_domains.discard(normalized_domain)
            
            self.logger.info("Domain removed from allowlist", domain=normalized_domain)
            return True
            
        except Exception as e:
            self.logger.error("Failed to remove domain from allowlist", domain=domain, error=str(e))
            return False
    
    def get_allowlist(self) -> List[str]:
        """Get current allowlist"""
        return sorted(list(self.allowed_domains))
    
    def get_restricted_actions(self) -> List[str]:
        """Get list of restricted actions"""
        return [action.value for action in self.restricted_actions]


# Global safety manager instance
safety_manager = SafetyManager()
