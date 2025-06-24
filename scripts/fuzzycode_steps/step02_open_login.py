#!/usr/bin/env python3
"""
Step 2: Open Login Modal
- Clicks the profile icon in left sidebar
- Waits for login modal to appear
- Verifies iframe is accessible
"""
from common import *

async def step02_open_login():
    """Click profile icon and open login modal"""
    print_step_header(2, "Open Login Modal")
    
    # Load session from previous step
    session_info = await load_session_info()
    if not session_info:
        print("❌ No session info found. Run step01_navigate.py first!")
        return False
    
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        print("\n1. Looking for profile icon...")
        # Based on our documentation: profile icon at (49, 375) with class user-profile-icon
        profile_check = await check_element_exists(
            client,
            '.user-profile-icon',
            "Profile icon"
        )
        
        if not profile_check['exists']:
            # Try clicking at known position with crosshair
            print("   Profile icon not found by class, trying position (49, 375)...")
            click_result = await client.click_at(49, 375, "profile_icon_position")
            print(f"   Click result: {click_result['success']}")
            if click_result['screenshot_path']:
                print(f"   📸 Crosshair screenshot: {click_result['screenshot_path']}")
        else:
            print("\n2. Clicking profile icon...")
            click_result = await client.click_with_crosshair(
                selector='.user-profile-icon',
                label="profile_icon"
            )
            print(f"   Click result: {click_result['success']}")
            if click_result['screenshot_path']:
                print(f"   📸 Crosshair screenshot: {click_result['screenshot_path']}")
        
        await wait_and_check(client, WAIT_LONG, "Waiting for modal to appear")
        
        print("\n3. Taking screenshot...")
        await take_screenshot_and_check(
            client,
            "step02_login_modal_open.png",
            "Should show login modal with username/password fields"
        )
        
        print("\n4. Checking for login iframe...")
        iframe_check = await client.evaluate("""
            (() => {
                const iframes = Array.from(document.querySelectorAll('iframe'));
                console.log('Found ' + iframes.length + ' iframes');
                
                // The login iframe is typically the second one
                if (iframes.length > 1) {
                    const loginIframe = iframes[1];
                    try {
                        const iframeDoc = loginIframe.contentDocument;
                        const inputs = iframeDoc.querySelectorAll('input');
                        const form = iframeDoc.querySelector('form');
                        const buttons = iframeDoc.querySelectorAll('button');
                        
                        return {
                            found: true,
                            accessible: true,
                            inputCount: inputs.length,
                            hasForm: form !== null,
                            buttonCount: buttons.length,
                            src: loginIframe.src
                        };
                    } catch (e) {
                        return {
                            found: true,
                            accessible: false,
                            error: e.message
                        };
                    }
                }
                
                return {
                    found: false,
                    iframeCount: iframes.length
                };
            })()
        """)
        
        print(f"   🔍 Login iframe check:")
        print(f"      Found: {iframe_check.get('found', False)}")
        print(f"      Accessible: {iframe_check.get('accessible', False)}")
        print(f"      Input count: {iframe_check.get('inputCount', 0)}")
        print(f"      Has form: {iframe_check.get('hasForm', False)}")
        print(f"      Button count: {iframe_check.get('buttonCount', 0)}")
        
        # Update session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 2)
        
        # Determine success
        success = (
            iframe_check.get('found', False) and
            iframe_check.get('accessible', False) and
            iframe_check.get('inputCount', 0) > 0
        )
        
        print_step_result(
            success,
            "Login modal opened successfully" if success else "Login modal not ready"
        )
        
        return success
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step02_error.png", "Error state")
        return False

if __name__ == "__main__":
    result = asyncio.run(step02_open_login())
    import sys
    sys.exit(0 if result else 1)