#!/usr/bin/env python3
"""
Test persistent session by clicking the More information link
"""
import asyncio
import json
from browser_client_poc import PersistentBrowserClient

async def continue_session_demo():
    """Continue the existing session and click link"""
    # Load session info
    with open('session_info.json', 'r') as f:
        data = json.load(f)
    
    session_id = data["session_id"]
    page_id = data["page_id"]
    
    print(f"Reconnecting to session: {session_id}")
    print(f"Working with page: {page_id}\n")
    
    client = PersistentBrowserClient()
    
    # Reconnect to existing session
    await client.connect_session(session_id)
    await client.set_page(page_id)
    
    # Verify we're still on the same page
    info = await client.get_info()
    print(f"✓ Current page: {info['title']} ({info['url']})")
    
    # Click the "More information..." link
    print("\n→ Clicking 'More information...' link")
    await client.click('a[href]')  # Click the first link
    
    # Wait for navigation
    await client.wait(2000)
    
    # Get new page info
    new_info = await client.get_info()
    print(f"\n✓ Navigated to: {new_info['title']}")
    print(f"✓ New URL: {new_info['url']}")
    
    # Take screenshot of new page
    screenshot_path = await client.screenshot("after_clicking_link.png")
    print(f"\n✓ Screenshot saved: {screenshot_path}")
    
    print("\n💡 The browser session is STILL alive!")
    print("   You can continue using it with the same session ID")

if __name__ == "__main__":
    asyncio.run(continue_session_demo())