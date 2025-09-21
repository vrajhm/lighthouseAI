"""Basic tests for Lighthouse.ai components"""

import pytest
import time
from unittest.mock import Mock, patch

from lighthouse.config.settings import get_settings
from lighthouse.core.nlu import NLUEngine, Intent
from lighthouse.core.safety import SafetyManager, ActionType
from lighthouse.utils.logging import get_logger


class TestNLUEngine:
    """Test NLU engine functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.nlu = NLUEngine()
    
    def test_navigate_intent(self):
        """Test navigation intent recognition"""
        test_cases = [
            ("go to google.com", Intent.NAVIGATE),
            ("navigate to amazon.com", Intent.NAVIGATE),
            ("visit github.com", Intent.NAVIGATE),
            ("open wikipedia.org", Intent.NAVIGATE),
        ]
        
        for text, expected_intent in test_cases:
            result = self.nlu.classify_intent(text)
            assert result.intent == expected_intent, f"Failed for: {text}"
            assert result.confidence > 0.5, f"Low confidence for: {text}"
    
    def test_click_intent(self):
        """Test click intent recognition"""
        test_cases = [
            ("click search button", Intent.CLICK),
            ("press submit", Intent.CLICK),
            ("tap the link", Intent.CLICK),
            ("select option 1", Intent.CLICK),
        ]
        
        for text, expected_intent in test_cases:
            result = self.nlu.classify_intent(text)
            assert result.intent == expected_intent, f"Failed for: {text}"
    
    def test_type_intent(self):
        """Test type intent recognition"""
        test_cases = [
            ("type hello world", Intent.TYPE),
            ("enter my email", Intent.TYPE),
            ("input password", Intent.TYPE),
            ("fill the form", Intent.TYPE),
        ]
        
        for text, expected_intent in test_cases:
            result = self.nlu.classify_intent(text)
            assert result.intent == expected_intent, f"Failed for: {text}"
    
    def test_describe_intent(self):
        """Test describe intent recognition"""
        test_cases = [
            ("describe this page", Intent.DESCRIBE),
            ("what's on screen", Intent.DESCRIBE),
            ("tell me about this page", Intent.DESCRIBE),
            ("read the page", Intent.DESCRIBE),
        ]
        
        for text, expected_intent in test_cases:
            result = self.nlu.classify_intent(text)
            assert result.intent == expected_intent, f"Failed for: {text}"
    
    def test_unknown_intent(self):
        """Test unknown intent handling"""
        test_cases = [
            "random text",
            "asdfghjkl",
            "123456789",
        ]
        
        for text in test_cases:
            result = self.nlu.classify_intent(text)
            assert result.intent == Intent.UNKNOWN, f"Should be unknown: {text}"
    
    def test_entity_extraction(self):
        """Test entity extraction"""
        result = self.nlu.classify_intent("go to google.com")
        url_entities = self.nlu.get_entity_values(result.entities, 'url')
        assert len(url_entities) > 0
        assert 'google.com' in url_entities[0]
    
    def test_parse_navigation_command(self):
        """Test navigation command parsing"""
        result = self.nlu.classify_intent("go to google.com")
        parsed = self.nlu.parse_navigation_command(result)
        assert 'url' in parsed
        assert 'google.com' in parsed['url']
    
    def test_parse_click_command(self):
        """Test click command parsing"""
        result = self.nlu.classify_intent("click the search button")
        parsed = self.nlu.parse_click_command(result)
        assert 'text' in parsed
        assert 'search button' in parsed['text']


class TestSafetyManager:
    """Test safety manager functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.safety = SafetyManager()
    
    def test_domain_allowlist(self):
        """Test domain allowlist functionality"""
        # Test allowed domain
        assert self.safety.is_domain_allowed("https://google.com")
        assert self.safety.is_domain_allowed("google.com")
        assert self.safety.is_domain_allowed("www.google.com")
        
        # Test disallowed domain
        assert not self.safety.is_domain_allowed("https://malicious-site.com")
    
    def test_action_restrictions(self):
        """Test action restrictions"""
        # Test restricted actions
        assert self.safety.is_action_restricted(ActionType.DELETE)
        assert self.safety.is_action_restricted(ActionType.PURCHASE)
        assert self.safety.is_action_restricted(ActionType.PAYMENT)
        
        # Test non-restricted actions
        assert not self.safety.is_action_restricted(ActionType.NAVIGATE)
        assert not self.safety.is_action_restricted(ActionType.CLICK)
    
    def test_confirmation_requirements(self):
        """Test confirmation requirements"""
        # Test actions that require confirmation
        assert self.safety.requires_confirmation(ActionType.DELETE)
        assert self.safety.requires_confirmation(ActionType.PURCHASE)
        assert self.safety.requires_confirmation(ActionType.PAYMENT)
        
        # Test actions that don't require confirmation
        assert not self.safety.requires_confirmation(ActionType.NAVIGATE)
        assert not self.safety.requires_confirmation(ActionType.DESCRIBE)
    
    def test_safety_levels(self):
        """Test safety level classification"""
        # Test dangerous actions
        assert self.safety.get_safety_level(ActionType.DELETE) == self.safety.SafetyLevel.DANGEROUS
        assert self.safety.get_safety_level(ActionType.PURCHASE) == self.safety.SafetyLevel.DANGEROUS
        
        # Test safe actions
        assert self.safety.get_safety_level(ActionType.NAVIGATE) == self.safety.SafetyLevel.SAFE
        assert self.safety.get_safety_level(ActionType.DESCRIBE) == self.safety.SafetyLevel.SAFE
    
    def test_url_validation(self):
        """Test URL validation"""
        # Test valid URLs
        result = self.safety.validate_url("https://google.com")
        assert result['valid']
        assert result['allowed']
        
        # Test invalid domain
        result = self.safety.validate_url("https://malicious-site.com")
        assert not result['allowed']
        assert not result['valid']
        
        # Test suspicious patterns
        result = self.safety.validate_url("javascript:alert('xss')")
        assert not result['valid']
        assert len(result['warnings']) > 0
    
    def test_text_sanitization(self):
        """Test text sanitization"""
        # Test normal text
        sanitized = self.safety.sanitize_text("hello world")
        assert sanitized == "hello world"
        
        # Test dangerous characters
        sanitized = self.safety.sanitize_text("hello<script>alert('xss')</script>world")
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
        
        # Test length limit
        long_text = "a" * 2000
        sanitized = self.safety.sanitize_text(long_text)
        assert len(sanitized) <= 1000
    
    def test_domain_management(self):
        """Test domain allowlist management"""
        # Add domain
        success = self.safety.add_domain_to_allowlist("test.com")
        assert success
        assert self.safety.is_domain_allowed("test.com")
        
        # Remove domain
        success = self.safety.remove_domain_from_allowlist("test.com")
        assert success
        assert not self.safety.is_domain_allowed("test.com")


class TestSettings:
    """Test configuration settings"""
    
    def test_settings_loading(self):
        """Test settings loading"""
        settings = get_settings()
        
        # Test basic settings
        assert settings.allowed_domains is not None
        assert len(settings.allowed_domains) > 0
        assert "google.com" in settings.allowed_domains
        
        # Test browser settings
        assert settings.browser_timeout > 0
        assert settings.browser_width > 0
        assert settings.browser_height > 0
        
        # Test audio settings
        assert settings.sample_rate > 0
        assert settings.chunk_size > 0
    
    def test_environment_override(self):
        """Test environment variable override"""
        import os
        
        # Set environment variable
        os.environ["BROWSER_TIMEOUT"] = "15"
        
        # Reload settings
        from lighthouse.config.settings import reload_settings
        settings = reload_settings()
        
        assert settings.browser_timeout == 15
        
        # Clean up
        del os.environ["BROWSER_TIMEOUT"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
