#!/usr/bin/env python3
"""
Step 5: Close Welcome Modal - Gemini Vision Version
Uses visual detection to reliably find and click the X button
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common import *
from scripts.gemini_click_helper import GeminiClickHelper

# Gemini API configuration
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def step05_close_modal():
    """Close the welcome modal using Gemini Vision detection"""
    print_step_header(5, "Close Welcome Modal (Gemini Vision)")
    
    # Load session from previous step
    session_info = await load_session_info()
    if not session_info or session_info['last_step'] < 4:
        print("❌ Previous steps not completed. Run step04_submit_login.py first!")
        return False
    
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        print("\n1. Taking screenshot to check current state...")
        await take_screenshot_and_check(
            client,
            "step05_modal_state.png",
            "Should show welcome modal with X button"
        )
        
        # Quick check if modal is visible
        modal_visible = await client.evaluate("""
            (() => {
                const modal = document.querySelector('.popup-overlay');
                const hasWelcome = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
                return modal && modal.offsetParent !== null && hasWelcome;
            })()
        """)
        
        if not modal_visible:
            print("   ✓ Modal is already closed!")
            await save_session_info(session_info['session_id'], session_info['page_id'], 5)
            print_step_result(True, "Modal was already closed")
            return True
        
        print("\n2. Using Gemini Vision to find the X button...")
        
        # Initialize enhanced Gemini helper with retry logic
        from scripts.gemini_click_helper_enhanced import EnhancedGeminiClickHelper
        helper = EnhancedGeminiClickHelper(client, GEMINI_API_KEY)
        
        # Use Gemini to find and click the X button with retry and corrections
        # The X button is sometimes detected as the expand button, so we provide corrections
        success = await helper.click_element_with_retry(
            session_info['session_id'],
            session_info['page_id'],
            "the X close button in the modal header (not the expand/fullscreen button)",
            max_attempts=2,
            manual_corrections=[
                (40, 0),   # 40 pixels to the right
                (30, 0),   # 30 pixels to the right
                (50, 0),   # 50 pixels to the right
            ]
        )
        
        if success:
            print("\n3. Verifying modal is closed...")
            await wait_and_check(client, WAIT_MEDIUM, "Waiting for modal to close")
            
            # Take screenshot after closing
            await take_screenshot_and_check(
                client,
                "step05_modal_closed.png",
                "Should show FuzzyCode interface without modal"
            )
            
            # Verify modal is gone
            final_check = await client.evaluate("""
                (() => {
                    const modal = document.querySelector('.popup-overlay');
                    const hasWelcome = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
                    const backdrop = document.querySelector('.modal-backdrop');
                    
                    return {
                        modalGone: !modal || modal.offsetParent === null,
                        welcomeTextGone: !hasWelcome,
                        backdropGone: !backdrop,
                        textareaReady: document.querySelector('textarea#prompt') !== null
                    };
                })()
            """)
            
            print(f"   Modal gone: {final_check['modalGone']}")
            print(f"   Welcome text gone: {final_check['welcomeTextGone']}")
            print(f"   Backdrop gone: {final_check['backdropGone']}")
            print(f"   Textarea ready: {final_check['textareaReady']}")
            
            if final_check['modalGone'] and final_check['backdropGone']:
                await save_session_info(session_info['session_id'], session_info['page_id'], 5)
                print_step_result(True, "Modal closed successfully with Gemini Vision!")
                return True
            else:
                print_step_result(False, "Modal still present after click attempt")
                return False
        else:
            print("\n❌ Gemini couldn't find the X button")
            
            # Try alternative approach - ESC key
            print("\n3. Falling back to ESC key method...")
            await client.evaluate("""
                document.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Escape',
                    code: 'Escape',
                    keyCode: 27,
                    bubbles: true
                }));
            """)
            
            await wait_and_check(client, WAIT_SHORT, "Waiting for ESC key effect")
            
            # Check if ESC worked
            esc_result = await client.evaluate("""
                (() => {
                    const modal = document.querySelector('.popup-overlay');
                    return !modal || modal.offsetParent === null;
                })()
            """)
            
            if esc_result:
                await save_session_info(session_info['session_id'], session_info['page_id'], 5)
                print_step_result(True, "Modal closed with ESC key fallback")
                return True
            else:
                print_step_result(False, "Could not close modal")
                return False
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print_step_result(False, f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--visible', action='store_true', help='Run in visible browser mode')
    args = parser.parse_args()
    
    asyncio.run(step05_close_modal())