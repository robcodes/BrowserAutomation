#!/usr/bin/env python3
"""
Step 6: Generate Code
- Enters a prompt in the textarea
- Clicks the generate button
- Takes screenshot of the result (visual verification only!)
"""
from common import *

async def step06_generate_code():
    print_step_header(6, "Generate Code")
    
    # Load session from previous step
    session_info = await load_session_info()
    if not session_info or session_info['last_step'] < 5:
        print("❌ Previous steps not completed. Run them first!")
        return False
    
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        print("\n1. Taking initial screenshot...")
        await take_screenshot_and_check(
            client,
            "step06_ready_to_generate.png",
            "Should show empty textarea and 'Fuzzy Code It!' button"
        )
        
        print("\n2. Entering prompt in textarea...")
        test_prompt = "Write a Python function to check if a number is prime"
        
        fill_result = await client.evaluate(f"""
            (() => {{
                const textarea = document.querySelector('textarea[placeholder*="Enter your request"]');
                if (textarea) {{
                    textarea.value = "{test_prompt}";
                    textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    return {{ success: true }};
                }}
                return {{ success: false, reason: 'Textarea not found' }};
            }})()
        """)
        
        print(f"   Fill result: {fill_result}")
        
        await wait_and_check(client, WAIT_SHORT, "Waiting for input to register")
        
        print("\n3. Taking screenshot with prompt...")
        await take_screenshot_and_check(
            client,
            "step06_prompt_entered.png",
            "Should show textarea with the prompt text"
        )
        
        print("\n4. Finding and clicking generate button...")
        # Get button location
        button_info = await client.evaluate("""
            (() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const fuzzyBtn = buttons.find(btn => btn.textContent.includes('Fuzzy Code It'));
                
                if (fuzzyBtn) {
                    const rect = fuzzyBtn.getBoundingClientRect();
                    return {
                        exists: true,
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2
                    };
                }
                return { exists: false };
            })()
        """)
        
        if button_info['exists']:
            print(f"   Clicking 'Fuzzy Code It!' button at ({button_info['x']}, {button_info['y']})...")
            await client.click_at(button_info['x'], button_info['y'], "fuzzy_code_it_button")
        else:
            print("   Trying direct selector click...")
            await client.click('button:has-text("Fuzzy Code It")')
        
        print("\n5. Waiting for code generation...")
        await wait_and_check(client, WAIT_EXTRA_LONG, "Waiting for code to generate")
        
        print("\n6. Taking final screenshot...")
        await take_screenshot_and_check(
            client,
            "step06_code_generated.png",
            "CHECK SCREENSHOT: Should show generated code output"
        )
        
        print("\n7. ⚠️  IMPORTANT: Check the screenshot above!")
        print("   - You should see generated Python code")
        print("   - The code should be about checking prime numbers")
        print("   - If you see code, generation succeeded!")
        print("   - If textarea is still there unchanged, it may have failed")
        
        # Save session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 6)
        
        print_step_result(
            True,
            "Step completed - CHECK SCREENSHOT to verify code was generated"
        )
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step06_error.png", "Error state")
        return False

if __name__ == "__main__":
    result = asyncio.run(step06_generate_code())
    import sys
    sys.exit(0 if result else 1)