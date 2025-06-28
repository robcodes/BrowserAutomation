#!/usr/bin/env python3
"""Test clicking using the browser server API directly"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
SESSION_ID = "ee91b013"
PAGE_ID = "6029627f"

def test_clicks():
    # First, take a screenshot before
    print("Taking screenshot before click...")
    response = requests.get(f"{BASE_URL}/get_screenshot/{SESSION_ID}/{PAGE_ID}")
    if response.status_code == 200:
        with open("before_api_click.png", "wb") as f:
            import base64
            f.write(base64.b64decode(response.json()["screenshot"]))
        print("Screenshot saved: before_api_click.png")
    
    # Get current URL
    response = requests.get(f"{BASE_URL}/sessions/{SESSION_ID}/pages/{PAGE_ID}/url")
    url_before = response.json()["url"]
    print(f"Current URL: {url_before}")
    
    # Check what element is at position 795, 60
    print("\nChecking element at (795, 60)...")
    check_command = """
    (() => {
        const elem = document.elementFromPoint(795, 60);
        if (!elem) return "No element found";
        return {
            tagName: elem.tagName,
            className: elem.className,
            id: elem.id,
            text: elem.textContent?.substring(0, 50),
            href: elem.href,
            onclick: elem.onclick ? "has onclick" : "no onclick",
            isLink: elem.tagName === 'A',
            isButton: elem.tagName === 'BUTTON',
            rect: elem.getBoundingClientRect()
        };
    })()
    """
    
    response = requests.post(
        f"{BASE_URL}/pages/{PAGE_ID}/command",
        json={
            "session_id": SESSION_ID,
            "method": "evaluate",
            "params": {"expression": check_command}
        }
    )
    print(f"Element info: {json.dumps(response.json(), indent=2)}")
    
    # Test 1: Using page.mouse.click
    print("\n--- Test 1: page.mouse.click(795, 60) ---")
    response = requests.post(
        f"{BASE_URL}/command",
        json={
            "session_id": SESSION_ID,
            "page_id": PAGE_ID,
            "command": "page.mouse.click(795, 60)"
        }
    )
    print(f"Response: {response.json()}")
    
    time.sleep(3)
    
    # Check URL after click
    response = requests.get(f"{BASE_URL}/sessions/{SESSION_ID}/pages/{PAGE_ID}/url")
    url_after = response.json()["url"]
    print(f"URL after click: {url_after}")
    print(f"URL changed: {url_before != url_after}")
    
    # Take screenshot after
    response = requests.get(f"{BASE_URL}/get_screenshot/{SESSION_ID}/{PAGE_ID}")
    if response.status_code == 200:
        with open("after_api_click.png", "wb") as f:
            import base64
            f.write(base64.b64decode(response.json()["screenshot"]))
        print("Screenshot saved: after_api_click.png")
    
    # Test 2: Try clicking with browser's click method
    print("\n--- Test 2: Using element.click() ---")
    click_js = """
    const elem = document.elementFromPoint(795, 60);
    if (elem) {
        elem.click();
        return "Clicked: " + elem.tagName + " " + elem.className;
    }
    return "No element found at position";
    """
    
    response = requests.post(
        f"{BASE_URL}/pages/{PAGE_ID}/command",
        json={
            "session_id": SESSION_ID,
            "method": "evaluate", 
            "params": {"expression": click_js}
        }
    )
    print(f"Click result: {response.json()}")
    
    time.sleep(3)
    
    # Final URL check
    response = requests.get(f"{BASE_URL}/sessions/{SESSION_ID}/pages/{PAGE_ID}/url")
    final_url = response.json()["url"]
    print(f"Final URL: {final_url}")

if __name__ == "__main__":
    test_clicks()