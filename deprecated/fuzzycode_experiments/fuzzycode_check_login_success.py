#\!/usr/bin/env python3
"""
Check if login succeeded
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def check_login_success():
    """Check if login was successful"""
    print("=== Checking Login Success ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Wait for login to process
    await client.wait(3000)
    
    # Take screenshot
    await client.screenshot("fuzzy_explore_20_after_login_wait.png")
    print("✓ Screenshot: fuzzy_explore_20_after_login_wait.png")
    
    # Check current state
    state_check = await client.evaluate("""
        () => {
            // Check if login modal is still visible
            const iframes = Array.from(document.querySelectorAll('iframe'));
            const loginIframe = iframes.find(f => f.src.includes('user_login'));
            const loginVisible = loginIframe ? loginIframe.offsetParent \!== null : false;
            
            // Check for user info in page
            const pageText = document.body.textContent;
            const hasUserEmail = pageText.includes('robert.norbeau');
            
            // Check if we can now generate code
            const textarea = document.querySelector('textarea');
            const generateButton = document.querySelector('#processTextButton') || 
                                 Array.from(document.querySelectorAll('button')).find(btn => 
                                     btn.textContent.includes('Fuzzy Code It'));
            
            return {
                loginModalVisible: loginVisible,
                hasUserEmail: hasUserEmail,
                hasTextarea: textarea \!== null,
                hasGenerateButton: generateButton \!== null,
                currentUrl: window.location.href
            };
        }
    """)
    
    print("\n  Current state:")
    print(f"    Login modal visible: {state_check['loginModalVisible']}")
    print(f"    User email in page: {state_check['hasUserEmail']}")
    print(f"    Has textarea: {state_check['hasTextarea']}")
    print(f"    Has generate button: {state_check['hasGenerateButton']}")
    print(f"    Current URL: {state_check['currentUrl']}")
    
    if not state_check['loginModalVisible'] or state_check['hasUserEmail']:
        print("\n✅ Login successful\!")
        
        # Update tracking files
        with open("FUZZY_CODE_STEPS.md", "a") as f:
            f.write("17. Successfully logged in using direct iframe access with inputs[0] and inputs[1]\n")
            f.write("18. Login modal closed after successful authentication\n")
        
        # Now test authenticated code generation
        print("\n→ Testing authenticated code generation...")
        
        if state_check['hasTextarea'] and state_check['hasGenerateButton']:
            # Fill prompt
            fill_result = await client.evaluate("""
                () => {
                    const textarea = document.querySelector('textarea');
                    if (textarea) {
                        textarea.focus();
                        textarea.value = 'Create a Python function to calculate fibonacci numbers';
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        return { success: true };
                    }
                    return { success: false };
                }
            """)
            
            if fill_result['success']:
                await client.wait(500)
                await client.screenshot("fuzzy_explore_21_authenticated_prompt.png")
                print("  ✓ Filled prompt for authenticated test")
                
                # Click generate
                generate_result = await client.evaluate("""
                    () => {
                        const btn = document.querySelector('#processTextButton') || 
                                   Array.from(document.querySelectorAll('button')).find(btn => 
                                       btn.textContent.includes('Fuzzy Code It'));
                        if (btn && \!btn.disabled) {
                            btn.click();
                            return { success: true };
                        }
                        return { success: false };
                    }
                """)
                
                if generate_result['success']:
                    print("  ✓ Clicked generate button")
                    await client.wait(5000)
                    await client.screenshot("fuzzy_explore_22_authenticated_generation.png")
                    print("  ✓ Screenshot: fuzzy_explore_22_authenticated_generation.png")

if __name__ == "__main__":
    asyncio.run(check_login_success())
ENDOFFILE < /dev/null
