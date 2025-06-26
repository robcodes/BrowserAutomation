#!/usr/bin/env python3
"""Check final state after login"""
from common import *

async def check_final_state():
    session_info = await load_session_info()
    client = BrowserClient()
    await client.connect_session(session_info['session_id'])
    client.page_id = session_info['page_id']
    
    await client.screenshot('final_logged_in_state.png')
    print("Screenshot saved: final_logged_in_state.png")
    
    # Check if we're ready to generate code
    state = await client.evaluate("""
        (() => {
            const textarea = document.querySelector('textarea');
            const button = Array.from(document.querySelectorAll('button'))
                .find(b => b.textContent.includes('Fuzzy Code It'));
            const modal = document.querySelector('.modal:not(.fade)');
            
            return {
                hasTextarea: textarea !== null,
                hasButton: button !== null,
                modalGone: modal === null || window.getComputedStyle(modal).display === 'none',
                url: window.location.href
            };
        })()
    """)
    
    print(f"\nFinal state: {state}")
    
    if state['hasTextarea'] and state['hasButton'] and state['modalGone']:
        print("\n✅ Success! Ready to generate code on FuzzyCode.")
        print("   - Logged in successfully")
        print("   - Modal closed")
        print("   - Main interface ready")
    
    return state

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_final_state())