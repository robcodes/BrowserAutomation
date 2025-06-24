#!/usr/bin/env python3
"""Simple script to close the modal"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from clients.browser_client_enhanced import EnhancedBrowserClient
from common import load_session_info, save_session_info

async def main():
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    print("Trying different methods to close modal...")
    
    # Method 1: Click the X button (simple selector)
    print("\n1. Trying to click X button...")
    try:
        result = await client.click('button.close')
        print(f"Click button.close result: {result}")
    except Exception as e:
        print(f"Failed: {e}")
    
    await asyncio.sleep(1)
    
    # Method 2: Press ESC
    print("\n2. Trying ESC key...")
    esc_result = await client.evaluate("""
        (() => {
            const event = new KeyboardEvent('keydown', {
                key: 'Escape',
                code: 'Escape',
                keyCode: 27,
                which: 27,
                bubbles: true,
                cancelable: true
            });
            document.dispatchEvent(event);
            return 'ESC key pressed';
        })()
    """)
    print(f"ESC result: {esc_result}")
    
    await asyncio.sleep(1)
    
    # Take screenshot
    await client.screenshot('modal_after_attempts.png')
    print("\nScreenshot saved as modal_after_attempts.png")
    
    # Check status
    check = await client.evaluate("""
        (() => {
            const modal = document.querySelector('.modal');
            const welcomeText = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
            return {
                modalVisible: modal && modal.offsetParent !== null,
                welcomeTextVisible: welcomeText,
                modalClass: modal ? modal.className : null
            };
        })()
    """)
    
    print(f"\nModal visible: {check['modalVisible']}")
    print(f"Welcome text visible: {check['welcomeTextVisible']}")
    print(f"Modal class: {check['modalClass']}")
    
    if not check['modalVisible']:
        print("\n✅ Modal successfully closed!")
        await save_session_info(session_info['session_id'], session_info['page_id'], 5)
    else:
        print("\n❌ Modal still visible")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())