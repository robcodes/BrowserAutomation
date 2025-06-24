#!/usr/bin/env python3
"""
Simple example of using Gemini Vision to find and click elements
when traditional selectors fail.
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from scripts.gemini_click_helper import GeminiClickHelper

# API Configuration
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"  # Replace with your key
GEMINI_MODEL = "gemini-2.5-flash"  # Recommended model

async def main():
    """
    Example: Navigate to a page and click a button using visual detection
    """
    # Create browser client
    client = EnhancedBrowserClient()
    
    # Start session (use headless=False to watch it work)
    session_id = await client.create_session(headless=False)
    page_id = await client.new_page("https://example.com")
    
    # Take initial screenshot
    await client.screenshot("before_click.png")
    print("Initial screenshot saved")
    
    # Initialize Gemini helper
    helper = GeminiClickHelper(client, GEMINI_API_KEY)
    
    # Find and click an element by description
    print("\nLooking for 'More information' link...")
    success = await helper.click_element_by_description(
        session_id,
        page_id,
        "the 'More information' link",
        "gemini_detection.png"
    )
    
    if success:
        print("✅ Successfully clicked the element!")
        
        # Take screenshot after click
        await asyncio.sleep(1)  # Wait for any animations
        await client.screenshot("after_click.png")
        print("Final screenshot saved")
    else:
        print("❌ Could not find or click the element")
        
        # Try finding all clickable elements
        print("\nFinding all clickable elements on the page...")
        all_elements = await helper.find_all_clickable_elements(
            session_id,
            page_id,
            "all_clickable_elements.png"
        )
        print(f"Found {len(all_elements['coordinates'])} clickable elements")
        print("Check the annotated image to see what was detected")

if __name__ == "__main__":
    asyncio.run(main())