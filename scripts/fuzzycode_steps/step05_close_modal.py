#!/usr/bin/env python3
"""
Step 5: Close the welcome modal after login
- Takes screenshot to check if modal is present
- If present, attempts to close it
- Relies on visual verification to confirm result
"""
from common import *

async def step05_close_modal():
    print_step_header(5, "Close Welcome Modal")
    
    # Load session info
    session_info = await load_session_info()
    if not session_info:
        print("❌ No session info found! Run previous steps first.")
        return False
    
    print(f"📋 Session ID: {session_info['session_id']}")
    print(f"📋 Page ID: {session_info['page_id']}")
    
    # Connect to existing session
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        # Take initial screenshot
        print("\n1. Taking screenshot to check for modal...")
        await take_screenshot_and_check(
            client, 
            "step05_modal_check.png", 
            "CHECK SCREENSHOT: Is there a welcome modal visible?"
        )
        
        print("\n2. ⚠️  IMPORTANT: Look at the screenshot above!")
        print("   - If you see a welcome modal, we'll try to close it")
        print("   - If no modal is visible, we're already good to go")
        
        # Find close button in the welcome modal
        print("\n3. Looking for close button in welcome modal...")
        close_button_info = await client.evaluate("""
            (() => {
                // Check in main document first
                let closeBtn = document.querySelector('.modal .close, .modal button.close, [data-dismiss="modal"], .modal-header button');
                
                if (!closeBtn) {
                    // Check in iframes
                    const iframes = Array.from(document.querySelectorAll('iframe'));
                    for (const iframe of iframes) {
                        try {
                            const iframeDoc = iframe.contentDocument;
                            if (!iframeDoc) continue;
                            
                            closeBtn = iframeDoc.querySelector('.close, button.close, [data-dismiss="modal"], .modal-header button');
                            if (closeBtn) {
                                // Get button position relative to iframe
                                const btnRect = closeBtn.getBoundingClientRect();
                                const iframeRect = iframe.getBoundingClientRect();
                                
                                return {
                                    x: iframeRect.left + btnRect.left + btnRect.width / 2,
                                    y: iframeRect.top + btnRect.top + btnRect.height / 2,
                                    text: closeBtn.textContent ? closeBtn.textContent.trim() : 'X',
                                    found: true,
                                    inIframe: true
                                };
                            }
                        } catch (e) {
                            console.warn('Cannot access iframe:', e);
                        }
                    }
                }
                
                if (closeBtn) {
                    const rect = closeBtn.getBoundingClientRect();
                    return {
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2,
                        text: closeBtn.textContent ? closeBtn.textContent.trim() : 'X',
                        found: true,
                        inIframe: false
                    };
                }
                
                // If no close button found, try to find the X in top-right of modal
                const modal = document.querySelector('.modal, .popup-window, .modal-content');
                if (modal) {
                    const rect = modal.getBoundingClientRect();
                    return {
                        x: rect.right - 20,  // 20px from right edge
                        y: rect.top + 20,    // 20px from top edge
                        text: 'X (estimated)',
                        found: false,
                        inIframe: false
                    };
                }
                
                return null;
            })()
        """)
        
        if close_button_info:
            print(f"   Found close button: '{close_button_info['text']}' at ({close_button_info['x']}, {close_button_info['y']})")
            if close_button_info['inIframe']:
                print("   📍 Button is inside an iframe - using deep click")
            
            print("\n4. Clicking close button with deep element detection...")
            print("   🔬 Using deep click to handle potential iframe elements")
            click_result = await client.click_at(close_button_info['x'], close_button_info['y'], "modal_close")
            
            print(f"   Click result: {click_result['success']}")
            if click_result.get('screenshot_path'):
                print(f"   📸 Crosshair screenshot: {click_result['screenshot_path']}")
            
            if not click_result.get('success'):
                print(f"   ⚠️  Click may have failed: {click_result.get('error', 'Unknown error')}")
            
            await wait_and_check(client, WAIT_SHORT, "Waiting after close button click")
        else:
            print("   ❌ No close button found - modal may already be closed")
        
        # Take final screenshot
        print("\n5. Taking final screenshot...")
        await take_screenshot_and_check(
            client,
            "step05_after_close.png",
            "CHECK SCREENSHOT: Modal should be gone, main interface should be visible"
        )
        
        print("\n6. ⚠️  VERIFY THE RESULT:")
        print("   - Check the screenshot above")
        print("   - Modal should be closed")
        print("   - You should see the main FuzzyCode interface")
        
        # Save session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 5)
        
        print_step_result(
            True,
            "Step completed - CHECK SCREENSHOT to verify modal is closed"
        )
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step05_error.png", "Error state")
        return False

if __name__ == "__main__":
    result = asyncio.run(step05_close_modal())
    import sys
    sys.exit(0 if result else 1)