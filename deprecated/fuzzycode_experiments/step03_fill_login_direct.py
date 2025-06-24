#!/usr/bin/env python3
"""
Step 3: Fill Login Form (Direct approach)
- Fills username and password fields directly without iframe
- Uses CSS selectors to find input fields
- Verifies fields are filled correctly
"""
from common import *

async def step03_fill_login():
    """Fill the login form with test credentials"""
    print_step_header(3, "Fill Login Form (Direct)")
    
    # Load session from previous step
    session_info = await load_session_info()
    if not session_info or session_info['last_step'] < 2:
        print("❌ Previous steps not completed. Run step02_open_login.py first!")
        return False
    
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        print("\n1. Looking for input fields in the modal...")
        
        # First take a screenshot to see current state
        await take_screenshot_and_check(
            client,
            "step03_current_state.png",
            "Current state of login modal"
        )
        
        # Try direct selectors first
        field_check = await client.evaluate("""
            (() => {
                // Look for all input fields on the page
                const allInputs = Array.from(document.querySelectorAll('input'));
                const visibleInputs = allInputs.filter(input => {
                    const rect = input.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                });
                
                // Try to find username/email and password fields
                const usernameField = visibleInputs.find(input => 
                    input.type === 'text' || input.type === 'email' || 
                    input.placeholder?.toLowerCase().includes('username') ||
                    input.placeholder?.toLowerCase().includes('email')
                );
                
                const passwordField = visibleInputs.find(input => 
                    input.type === 'password'
                );
                
                return {
                    totalInputs: allInputs.length,
                    visibleInputs: visibleInputs.length,
                    hasUsernameField: usernameField !== undefined,
                    hasPasswordField: passwordField !== undefined,
                    usernamePlaceholder: usernameField?.placeholder,
                    passwordPlaceholder: passwordField?.placeholder
                };
            })()
        """)
        
        print(f"   Total inputs found: {field_check['totalInputs']}")
        print(f"   Visible inputs: {field_check['visibleInputs']}")
        print(f"   Username field: {field_check['hasUsernameField']} - '{field_check['usernamePlaceholder']}'")
        print(f"   Password field: {field_check['hasPasswordField']} - '{field_check['passwordPlaceholder']}'")
        
        if not (field_check['hasUsernameField'] and field_check['hasPasswordField']):
            print("\n2. Trying to find fields in iframes...")
            # If direct approach fails, check iframes
            iframe_result = await client.evaluate("""
                (() => {
                    const iframes = Array.from(document.querySelectorAll('iframe'));
                    let foundFields = false;
                    
                    for (let i = 0; i < iframes.length; i++) {
                        try {
                            const iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                            const inputs = iframeDoc.querySelectorAll('input');
                            if (inputs.length >= 2) {
                                // Fill the fields
                                inputs[0].value = '""" + TEST_USERNAME + """';
                                inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                                inputs[0].dispatchEvent(new Event('change', { bubbles: true }));
                                
                                inputs[1].value = '""" + TEST_PASSWORD + """';
                                inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
                                inputs[1].dispatchEvent(new Event('change', { bubbles: true }));
                                
                                foundFields = true;
                                return {
                                    success: true,
                                    method: 'iframe',
                                    iframeIndex: i
                                };
                            }
                        } catch (e) {
                            // Cross-origin or other access issues
                        }
                    }
                    
                    return { success: false, reason: 'No accessible iframe with input fields' };
                })()
            """)
            
            print(f"   Iframe result: {iframe_result}")
            fill_result = iframe_result
        else:
            print("\n2. Filling login form directly...")
            print(f"   Username: {TEST_USERNAME}")
            print(f"   Password: {'*' * len(TEST_PASSWORD)}")
            
            # Fill fields directly
            fill_result = await client.evaluate(f"""
                (() => {{
                    const allInputs = Array.from(document.querySelectorAll('input'));
                    const visibleInputs = allInputs.filter(input => {{
                        const rect = input.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    }});
                    
                    const usernameField = visibleInputs.find(input => 
                        input.type === 'text' || input.type === 'email' || 
                        input.placeholder?.toLowerCase().includes('username') ||
                        input.placeholder?.toLowerCase().includes('email')
                    );
                    
                    const passwordField = visibleInputs.find(input => 
                        input.type === 'password'
                    );
                    
                    if (usernameField && passwordField) {{
                        // Fill username
                        usernameField.value = '{TEST_USERNAME}';
                        usernameField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        usernameField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        usernameField.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        
                        // Fill password
                        passwordField.value = '{TEST_PASSWORD}';
                        passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        passwordField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        passwordField.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        
                        return {{
                            success: true,
                            method: 'direct',
                            username: usernameField.value,
                            passwordLength: passwordField.value.length
                        }};
                    }}
                    
                    return {{ success: false, reason: 'Could not find username and password fields' }};
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
        
        print("\n4. Verifying form is filled...")
        verify_result = await client.evaluate("""
            (() => {
                // Check direct inputs first
                const inputs = Array.from(document.querySelectorAll('input'));
                const filledInputs = inputs.filter(input => input.value.length > 0);
                
                // Check for Sign In button
                const buttons = Array.from(document.querySelectorAll('button'));
                const signInButton = buttons.find(btn => 
                    btn.textContent.toLowerCase().includes('sign in') ||
                    btn.textContent.toLowerCase().includes('login')
                );
                
                // Also check in iframes
                let iframeInputs = 0;
                let iframeButton = null;
                const iframes = Array.from(document.querySelectorAll('iframe'));
                for (const iframe of iframes) {
                    try {
                        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                        const iframeInputsFilled = Array.from(iframeDoc.querySelectorAll('input'))
                            .filter(input => input.value.length > 0);
                        if (iframeInputsFilled.length > iframeInputs) {
                            iframeInputs = iframeInputsFilled.length;
                        }
                        
                        const iframeButtons = Array.from(iframeDoc.querySelectorAll('button'));
                        const iframeSignIn = iframeButtons.find(btn => 
                            btn.textContent.toLowerCase().includes('sign in') ||
                            btn.textContent.toLowerCase().includes('login')
                        );
                        if (iframeSignIn) {
                            iframeButton = {
                                exists: true,
                                disabled: iframeSignIn.disabled,
                                text: iframeSignIn.textContent
                            };
                        }
                    } catch (e) {
                        // Ignore cross-origin errors
                    }
                }
                
                return {
                    directInputsFilled: filledInputs.length,
                    iframeInputsFilled: iframeInputs,
                    signInButton: signInButton ? {
                        exists: true,
                        disabled: signInButton.disabled,
                        text: signInButton.textContent
                    } : iframeButton || { exists: false }
                };
            })()
        """)
        
        print(f"   🔍 Verification:")
        print(f"      Direct inputs filled: {verify_result['directInputsFilled']}")
        print(f"      Iframe inputs filled: {verify_result['iframeInputsFilled']}")
        print(f"      Sign In button: {verify_result['signInButton']}")
        
        # Update session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 3)
        
        # Determine success
        fields_filled = (verify_result['directInputsFilled'] >= 2 or 
                        verify_result['iframeInputsFilled'] >= 2)
        button_ready = (verify_result['signInButton']['exists'] and 
                       not verify_result['signInButton'].get('disabled', True))
        
        success = fields_filled and button_ready
        
        print_step_result(
            success,
            "Form filled and ready to submit" if success else "Form not properly filled"
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