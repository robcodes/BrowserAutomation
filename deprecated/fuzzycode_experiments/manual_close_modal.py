#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from clients.browser_client_enhanced import EnhancedBrowserClient
from scripts.fuzzycode_steps.common import load_session_info, save_session_info

async def main():
    session_id, page_id, _ = load_session_info()
    client = EnhancedBrowserClient()
    
    print("Attempting to close modal...")
    
    # Try multiple strategies
    strategies = [
        # 1. Click the X button
        "button.close, button[aria-label='Close'], button.modal-close",
        # 2. Click button containing ×
        "button:has-text('×')",
        # 3. Click the outer modal X
        ".modal-header button",
    ]
    
    for selector in strategies:
        result = await client.click(session_id, page_id, selector)
        print(f"Try selector '{selector}': {result}")
        if result.get('success'):
            print("Success! Modal should be closed")
            break
        await asyncio.sleep(0.5)
    
    # Take screenshot
    await client.screenshot(session_id, page_id, 'manual_modal_closed.png')
    
    # Check if modal is gone
    modal_check = await client.evaluate(session_id, page_id, '''
        const modal = document.querySelector('.modal');
        return modal ? 'Modal still visible' : 'Modal gone';
    ''')
    print(f"Modal status: {modal_check}")
    
    await save_session_info(session_id, page_id, 5)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())