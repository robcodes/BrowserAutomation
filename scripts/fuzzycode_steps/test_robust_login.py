#!/usr/bin/env python3
"""
Test robust login flow
"""
from common import *
from find_login_iframe import get_find_login_iframe_js, get_login_iframe_accessor_js

async def test_robust_login():
    """Test the robust login approach"""
    print("Testing robust login flow...")
    
    session_info = await load_session_info()
    if not session_info:
        print("❌ No session found! Run step01 first.")
        return False
    
    client = BrowserClient()
    await client.connect_session(session_info['session_id'])
    client.page_id = session_info['page_id']
    
    print("\n1. Clicking profile icon to open login...")
    # Click profile icon
    await client.click_with_crosshair(selector='.user-profile-icon', label='profile_icon')
    await wait_and_check(client, WAIT_LONG, "Wait for modal")
    
    print("\n2. Finding login iframe...")
    iframe_info = await client.evaluate(get_find_login_iframe_js())
    print(f"   Iframe search result: {iframe_info}")
    
    if not iframe_info.get('found'):
        print("❌ No login iframe found!")
        return False
    
    print(f"   ✓ Found login iframe at index {iframe_info['index']}")
    
    print("\n3. Filling login form...")
    fill_result = await client.evaluate(
        get_login_iframe_accessor_js(TEST_USERNAME, TEST_PASSWORD)
    )
    print(f"   Fill result: {fill_result}")
    
    if not fill_result.get('success'):
        print(f"❌ Failed: {fill_result.get('reason')}")
        return False
    
    print("\n4. Taking screenshot...")
    await client.screenshot("robust_login_filled.png")
    print("   📸 Screenshot saved: robust_login_filled.png")
    
    print("\n5. Clicking Sign In button...")
    # Find and click sign in button
    click_result = await client.evaluate(f"""
        (() => {{
            const loginIframe = document.querySelectorAll('iframe')[{iframe_info['index']}];
            const iframeDoc = loginIframe.contentDocument;
            
            // Find sign in button
            const buttons = Array.from(iframeDoc.querySelectorAll('button'));
            const signInBtn = buttons.find(btn => btn.textContent.includes('Sign In'));
            
            if (signInBtn) {{
                signInBtn.click();
                return {{ success: true }};
            }}
            
            // Try form submit as fallback
            const form = iframeDoc.querySelector('form');
            if (form) {{
                form.submit();
                return {{ success: true, method: 'form.submit' }};
            }}
            
            return {{ success: false, reason: 'No button or form found' }};
        }})()
    """)
    
    print(f"   Click result: {click_result}")
    
    print("\n6. Waiting for login to complete...")
    await wait_and_check(client, WAIT_EXTRA_LONG, "Wait for login")
    
    # Take final screenshot
    await client.screenshot("robust_login_result.png")
    print("   📸 Screenshot saved: robust_login_result.png")
    
    return True

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_robust_login())
    if success:
        print("\n✅ Test completed! Check the screenshots.")