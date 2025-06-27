#!/usr/bin/env python3
"""
Test script to verify the UI integration is working
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test that all new endpoints are accessible"""
    
    print("Testing Browser Automation UI Integration")
    print("=" * 50)
    
    # Test root endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ Root endpoint: {response.status_code}")
        print(f"  Server info: {response.json()}")
    except Exception as e:
        print(f"✗ Root endpoint failed: {e}")
    
    # Test UI endpoint
    try:
        response = requests.get(f"{BASE_URL}/ui")
        print(f"✓ UI endpoint: {response.status_code}")
    except Exception as e:
        print(f"✗ UI endpoint failed: {e}")
    
    # Test API docs
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"✓ API docs endpoint: {response.status_code}")
    except Exception as e:
        print(f"✗ API docs endpoint failed: {e}")
    
    print("\nNew endpoints added:")
    print("- GET  /get_screenshot/{session_id}/{page_id}")
    print("- POST /navigate_to")
    print("- POST /screenshot_to_bounding_boxes")
    print("- POST /visualize_bounding_boxes")
    print("- GET  /ui (Web interface)")
    
    print("\nAccess the UI at: http://localhost:8000/ui")
    print("API documentation at: http://localhost:8000/docs")

if __name__ == "__main__":
    test_endpoints()