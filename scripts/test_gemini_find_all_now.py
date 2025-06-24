#!/usr/bin/env python3
"""Test Gemini find all approach right now"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from scripts.gemini_click_helper import GeminiClickHelper
from scripts.fuzzycode_steps.common import load_session_info

GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def main():
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    helper = GeminiClickHelper(client, GEMINI_API_KEY)
    
    # Find all clickable elements
    print("Finding ALL clickable elements...")
    result = await helper.find_all_clickable_elements(
        session_info['session_id'],
        session_info['page_id'],
        "find_all_test.png"
    )
    
    print(f"\nFound {len(result['coordinates'])} elements")
    
    # Check if any looks like an X button
    if result['coordinates']:
        print("\nLooking at coordinates to find X button...")
        for i, coords in enumerate(result['coordinates']):
            print(f"Element {i+1}: {coords}")
            # The X button is typically in top-right, so high xmin/xmax, low ymin/ymax
            ymin, xmin, ymax, xmax = coords
            if xmin > 900 and ymin < 100:  # Top-right area
                print(f"  -> This could be the X button (top-right position)")

if __name__ == "__main__":
    asyncio.run(main())