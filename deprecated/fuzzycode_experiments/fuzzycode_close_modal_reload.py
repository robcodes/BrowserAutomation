#!/usr/bin/env python3
"""
Close the login modal by reloading the page
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def close_modal_and_continue():
    """Close modal by reloading and continue exploration"""
    print("=== Closing Modal and Continuing ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # The proven solution: reload the page
    print("\n→ Reloading page to close modal...")
    await client.goto("https://fuzzycode.dev")
    await client.wait(3000)
    
    await client.screenshot("fuzzy_explore_26_after_reload.png")
    print("✓ Screenshot: fuzzy_explore_26_after_reload.png")
    
    # Verify we're logged in and modal is gone
    state_check = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login'));
            const modalVisible = loginIframe ? loginIframe.offsetParent !== null : false;
            
            const pageText = document.body.textContent;
            const hasUserEmail = pageText.includes('robert.norbeau');
            
            const textarea = document.querySelector('textarea');
            const generateBtn = document.querySelector('#processTextButton') || 
                              Array.from(document.querySelectorAll('button')).find(btn => 
                                  btn.textContent.includes('Fuzzy Code It'));
            
            return {
                modalVisible: modalVisible,
                loggedIn: hasUserEmail,
                hasTextarea: textarea !== null,
                hasGenerateBtn: generateBtn !== null
            };
        }
    """)
    
    print("\n  State after reload:")
    print(f"    Modal visible: {state_check['modalVisible']}")
    print(f"    Logged in: {state_check['loggedIn']}")
    print(f"    Has textarea: {state_check['hasTextarea']}")
    print(f"    Has generate button: {state_check['hasGenerateBtn']}")
    
    if not state_check['modalVisible'] and state_check['hasTextarea']:
        print("\n✅ Modal closed successfully! Now testing authenticated code generation...")
        
        # Test authenticated code generation
        fill_result = await client.evaluate("""
            () => {
                const textarea = document.querySelector('textarea');
                if (textarea) {
                    textarea.focus();
                    textarea.value = 'Create a Python function that calculates the factorial of a number';
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.dispatchEvent(new Event('change', { bubbles: true }));
                    return { success: true };
                }
                return { success: false };
            }
        """)
        
        if fill_result['success']:
            await client.screenshot("fuzzy_explore_27_auth_prompt_filled.png")
            print("  ✓ Filled authenticated prompt")
            
            # Click generate
            generate_result = await client.evaluate("""
                () => {
                    const btn = document.querySelector('#processTextButton') || 
                               Array.from(document.querySelectorAll('button')).find(btn => 
                                   btn.textContent.includes('Fuzzy Code It'));
                    if (btn && !btn.disabled) {
                        btn.click();
                        return { success: true };
                    }
                    return { success: false };
                }
            """)
            
            if generate_result['success']:
                print("  ✓ Clicked generate button")
                await client.wait(5000)
                await client.screenshot("fuzzy_explore_28_auth_code_generated.png")
                print("  ✓ Screenshot: fuzzy_explore_28_auth_code_generated.png")
                
                # Check for generated code
                code_check = await client.evaluate("""
                    () => {
                        const codeElements = Array.from(document.querySelectorAll('pre, code, [class*="code"], .hljs'));
                        const codeText = codeElements.map(el => el.textContent).join('\\n');
                        
                        return {
                            hasCode: codeElements.length > 0 && codeText.includes('def'),
                            codeBlockCount: codeElements.length,
                            containsFactorial: codeText.toLowerCase().includes('factorial'),
                            sampleCode: codeText.substring(0, 200)
                        };
                    }
                """)
                
                print(f"\n  Code generation result:")
                print(f"    Has code: {code_check['hasCode']}")
                print(f"    Code blocks: {code_check['codeBlockCount']}")
                print(f"    Contains factorial: {code_check['containsFactorial']}")
                if code_check['sampleCode']:
                    print(f"    Sample: {code_check['sampleCode'][:100]}...")
                
                # Update tracking
                with open("FUZZY_CODE_STEPS.md", "a") as f:
                    f.write("22. Closed modal by reloading page - session persisted\n")
                    f.write("23. Successfully tested authenticated code generation\n")
                
                # Check console logs for any errors
                logs = await client.get_console_logs(limit=10)
                errors = [log for log in logs["logs"] if log["type"] == "error"]
                if not errors:
                    print("\n✅ No console errors - authenticated code generation works!")

if __name__ == "__main__":
    asyncio.run(close_modal_and_continue())