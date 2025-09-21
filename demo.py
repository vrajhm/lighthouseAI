#!/usr/bin/env python3
"""Demo script for Lighthouse.ai functionality"""

import sys
import os
sys.path.insert(0, '.')

from lighthouse.core.nlu import nlu_manager, Intent
from lighthouse.core.safety import safety_manager, ActionType
from lighthouse.utils.logging import get_logger, setup_logging


def demo_nlu():
    """Demonstrate NLU functionality"""
    print("\n🎯 NLU (Natural Language Understanding) Demo")
    print("=" * 50)
    
    test_commands = [
        "go to google.com",
        "click the search button", 
        "type hello world",
        "describe this page",
        "list all buttons",
        "stop",
        "help me",
        "random text that should be unknown"
    ]
    
    for command in test_commands:
        result = nlu_manager.process_command(command)
        status = "✅" if result.intent != Intent.UNKNOWN else "❌"
        print(f"{status} '{command}' → {result.intent.value} (confidence: {result.confidence:.2f})")
        
        # Show entities if any
        if result.entities:
            entities = [f"{e.type}: {e.value}" for e in result.entities]
            print(f"   Entities: {', '.join(entities)}")


def demo_safety():
    """Demonstrate safety functionality"""
    print("\n🛡️ Safety & Privacy Demo")
    print("=" * 50)
    
    # Test domain allowlist
    test_urls = [
        "https://google.com",
        "https://amazon.com", 
        "https://malicious-site.com",
        "https://github.com",
        "https://evil-hacker.net"
    ]
    
    print("Domain Allowlist Test:")
    for url in test_urls:
        allowed = safety_manager.is_domain_allowed(url)
        status = "✅" if allowed else "❌"
        print(f"{status} {url} → {'Allowed' if allowed else 'Blocked'}")
    
    # Test action restrictions
    print("\nAction Restrictions Test:")
    test_actions = [
        ActionType.NAVIGATE,
        ActionType.CLICK,
        ActionType.DELETE,
        ActionType.PURCHASE,
        ActionType.PAYMENT,
        ActionType.DESCRIBE
    ]
    
    for action in test_actions:
        restricted = safety_manager.is_action_restricted(action)
        requires_confirmation = safety_manager.requires_confirmation(action)
        safety_level = safety_manager.get_safety_level(action)
        
        status = "🔒" if restricted else "✅"
        confirm = "⚠️" if requires_confirmation else "✅"
        
        print(f"{status} {action.value} → Restricted: {restricted}, Confirmation: {requires_confirmation}, Level: {safety_level.value}")


def demo_commands():
    """Demonstrate available commands"""
    print("\n📋 Available Voice Commands")
    print("=" * 50)
    
    commands = nlu_manager.get_command_help()
    for i, command in enumerate(commands, 1):
        print(f"{i}. {command}")


def demo_navigation_parsing():
    """Demonstrate navigation command parsing"""
    print("\n🧭 Navigation Command Parsing Demo")
    print("=" * 50)
    
    navigation_commands = [
        "go to google.com",
        "navigate to amazon.com",
        "visit github.com",
        "open wikipedia.org"
    ]
    
    for command in navigation_commands:
        result = nlu_manager.process_command(command)
        if result.intent == Intent.NAVIGATE:
            parsed = nlu_manager.nlu_engine.parse_navigation_command(result)
            if 'url' in parsed:
                print(f"✅ '{command}' → URL: {parsed['url']}")
            else:
                print(f"❌ '{command}' → No URL extracted")
        else:
            print(f"❌ '{command}' → Not recognized as navigation")


def main():
    """Run the demo"""
    print("🚀 Lighthouse.ai Demo")
    print("Voice-driven web navigator for blind and low-vision users")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    try:
        # Run demos
        demo_nlu()
        demo_safety()
        demo_commands()
        demo_navigation_parsing()
        
        print("\n🎉 Demo completed successfully!")
        print("\nNext steps:")
        print("1. Install additional dependencies: pip install selenium faster-whisper pyttsx3")
        print("2. Run the CLI: python cli.py")
        print("3. Run the API: python main.py")
        print("4. Test on websites: python scripts/test_sites.py")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
