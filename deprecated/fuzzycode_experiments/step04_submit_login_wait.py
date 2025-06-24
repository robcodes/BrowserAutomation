#!/usr/bin/env python3
"""
Step 4: Submit Login Form - Wait for Completion Version
Clicks the Sign In button and waits for login to complete
"""
from common import *

async def step04_submit_login():
    """Submit the login form and wait for it to complete"""
    print_step_header(4, "Submit Login Form (Wait for Completion)")
    
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
        
        # Wait for login to process with multiple checkpoints
        print("\n4. Waiting for login to process...")
        wait_times = [2, 3, 5, 5]  # Total 15 seconds
        for i, wait_time in enumerate(wait_times):
            print(f"   Waiting {wait_time} seconds... (checkpoint {i+1}/4)")
            await asyncio.sleep(wait_time)
            
            # Take screenshot at each checkpoint
            screenshot_name = f"step04_login_progress_{i+1}.png"
            await client.screenshot(screenshot_name)
            print(f"   ✓ Progress screenshot: {screenshot_name}")
            
            # Quick check if we see welcome message
            check = await client.evaluate("""
                (() => {
                    const bodyText = document.body.textContent;
                    return {
                        hasWelcome: bodyText.includes('Welcome, robert.norbeau+test2@gmail.com!'),
                        stillHasSignIn: bodyText.includes('Sign In')
                    };
                })()
            """)
            
            if check['hasWelcome']:
                print("   ✅ Welcome message detected!")
                break
            elif not check['stillHasSignIn']:
                print("   ℹ️  Sign In form no longer visible")
        
        print("\n5. Taking final screenshot...")
        await client.screenshot("step04_final_state.png")
        print("   ✓ Screenshot saved: step04_final_state.png")
        print("   👀 Should show welcome modal if login succeeded")
        
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