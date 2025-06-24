#!/usr/bin/env python3
"""Quick script to close the modal using the X button"""
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
    
    print("Looking for X button in modal header...")
    
    # The subagent found that the X button is in the modal header
    result = await client.click('.modal-header button.close, .modal-header .close, .modal-header button[aria-label="Close"]')
    print(f"Click result: {result}")
    
    await asyncio.sleep(1)
    
    # Take screenshot
    await client.screenshot('modal_closed_x_button.png')
    print("Screenshot saved as modal_closed_x_button.png")
    
    # Check if modal is gone
    check = await client.evaluate("""
        (() => {
            const modal = document.querySelector('.modal');
            const welcomeText = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
            return {
                modalVisible: modal && modal.offsetParent !== null,
                welcomeTextVisible: welcomeText
            };
        })()
    """)
    
    print(f"Modal visible: {check['modalVisible']}")
    print(f"Welcome text visible: {check['welcomeTextVisible']}")
    
    if not check['modalVisible']:
        print("✅ Modal successfully closed!")
        await save_session_info(session_info['session_id'], session_info['page_id'], 5)
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())