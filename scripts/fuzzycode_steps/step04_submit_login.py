#!/usr/bin/env python3
"""
Step 4: Submit Login Form
- Clicks the Sign In button
- Waits for login to process
- Takes screenshot for visual verification (DO NOT trust programmatic checks!)
"""
from common import *

async def step04_submit_login():
    """Submit the login form and check result"""
    print_step_header(4, "Submit Login Form")
    
    # Load session from previous step
    session_info = await load_session_info()
    if not session_info or session_info['last_step'] < 3:
        print("❌ Previous steps not completed. Run step03_fill_login.py first!")
        return False
    
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        print("\n1. Taking pre-submit screenshot...")
        await take_screenshot_and_check(
            client,
            "step04_pre_submit.png",
            "Should show filled login form ready to submit"
        )
        
        print("\n2. Finding Sign In button...")
        # First find the button location
        button_info = await client.evaluate("""
            (() => {
                const loginIframe = Array.from(document.querySelectorAll('iframe'))[1];
                if (!loginIframe) return null;
                
                const iframeDoc = loginIframe.contentDocument;
                const buttons = Array.from(iframeDoc.querySelectorAll('button'));
                const signInBtn = buttons.find(btn => btn.textContent.includes('Sign'));
                
                if (!signInBtn) return null;
                
                // Get button position relative to iframe
                const btnRect = signInBtn.getBoundingClientRect();
                const iframeRect = loginIframe.getBoundingClientRect();
                
                return {
                    x: iframeRect.left + btnRect.left + btnRect.width / 2,
                    y: iframeRect.top + btnRect.top + btnRect.height / 2,
                    text: signInBtn.textContent.trim(),
                    disabled: signInBtn.disabled
                };
            })()
        """)
        
        if not button_info:
            print("   ❌ Sign In button not found")
            return False
            
        print(f"   Found Sign In button: '{button_info['text']}' at ({button_info['x']}, {button_info['y']})")
        
        if button_info['disabled']:
            print("   ❌ Sign In button is disabled")
            return False
        
        print("\n3. Clicking Sign In button with deep element detection...")
        print("   🔬 Using deep click to handle iframe elements")
        click_result = await client.click_at(button_info['x'], button_info['y'], "sign_in_button")
        
        print(f"   Click result: {click_result['success']}")
        if click_result['screenshot_path']:
            print(f"   📸 Crosshair screenshot: {click_result['screenshot_path']}")
        
        if not click_result.get('success'):
            print(f"   ❌ Failed to click Sign In: {click_result.get('reason')}")
            return False
        
        await wait_and_check(client, WAIT_LONG, "Waiting for login to process")
        
        print("\n4. Taking post-submit screenshot...")
        await take_screenshot_and_check(
            client,
            "step04_post_submit.png",
            "CHECK THE SCREENSHOT: Should show either welcome modal OR login form with error"
        )
        
        print("\n5. ⚠️  IMPORTANT: Check the screenshot above to verify login result!")
        print("   - If you see a welcome modal, login succeeded")
        print("   - If you see the login form still, login failed")
        print("   - Only the screenshot tells the truth!")
        
        # Update session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 4)
        
        print_step_result(
            True,  # Always return True since only visual verification matters
            "Step completed - CHECK SCREENSHOT to verify login result"
        )
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step04_error.png", "Error state")
        return False

if __name__ == "__main__":
    result = asyncio.run(step04_submit_login())
    import sys
    sys.exit(0 if result else 1)