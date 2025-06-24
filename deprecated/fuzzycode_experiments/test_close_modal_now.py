#!/usr/bin/env python3
"""Quick test to close the modal with Gemini"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from scripts.gemini_click_helper import GeminiClickHelper
from common import load_session_info, save_session_info

GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def main():
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    print("Using Gemini to close the modal...")
    
    helper = GeminiClickHelper(client, GEMINI_API_KEY)
    
    # Find and click the X button
    success = await helper.click_element_by_description(
        session_info['session_id'],
        session_info['page_id'],
        "the X button in the top right corner of the modal",
        "close_modal_test.png"
    )
    
    if success:
        print("✅ Modal closed successfully!")
        await save_session_info(session_info['session_id'], session_info['page_id'], 5)
    else:
        print("❌ Failed to close modal")

if __name__ == "__main__":
    asyncio.run(main())