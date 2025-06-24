#!/usr/bin/env python3
"""
Step 5: Close Welcome Modal (Direct X button click)
- Clicks the X button on the modal
- Uses specific coordinates
"""
from common import *

async def step05_close_modal():
    """Close the welcome modal by clicking X"""
    print_step_header(5, "Close Welcome Modal (Direct)")
    
    # Load session from previous step
    session_info = await load_session_info()
    if not session_info or session_info['last_step'] < 4:
        print("❌ Previous steps not completed. Run step04 first!")
        return False
    
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        print("\n1. Taking screenshot to see current state...")
        await take_screenshot_and_check(
            client,
            "step05_current_state.png",
            "Current state - should show welcome modal"
        )
        
        print("\n2. Looking for the X button...")
        # Based on the screenshot, the X is at approximately (1184, 53)
        # Let's click slightly to the left to hit the center
        x_coord = 1180
        y_coord = 53
        
        print(f"   Clicking X button at ({x_coord}, {y_coord})...")
        await client.click_with_crosshair(
            x=x_coord, 
            y=y_coord, 
            label='modal_x_button'
        )
        
        await wait_and_check(client, 1000, "Waiting for modal to close")
        
        print("\n3. Taking final screenshot...")
        await take_screenshot_and_check(
            client,
            "step05_modal_closed.png",
            "Modal should be closed"
        )
        
        # Update session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 5)
        
        print_step_result(True, "Modal close attempted - check screenshot")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step05_error.png", "Error state")
        return False

if __name__ == "__main__":
    result = asyncio.run(step05_close_modal())
    import sys
    sys.exit(0 if result else 1)