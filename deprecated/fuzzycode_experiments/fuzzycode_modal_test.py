#!/usr/bin/env python3
"""
Test script to close FuzzyCode modal using Gemini Vision detection
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from scripts.gemini_click_helper import GeminiClickHelper
sys.path.append(str(Path(__file__).parent / "fuzzycode_steps"))
from common import load_session_info, save_session_info

# API key provided by user
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def main():
    print("Testing Gemini Vision for modal detection...\n")
    
    # Load current session
    session_info = await load_session_info()
    if not session_info:
        print("No session found. Run the FuzzyCode steps first!")
        return
    
    print(f"Session ID: {session_info['session_id']}")
    print(f"Page ID: {session_info['page_id']}")
    
    # Connect to browser
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    # Initialize Gemini helper
    helper = GeminiClickHelper(client, GEMINI_API_KEY)
    
    # First, let's detect all clickable elements to see what Gemini finds
    print("\n1. Finding all clickable elements in the page...")
    all_elements = await helper.find_all_clickable_elements(
        session_info['session_id'],
        session_info['page_id'],
        "gemini_all_elements.png"
    )
    
    print(f"\nGemini found {len(all_elements['coordinates'])} clickable elements")
    print("Check the annotated image to see what was detected")
    
    # Now specifically look for the close button
    print("\n2. Looking for the modal close button...")
    success = await helper.click_element_by_description(
        session_info['session_id'],
        session_info['page_id'],
        "X button or close button in the top right of the modal dialog",
        "gemini_close_button.png"
    )
    
    if success:
        print("\n✅ Successfully clicked the close button using Gemini detection!")
        
        # Wait and take another screenshot
        await asyncio.sleep(1)
        await client.screenshot("after_gemini_close.png")
        print("Screenshot saved: after_gemini_close.png")
        
        # Check if modal is gone
        modal_check = await client.evaluate(
            session_info['session_id'],
            session_info['page_id'],
            """
            (() => {
                const modal = document.querySelector('.modal');
                const welcomeText = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
                return {
                    modalVisible: modal && modal.offsetParent !== null,
                    welcomeTextVisible: welcomeText
                };
            })()
            """
        )
        
        print(f"\nModal visible: {modal_check['modalVisible']}")
        print(f"Welcome text visible: {modal_check['welcomeTextVisible']}")
        
        if not modal_check['modalVisible']:
            await save_session_info(session_info['session_id'], session_info['page_id'], 5)
            print("\n✅ Modal successfully closed and session saved!")
    else:
        print("\n❌ Could not find or click the close button")
        
        # Try alternative description
        print("\n3. Trying alternative description...")
        success2 = await helper.click_element_by_description(
            session_info['session_id'],
            session_info['page_id'],
            "The X or × symbol button that closes the User Login modal",
            "gemini_x_symbol.png"
        )
        
        if success2:
            print("✅ Found it with alternative description!")

if __name__ == "__main__":
    asyncio.run(main())