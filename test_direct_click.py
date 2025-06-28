#!/usr/bin/env python3
"""Test direct clicking without parsing issues"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
SESSION_ID = "ee91b013"
PAGE_ID = "6029627f"

# Test clicking on Blog link (around 795, 60 based on the screenshot)
commands = [
    # Try with explicit integers
    "page.mouse.click(1090, 44)",  # Blog link position
    
    # Try with page.click on selector
    'page.click("a:has-text(\'Blog\')")',
    
    # Try with evaluate and direct click
    'page.evaluate("document.querySelector(\'a[href*=blog]\')?.click()")',
]

for i, cmd in enumerate(commands, 1):
    print(f"\n--- Test {i}: {cmd} ---")
    
    # Get URL before
    response = requests.get(f"{BASE_URL}/sessions/{SESSION_ID}/pages/{PAGE_ID}/url")
    url_before = response.json()["url"]
    print(f"URL before: {url_before}")
    
    # Execute command
    response = requests.post(
        f"{BASE_URL}/command",
        json={
            "session_id": SESSION_ID,
            "page_id": PAGE_ID,
            "command": cmd
        }
    )
    print(f"Response: {response.json()}")
    
    # Wait for navigation
    time.sleep(3)
    
    # Get URL after
    response = requests.get(f"{BASE_URL}/sessions/{SESSION_ID}/pages/{PAGE_ID}/url")
    url_after = response.json()["url"]
    print(f"URL after: {url_after}")
    print(f"Changed: {url_before != url_after}")
    
    if url_before != url_after:
        print("✓ Success! Navigation occurred.")
        break