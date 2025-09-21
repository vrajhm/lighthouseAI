#!/usr/bin/env python3
"""Test script for Lighthouse.ai API"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8001"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing {endpoint}: {e}")
        return None

def main():
    """Run API tests"""
    print("🧪 Testing Lighthouse.ai API")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    result = test_endpoint("/")
    if result:
        print(f"✅ Root: {result['message']}")
    
    # Test 2: Health check
    print("\n2. Testing health check...")
    result = test_endpoint("/health")
    if result:
        print(f"✅ Health: {result['status']}")
        print(f"   Components: {result['components']}")
    
    # Test 3: Voice commands
    print("\n3. Testing voice commands...")
    test_commands = [
        "describe this page",
        "help me",
        "stop",
        "go to google.com"
    ]
    
    for command in test_commands:
        result = test_endpoint("/api/voice/command", "POST", {"text": command})
        if result:
            status = "✅" if result["success"] else "❌"
            print(f"{status} '{command}' → {result['intent']} (confidence: {result['confidence']:.2f})")
    
    # Test 4: Safety system
    print("\n4. Testing safety system...")
    result = test_endpoint("/api/safety/domains")
    if result:
        print(f"✅ Allowed domains: {len(result['allowed_domains'])}")
        print(f"✅ Restricted actions: {len(result['restricted_actions'])}")
    
    # Test 5: Help system
    print("\n5. Testing help system...")
    result = test_endpoint("/api/commands/help")
    if result:
        print(f"✅ Available commands: {len(result['commands'])}")
        print(f"✅ Supported intents: {len(result['supported_intents'])}")
    
    print("\n🎉 API testing completed!")
    print(f"\n📖 Interactive API docs: {BASE_URL}/docs")
    print(f"🔍 Health check: {BASE_URL}/health")

if __name__ == "__main__":
    main()
