#!/usr/bin/env python3
"""
Step 5: Close Welcome Modal - Visual Verification Version
Uses screenshots for verification instead of programmatic detection
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common import *
from clients.gemini_detector import GeminiDetector

# Gemini API configuration
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def step05_close_modal():
    """Close the welcome modal using visual verification"""
    print_step_header(5, "Close Welcome Modal (Visual Verification)")
    
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
        await client.screenshot("step05_check_modal.png")
        print("   ✓ Screenshot saved: step05_check_modal.png")
        print("   👀 Please check the screenshot to see if modal is present")
        
        # Try clicking the X button using known position
        print("\n2. Attempting to click X button at typical position...")
        
        # Common positions for X button based on our testing
        x_positions = [
            (1199, 55, "top_right_x"),
            (961, 55, "modal_x_position"),
            (1175, 40, "alternative_x")
        ]
        
        for x, y, label in x_positions:
            print(f"\n   Trying position ({x}, {y})...")
            click_result = await client.click_at(x, y, f"close_modal_{label}")
            
            if click_result['screenshot_path']:
                print(f"   📸 Crosshair screenshot: {click_result['screenshot_path']}")
            
            # Wait a bit
            await asyncio.sleep(1)
            
            # Take screenshot after click
            screenshot_name = f"step05_after_click_{label}.png"
            await client.screenshot(screenshot_name)
            print(f"   ✓ Post-click screenshot: {screenshot_name}")
            print("   👀 Check if modal is closed in this screenshot")
            
            # Give it a moment - if it worked, we're done
            await asyncio.sleep(0.5)
        
        # Alternative: Try ESC key
        print("\n3. Trying ESC key as fallback...")
        await client.evaluate("""
            document.dispatchEvent(new KeyboardEvent('keydown', {
                key: 'Escape',
                code: 'Escape',
                keyCode: 27,
                bubbles: true
            }));
        """)
        
        await asyncio.sleep(1)
        
        # Final screenshot
        await client.screenshot("step05_final_state.png")
        print("\n4. Final screenshot saved: step05_final_state.png")
        print("   👀 Please verify if the modal is closed")
        
        # Save session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 5)
        
        print_step_result(True, "Modal close attempted - check screenshots for verification")
        return True
                
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