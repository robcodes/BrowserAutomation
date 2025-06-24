#!/usr/bin/env python3
"""
Step 6: Generate Code - Visual Verification Version
Uses screenshots to verify code generation
"""
from common import *

async def step06_generate_code():
    """Generate code using FuzzyCode with visual verification"""
    print_step_header(6, "Generate Code (Visual Verification)")
    
    # Load session from previous step
    session_info = await load_session_info()
    if not session_info or session_info['last_step'] < 5:
        print("❌ Previous steps not completed. Run step05_close_modal.py first!")
        return False
    
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        # Test prompt
        test_prompt = "Write a Python function to check if a number is prime"
        
        print("\n1. Taking initial screenshot...")
        await client.screenshot("step06_initial_state.png")
        print("   ✓ Screenshot saved: step06_initial_state.png")
        print("   👀 Should show FuzzyCode interface without modal")
        
        print("\n2. Finding and filling textarea...")
        # Try to find textarea
        textarea_info = await client.evaluate("""
            (() => {
                const textarea = document.querySelector('textarea[placeholder*="Enter your request"]');
                if (!textarea) return null;
                
                const rect = textarea.getBoundingClientRect();
                return {
                    found: true,
                    x: rect.left + rect.width / 2,
                    y: rect.top + rect.height / 2
                };
            })()
        """)
        
        if textarea_info and textarea_info['found']:
            print(f"   Found textarea at ({textarea_info['x']}, {textarea_info['y']})")
            
            # Click on textarea first
            await client.click_at(textarea_info['x'], textarea_info['y'], "textarea_focus")
            await asyncio.sleep(0.5)
            
            # Fill the textarea
            print(f"\n3. Entering prompt: '{test_prompt}'...")
            await client.evaluate(f"""
                (() => {{
                    const textarea = document.querySelector('textarea[placeholder*="Enter your request"]');
                    if (textarea) {{
                        textarea.value = '{test_prompt}';
                        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }})()
            """)
        else:
            print("   ⚠️  Textarea not found - may be blocked by modal")
        
        await asyncio.sleep(1)
        
        print("\n4. Taking screenshot with prompt...")
        await client.screenshot("step06_prompt_entered.png")
        print("   ✓ Screenshot saved: step06_prompt_entered.png")
        print("   👀 Should show textarea with the prompt text")
        
        print("\n5. Finding generate button...")
        button_info = await client.evaluate("""
            (() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const fuzzyBtn = buttons.find(btn => btn.textContent.includes('Fuzzy Code It'));
                
                if (fuzzyBtn) {
                    const rect = fuzzyBtn.getBoundingClientRect();
                    return {
                        exists: true,
                        enabled: !fuzzyBtn.disabled,
                        text: fuzzyBtn.textContent.trim(),
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2
                    };
                }
                return { exists: false };
            })()
        """)
        
        if button_info and button_info['exists']:
            print(f"   Found button: '{button_info['text']}' at ({button_info['x']}, {button_info['y']})")
            
            print(f"\n6. Clicking 'Fuzzy Code It!' button...")
            click_result = await client.click_at(button_info['x'], button_info['y'], "fuzzy_code_it_button")
            
            print(f"   Click result: {click_result['success']}")
            if click_result['screenshot_path']:
                print(f"   📸 Crosshair screenshot: {click_result['screenshot_path']}")
        else:
            print("   ⚠️  Generate button not found - may be blocked")
        
        print("\n7. Waiting for code generation...")
        await asyncio.sleep(5)
        
        print("\n8. Taking screenshot of result...")
        await client.screenshot("step06_code_generated.png")
        print("   ✓ Screenshot saved: step06_code_generated.png")
        print("   👀 Should show generated code output")
        
        # Take another screenshot after more waiting
        await asyncio.sleep(3)
        await client.screenshot("step06_final_result.png")
        print("\n9. Final screenshot saved: step06_final_result.png")
        print("   👀 Check if code was successfully generated")
        
        # Update session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 6)
        
        print_step_result(True, "Code generation attempted - check screenshots for result")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await client.screenshot("step06_error.png")
        print("   Error screenshot saved: step06_error.png")
        return False

if __name__ == "__main__":
    result = asyncio.run(step06_generate_code())
    import sys
    sys.exit(0 if result else 1)