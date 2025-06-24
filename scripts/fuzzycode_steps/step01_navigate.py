#!/usr/bin/env python3
"""
Step 1: Navigate to FuzzyCode
- Creates a new browser session
- Navigates to fuzzycode.dev
- Verifies page loaded correctly
"""
from common import *

async def step01_navigate(headless=True):
    """Navigate to FuzzyCode homepage"""
    print_step_header(1, "Navigate to FuzzyCode")
    
    client = BrowserClient()  # Use crosshair client
    
    try:
        print("\n1. Creating browser session...")
        print(f"   Mode: {'Headless' if headless else 'Visible'}")
        session_id = await client.create_session(headless=headless)
        print(f"   ✓ Session created: {session_id}")
        
        print("\n2. Navigating to FuzzyCode...")
        page_id = await client.new_page("https://fuzzycode.dev")
        await wait_and_check(client, WAIT_LONG, "Waiting for page to load")
        
        print("\n3. Taking screenshot...")
        await take_screenshot_and_check(
            client,
            "step01_fuzzycode_homepage.png",
            "Should show FuzzyCode homepage with textarea and 'Fuzzy Code It!' button"
        )
        
        print("\n4. Verifying page elements...")
        
        # Check for main textarea
        textarea_check = await check_element_exists(
            client,
            'textarea[placeholder*="Enter your request"]',
            "Main textarea"
        )
        
        # Check for generate button
        button_check = await client.evaluate("""
            (() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const fuzzyBtn = buttons.find(btn => btn.textContent.includes('Fuzzy Code It'));
                return {
                    exists: fuzzyBtn !== null,
                    enabled: fuzzyBtn ? !fuzzyBtn.disabled : false
                };
            })()
        """)
        print(f"   🔍 Checking 'Fuzzy Code It!' button:")
        print(f"      Exists: {button_check['exists']}")
        print(f"      Enabled: {button_check['enabled']}")
        
        # Save session for next step
        await save_session_info(session_id, page_id, 1)
        
        # Determine success
        success = (
            textarea_check['exists'] and 
            button_check['exists']
        )
        
        print_step_result(
            success,
            "Page loaded with main elements" if success else "Missing required elements"
        )
        
        return success
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step01_error.png", "Error state")
        return False

if __name__ == "__main__":
    # Check command line args
    import sys
    headless = "--visible" not in sys.argv
    
    result = asyncio.run(step01_navigate(headless=headless))
    sys.exit(0 if result else 1)