#!/usr/bin/env python3
"""
Test login with provided credentials
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def test_login():
    """Test login functionality"""
    print("=== Testing Login ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Step 23: Fill login form
    print("\n→ Step 23: Filling login form...")
    
    # Analyze the form structure first
    form_analysis = await client.evaluate("""
        () => {
            // Look for input fields in the modal
            const inputs = Array.from(document.querySelectorAll('input'));
            const visibleInputs = inputs.filter(i => i.offsetParent !== null);
            
            return visibleInputs.map(input => ({
                type: input.type,
                name: input.name,
                id: input.id,
                placeholder: input.placeholder,
                required: input.required,
                value: input.value,
                rect: {
                    top: Math.round(input.getBoundingClientRect().top),
                    left: Math.round(input.getBoundingClientRect().left)
                }
            }));
        }
    """)
    
    print("  Found input fields:")
    for inp in form_analysis:
        print(f"    - {inp['type']}: '{inp['placeholder']}' at ({inp['rect']['left']}, {inp['rect']['top']})")
    
    # Fill the form
    fill_result = await client.evaluate("""
        () => {
            // Find username/email field
            const usernameField = document.querySelector('input[type="text"], input[type="email"]');
            const passwordField = document.querySelector('input[type="password"]');
            
            if (usernameField && passwordField) {
                // Clear and fill username
                usernameField.focus();
                usernameField.value = '';
                usernameField.value = 'robert.norbeau+test2@gmail.com';
                usernameField.dispatchEvent(new Event('input', { bubbles: true }));
                usernameField.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Clear and fill password
                passwordField.focus();
                passwordField.value = '';
                passwordField.value = 'robert.norbeau+test2';
                passwordField.dispatchEvent(new Event('input', { bubbles: true }));
                passwordField.dispatchEvent(new Event('change', { bubbles: true }));
                
                return {
                    success: true,
                    usernameValue: usernameField.value,
                    passwordFilled: passwordField.value.length > 0
                };
            }
            
            return { success: false, message: 'Could not find input fields' };
        }
    """)
    
    print(f"\n  Fill result: {fill_result}")
    
    if fill_result['success']:
        await client.wait(500)
        await client.screenshot("fuzzy_explore_11_login_filled.png")
        print("  ✓ Screenshot: fuzzy_explore_11_login_filled.png")
        
        # Step 24: Check button state and submit
        print("\n→ Step 24: Checking Sign In button...")
        
        button_check = await client.evaluate("""
            () => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const signInButton = buttons.find(btn => 
                    btn.textContent.includes('Sign In') && 
                    btn.offsetParent !== null
                );
                
                if (signInButton) {
                    return {
                        found: true,
                        disabled: signInButton.disabled,
                        text: signInButton.textContent.trim(),
                        rect: {
                            top: Math.round(signInButton.getBoundingClientRect().top),
                            left: Math.round(signInButton.getBoundingClientRect().left)
                        }
                    };
                }
                
                return { found: false };
            }
        """)
        
        print(f"  Sign In button: {button_check}")
        
        if button_check['found'] and not button_check['disabled']:
            print("\n  → Clicking Sign In button...")
            
            submit_result = await client.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const signInButton = buttons.find(btn => 
                        btn.textContent.includes('Sign In') && 
                        btn.offsetParent !== null
                    );
                    
                    if (signInButton && !signInButton.disabled) {
                        signInButton.click();
                        return { success: true };
                    }
                    
                    return { success: false };
                }
            """)
            
            if submit_result['success']:
                print("  ✓ Clicked Sign In button")
                
                # Wait for login to process
                await client.wait(3000)
                await client.screenshot("fuzzy_explore_12_after_login.png")
                print("  ✓ Screenshot: fuzzy_explore_12_after_login.png")
                
                # Check login result
                login_status = await client.evaluate("""
                    () => {
                        // Check if modal is still visible
                        const modal = document.querySelector('.modal, [role="dialog"]');
                        const modalVisible = modal ? modal.offsetParent !== null : false;
                        
                        // Look for success indicators
                        const pageText = document.body.textContent;
                        const hasUserEmail = pageText.includes('robert.norbeau');
                        
                        // Check for error messages
                        const errorElements = Array.from(document.querySelectorAll('.error, .alert, [class*="error"]'));
                        const visibleErrors = errorElements.filter(e => e.offsetParent !== null);
                        
                        return {
                            modalStillVisible: modalVisible,
                            hasUserEmail: hasUserEmail,
                            errorCount: visibleErrors.length,
                            errorMessages: visibleErrors.map(e => e.textContent.trim()).slice(0, 3)
                        };
                    }
                """)
                
                print("\n  Login status:")
                print(f"    Modal still visible: {login_status['modalStillVisible']}")
                print(f"    User email in page: {login_status['hasUserEmail']}")
                print(f"    Errors: {login_status['errorCount']}")
                if login_status['errorMessages']:
                    for err in login_status['errorMessages']:
                        print(f"      - {err}")

if __name__ == "__main__":
    asyncio.run(test_login())