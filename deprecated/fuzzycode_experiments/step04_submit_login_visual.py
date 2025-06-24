#!/usr/bin/env python3
"""
Step 4: Submit Login Form - Visual Verification Version
Clicks the Sign In button and uses screenshots for verification
"""
from common import *

async def step04_submit_login():
    """Submit the login form and verify with screenshots"""
    print_step_header(4, "Submit Login Form (Visual Verification)")
    
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
        await client.screenshot("step04_pre_submit.png")
        print("   ✓ Screenshot saved: step04_pre_submit.png")
        print("   👀 Should show filled login form ready to submit")
        
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
        
        print("\n3. Clicking Sign In button with crosshair...")
        click_result = await client.click_at(button_info['x'], button_info['y'], "sign_in_button")
        
        print(f"   Click result: {click_result['success']}")
        if click_result['screenshot_path']:
            print(f"   📸 Crosshair screenshot: {click_result['screenshot_path']}")
        
        # Wait for login to process
        print("\n4. Waiting for login to process...")
        await asyncio.sleep(3)
        
        print("\n5. Taking post-submit screenshot...")
        await client.screenshot("step04_post_submit.png")
        print("   ✓ Screenshot saved: step04_post_submit.png")
        print("   👀 Should show either welcome message or login result")
        
        # Take another screenshot after more waiting
        print("\n6. Waiting a bit more and taking another screenshot...")
        await asyncio.sleep(3)
        await client.screenshot("step04_login_result.png")
        print("   ✓ Screenshot saved: step04_login_result.png")
        print("   👀 Check if login succeeded (welcome modal) or failed (error message)")
        
        # Update session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 4)
        
        print_step_result(True, "Login submitted - check screenshots for result")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await client.screenshot("step04_error.png")
        print("   Error screenshot saved: step04_error.png")
        return False

if __name__ == "__main__":
    result = asyncio.run(step04_submit_login())
    import sys
    sys.exit(0 if result else 1)