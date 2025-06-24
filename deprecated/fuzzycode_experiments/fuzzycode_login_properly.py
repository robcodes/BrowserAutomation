#!/usr/bin/env python3
"""
Login properly with sanity checks
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def login_properly():
    """Login with proper checks like a real user"""
    print("=== Logging In Properly ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # First, take a screenshot to see current state
    await client.screenshot("login_1_current_state.png")
    print("✓ Screenshot 1: Current state")
    
    # Check if login form is visible
    login_check = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            if (!loginIframe) return { hasLoginForm: false };
            
            try {
                const iframeDoc = loginIframe.contentDocument;
                const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                                 iframeDoc.querySelector('input[type="text"]');
                const passwordInput = iframeDoc.querySelector('input[type="password"]');
                const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                                   Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                       btn.textContent.includes('Sign'));
                
                return {
                    hasLoginForm: true,
                    hasEmailField: emailInput !== null,
                    hasPasswordField: passwordInput !== null,
                    hasSubmitButton: submitButton !== null,
                    submitButtonText: submitButton ? submitButton.textContent : null
                };
            } catch (e) {
                return { hasLoginForm: false, error: e.message };
            }
        }
    """)
    
    if not login_check['hasLoginForm']:
        print("❌ No login form found. Stopping.")
        return
    
    print(f"\n✓ Login form found:")
    print(f"  Email field: {login_check['hasEmailField']}")
    print(f"  Password field: {login_check['hasPasswordField']}")
    print(f"  Submit button: {login_check['hasSubmitButton']} ('{login_check['submitButtonText']}')")
    
    # Fill email field
    print("\n→ Filling email field...")
    email_result = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            const iframeDoc = loginIframe.contentDocument;
            const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                             iframeDoc.querySelector('input[type="text"]');
            
            if (emailInput) {
                emailInput.focus();
                emailInput.value = '';  // Clear first
                emailInput.value = 'robert.norbeau+test2@gmail.com';
                emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                emailInput.dispatchEvent(new Event('change', { bubbles: true }));
                return { success: true, value: emailInput.value };
            }
            return { success: false };
        }
    """)
    
    if not email_result['success']:
        print("❌ Failed to fill email. Stopping.")
        return
    
    print(f"✓ Email filled: {email_result['value']}")
    
    # Take screenshot after email
    await client.wait(500)
    await client.screenshot("login_2_email_filled.png")
    print("✓ Screenshot 2: After filling email")
    
    # Fill password field
    print("\n→ Filling password field...")
    password_result = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            const iframeDoc = loginIframe.contentDocument;
            const passwordInput = iframeDoc.querySelector('input[type="password"]');
            
            if (passwordInput) {
                passwordInput.focus();
                passwordInput.value = '';  // Clear first
                passwordInput.value = 'robert.norbeau+test2';
                passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                return { success: true, filled: passwordInput.value.length > 0 };
            }
            return { success: false };
        }
    """)
    
    if not password_result['success']:
        print("❌ Failed to fill password. Stopping.")
        return
    
    print(f"✓ Password filled: {password_result['filled']}")
    
    # Take screenshot after password
    await client.wait(500)
    await client.screenshot("login_3_both_filled.png")
    print("✓ Screenshot 3: After filling both fields")
    
    # Verify both fields are filled and button is enabled
    print("\n→ Verifying form is ready...")
    verify_result = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            const iframeDoc = loginIframe.contentDocument;
            const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                             iframeDoc.querySelector('input[type="text"]');
            const passwordInput = iframeDoc.querySelector('input[type="password"]');
            const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                               Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                   btn.textContent.includes('Sign'));
            
            return {
                emailValue: emailInput ? emailInput.value : '',
                passwordFilled: passwordInput ? passwordInput.value.length > 0 : false,
                buttonEnabled: submitButton ? !submitButton.disabled : false,
                buttonText: submitButton ? submitButton.textContent : ''
            };
        }
    """)
    
    print(f"\nForm verification:")
    print(f"  Email value: {verify_result['emailValue']}")
    print(f"  Password filled: {verify_result['passwordFilled']}")
    print(f"  Button enabled: {verify_result['buttonEnabled']}")
    print(f"  Button text: '{verify_result['buttonText']}'")
    
    if not verify_result['emailValue'] or not verify_result['passwordFilled']:
        print("\n❌ Form not properly filled. Stopping.")
        return
    
    if not verify_result['buttonEnabled']:
        print("\n⚠️  Button is disabled. Waiting a moment...")
        await client.wait(2000)
    
    # Click submit button
    print("\n→ Clicking Sign In button...")
    submit_result = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            const iframeDoc = loginIframe.contentDocument;
            const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                               Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                   btn.textContent.includes('Sign'));
            
            if (submitButton && !submitButton.disabled) {
                submitButton.click();
                return { success: true, clicked: true };
            }
            return { success: false, disabled: submitButton ? submitButton.disabled : null };
        }
    """)
    
    if submit_result['success']:
        print("✓ Sign In button clicked!")
        await client.wait(1000)
        await client.screenshot("login_4_after_click.png")
        print("✓ Screenshot 4: After clicking Sign In")
    else:
        print(f"❌ Could not click button (disabled: {submit_result['disabled']})")

if __name__ == "__main__":
    asyncio.run(login_properly())