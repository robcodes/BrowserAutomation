#!/usr/bin/env python3
"""
Step 3: Fill Login Form
- Fills username and password fields
- Uses direct array access (inputs[0] and inputs[1])
- Verifies fields are filled correctly
"""
from common import *

async def step03_fill_login():
    """Fill the login form with test credentials"""
    print_step_header(3, "Fill Login Form")
    
    # Load session from previous step
    session_info = await load_session_info()
    if not session_info or session_info['last_step'] < 2:
        print("❌ Previous steps not completed. Run step02_open_login.py first!")
        return False
    
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        print("\n1. Checking login iframe is still accessible...")
        iframe_check = await client.evaluate("""
            (() => {
                const iframes = Array.from(document.querySelectorAll('iframe'));
                if (iframes.length > 1) {
                    const loginIframe = iframes[1];
                    try {
                        const iframeDoc = loginIframe.contentDocument;
                        const inputs = iframeDoc.querySelectorAll('input');
                        return {
                            accessible: true,
                            inputCount: inputs.length
                        };
                    } catch (e) {
                        return { accessible: false, error: e.message };
                    }
                }
                return { accessible: false, reason: 'No login iframe found' };
            })()
        """)
        
        if not iframe_check.get('accessible'):
            print(f"   ❌ Login iframe not accessible: {iframe_check}")
            return False
        
        print(f"   ✓ Login iframe accessible with {iframe_check['inputCount']} inputs")
        
        print("\n2. Filling login form...")
        print(f"   Username: {TEST_USERNAME}")
        print(f"   Password: {'*' * len(TEST_PASSWORD)}")
        
        fill_result = await client.evaluate(f"""
            (() => {{
                const loginIframe = Array.from(document.querySelectorAll('iframe'))[1];
                const iframeDoc = loginIframe.contentDocument;
                const inputs = iframeDoc.querySelectorAll('input');
                
                // Use direct array access as documented
                if (inputs.length >= 2) {{
                    // Username field
                    inputs[0].value = '{TEST_USERNAME}';
                    inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    // Password field
                    inputs[1].value = '{TEST_PASSWORD}';
                    inputs[1].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[1].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    return {{
                        success: true,
                        username: inputs[0].value,
                        passwordLength: inputs[1].value.length
                    }};
                }}
                
                return {{ success: false, reason: 'Not enough input fields' }};
            }})()
        """)
        
        print(f"   Fill result: {fill_result}")
        
        await wait_and_check(client, WAIT_SHORT, "Waiting for form to update")
        
        print("\n3. Taking screenshot...")
        await take_screenshot_and_check(
            client,
            "step03_login_form_filled.png",
            "Should show login form with username and password filled"
        )
        
        print("\n4. Checking form validation...")
        validation_check = await client.evaluate("""
            (() => {
                const loginIframe = Array.from(document.querySelectorAll('iframe'))[1];
                const iframeDoc = loginIframe.contentDocument;
                const form = iframeDoc.querySelector('form');
                const submitBtn = iframeDoc.querySelector('button[type="submit"]');
                const signInBtn = Array.from(iframeDoc.querySelectorAll('button'))
                    .find(btn => btn.textContent.includes('Sign'));
                
                return {
                    formValid: form ? form.checkValidity() : null,
                    submitBtnExists: submitBtn !== null,
                    submitBtnDisabled: submitBtn ? submitBtn.disabled : null,
                    signInBtnExists: signInBtn !== null,
                    signInBtnDisabled: signInBtn ? signInBtn.disabled : null,
                    signInBtnText: signInBtn ? signInBtn.textContent : null
                };
            })()
        """)
        
        print(f"   🔍 Form validation check:")
        print(f"      Form valid: {validation_check['formValid']}")
        print(f"      Submit button exists: {validation_check['submitBtnExists']}")
        print(f"      Submit button disabled: {validation_check['submitBtnDisabled']}")
        print(f"      Sign In button exists: {validation_check['signInBtnExists']}")
        print(f"      Sign In button disabled: {validation_check['signInBtnDisabled']}")
        
        # Update session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 3)
        
        # Determine success
        success = (
            fill_result.get('success', False) and
            validation_check['signInBtnExists'] and
            not validation_check['signInBtnDisabled']
        )
        
        print_step_result(
            success,
            "Form filled and ready to submit" if success else "Form not ready"
        )
        
        return success
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step03_error.png", "Error state")
        return False

if __name__ == "__main__":
    result = asyncio.run(step03_fill_login())
    import sys
    sys.exit(0 if result else 1)