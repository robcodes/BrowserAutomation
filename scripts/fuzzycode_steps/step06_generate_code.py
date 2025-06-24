#!/usr/bin/env python3
"""
Step 6: Generate Code
- Enters a prompt in the textarea
- Clicks the 'Fuzzy Code It!' button
- Waits for code generation
- Verifies code output appears
"""
from common import *

async def step06_generate_code():
    """Generate code using FuzzyCode"""
    print_step_header(6, "Generate Code")
    
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
        
        print("\n1. Checking textarea is ready...")
        textarea_check = await check_element_exists(
            client,
            'textarea[placeholder*="Enter your request"]',
            "Main textarea"
        )
        
        if not textarea_check['exists']:
            print("   ❌ Textarea not found!")
            return False
        
        print(f"\n2. Entering prompt: '{test_prompt}'...")
        fill_result = await client.evaluate(f"""
            (() => {{
                const textarea = document.querySelector('textarea[placeholder*="Enter your request"]');
                if (textarea) {{
                    textarea.value = '{test_prompt}';
                    textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return {{ success: true, value: textarea.value }};
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
        
        print("\n4. Finding generate button...")
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
        
        print(f"   Button check: {button_info}")
        
        if not button_info['exists'] or not button_info['enabled']:
            print("   ❌ Generate button not ready!")
            return False
        
        print(f"\n5. Clicking 'Fuzzy Code It!' button at ({button_info['x']}, {button_info['y']})...")
        click_result = await client.click_at(button_info['x'], button_info['y'], "fuzzy_code_it_button")
        
        print(f"   Click result: {click_result['success']}")
        if click_result['screenshot_path']:
            print(f"   📸 Crosshair screenshot: {click_result['screenshot_path']}")
        
        print("\n6. Waiting for code generation...")
        await wait_and_check(client, WAIT_EXTRA_LONG, "Waiting for code to generate")
        
        print("\n7. Taking screenshot of result...")
        await take_screenshot_and_check(
            client,
            "step06_code_generated.png",
            "Should show generated code output"
        )
        
        print("\n8. Checking for generated code...")
        code_check = await client.evaluate("""
            (() => {
                // Look for code output in various possible containers
                const codeElements = document.querySelectorAll('pre, code, .code-output, [class*="code"]');
                let hasCode = false;
                let codeSnippet = '';
                
                for (const elem of codeElements) {
                    const text = elem.textContent.trim();
                    if (text.length > 20 && (text.includes('def') || text.includes('function') || text.includes('prime'))) {
                        hasCode = true;
                        codeSnippet = text.substring(0, 100);
                        break;
                    }
                }
                
                // Also check for any new content that might be code
                const bodyText = document.body.textContent;
                const hasPrimeKeyword = bodyText.includes('prime') || bodyText.includes('Prime');
                const hasDefKeyword = bodyText.includes('def ') || bodyText.includes('function ');
                
                return {
                    hasCode,
                    codeSnippet,
                    hasPrimeKeyword,
                    hasDefKeyword,
                    codeElementCount: codeElements.length
                };
            })()
        """)
        
        print(f"   🔍 Code generation check:")
        print(f"      Has code: {code_check['hasCode']}")
        print(f"      Code elements found: {code_check['codeElementCount']}")
        print(f"      Has 'prime' keyword: {code_check['hasPrimeKeyword']}")
        print(f"      Has function definition: {code_check['hasDefKeyword']}")
        if code_check['codeSnippet']:
            print(f"      Code snippet: {code_check['codeSnippet']}...")
        
        # Check console for any errors
        print("\n9. Checking console for errors...")
        await client.print_recent_errors()
        
        # Update session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 6)
        
        # Determine success
        success = code_check['hasCode'] or (code_check['hasPrimeKeyword'] and code_check['hasDefKeyword'])
        
        print_step_result(
            success,
            "Code generated successfully!" if success else "Code generation failed"
        )
        
        return success
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step06_error.png", "Error state")
        return False

if __name__ == "__main__":
    result = asyncio.run(step06_generate_code())
    import sys
    sys.exit(0 if result else 1)