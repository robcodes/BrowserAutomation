#!/usr/bin/env python3
"""
Step 4: Submit Login Form
- Clicks the Sign In button
- Waits for login to process
- Checks for success or error messages
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
        
        print("\n3. Clicking Sign In button with crosshair...")
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
            "Should show either welcome message or error message"
        )
        
        print("\n5. Checking login result...")
        login_result = await client.evaluate("""
            (() => {
                const bodyText = document.body.textContent;
                
                // Check for various indicators
                const hasInvalidLogin = bodyText.includes('Invalid login credentials');
                const hasWelcome = bodyText.includes('Welcome');
                const hasSignOut = bodyText.includes('Sign Out');
                const hasError = bodyText.includes('error') || bodyText.includes('Error');
                
                // Check if modal is still showing welcome
                const modal = document.querySelector('.modal, [role="dialog"]');
                const modalVisible = modal && modal.offsetParent !== null;
                
                // Check if we're logged in by looking for email
                const hasEmail = bodyText.includes('robert.norbeau+test2@gmail.com');
                
                // Check specifically for welcome modal text
                const welcomeModalText = modal ? modal.textContent : '';
                const hasWelcomeModal = welcomeModalText.includes('Welcome') && 
                                       welcomeModalText.includes('robert.norbeau+test2@gmail.com');
                
                return {
                    hasInvalidLogin,
                    hasWelcome,
                    hasSignOut,
                    hasError,
                    modalVisible,
                    hasEmail,
                    hasWelcomeModal,
                    loginStatus: hasInvalidLogin ? 'failed' : 
                                (hasWelcomeModal || (hasWelcome && hasEmail) ? 'success' : 'unknown')
                };
            })()
        """)
        
        print(f"   🔍 Login result check:")
        print(f"      Invalid login message: {login_result['hasInvalidLogin']}")
        print(f"      Welcome message: {login_result['hasWelcome']}")
        print(f"      Email visible: {login_result['hasEmail']}")
        print(f"      Modal visible: {login_result['modalVisible']}")
        print(f"      Login status: {login_result['loginStatus']}")
        
        # Check console for errors
        print("\n6. Checking console for errors...")
        await client.print_recent_errors()
        
        # Update session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 4)
        
        # Determine success
        success = login_result['loginStatus'] == 'success'
        
        if login_result['hasInvalidLogin']:
            print("\n⚠️  Invalid login credentials!")
            print(f"   Check that credentials are correct:")
            print(f"   Username: {TEST_USERNAME}")
            print(f"   Password: {TEST_PASSWORD}")
        
        print_step_result(
            success,
            "Login successful!" if success else f"Login {login_result['loginStatus']}"
        )
        
        return success
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step04_error.png", "Error state")
        return False

if __name__ == "__main__":
    result = asyncio.run(step04_submit_login())
    import sys
    sys.exit(0 if result else 1)