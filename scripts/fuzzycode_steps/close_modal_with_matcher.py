#!/usr/bin/env python3
"""
Close modal using Gemini element matcher
"""
from common import *
from gemini_element_matcher import click_element_by_description

GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def close_modal_with_matcher():
    """Close modal by finding X button with Gemini"""
    print("Closing modal using Gemini element matcher...")
    
    session_info = await load_session_info()
    client = BrowserClient()
    await client.connect_session(session_info['session_id'])
    client.page_id = session_info['page_id']
    
    # Use Gemini to find and click the X close button
    print("\nSearching for X close button...")
    success = await click_element_by_description(
        client,
        "X close button in the top right corner of the modal dialog",
        GEMINI_API_KEY
    )
    
    if success:
        print("\n✓ Clicked X button")
        await wait_and_check(client, 2000, "Wait for modal to close")
        
        # Take screenshot to verify
        await client.screenshot("after_gemini_x_click.png")
        print("📸 Screenshot saved: after_gemini_x_click.png")
        
        # Check if modal is gone
        modal_check = await client.evaluate("""
            (() => {
                const modal = document.querySelector('.modal');
                const visible = modal && window.getComputedStyle(modal).display !== 'none';
                return !visible;
            })()
        """)
        
        if modal_check:
            print("✅ Modal successfully closed!")
        else:
            print("⚠️  Modal might still be visible")
    else:
        print("❌ Could not find X button")
    
    return success

if __name__ == "__main__":
    import asyncio
    asyncio.run(close_modal_with_matcher())