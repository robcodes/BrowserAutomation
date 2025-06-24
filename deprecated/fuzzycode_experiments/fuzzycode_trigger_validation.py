#!/usr/bin/env python3
"""
Trigger form validation properly
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def trigger_validation():
    """Trigger form validation events"""
    print("=== Triggering Form Validation ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Try different approach - trigger all possible events
    print("→ Triggering validation events...")
    
    validation_result = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            if (!loginIframe) return { error: 'No login iframe' };
            
            const iframeDoc = loginIframe.contentDocument;
            const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                             iframeDoc.querySelector('input[type="text"]');
            const passwordInput = iframeDoc.querySelector('input[type="password"]');
            
            // Clear and refill with all events
            if (emailInput) {
                emailInput.focus();
                emailInput.select();
                emailInput.value = '';
                emailInput.value = 'robert.norbeau+test2@gmail.com';
                
                // Trigger all possible events
                ['input', 'change', 'keyup', 'keydown', 'blur'].forEach(eventType => {
                    emailInput.dispatchEvent(new Event(eventType, { bubbles: true }));
                });
            }
            
            if (passwordInput) {
                passwordInput.focus();
                passwordInput.select();
                passwordInput.value = '';
                passwordInput.value = 'robert.norbeau+test2';
                
                // Trigger all possible events
                ['input', 'change', 'keyup', 'keydown', 'blur'].forEach(eventType => {
                    passwordInput.dispatchEvent(new Event(eventType, { bubbles: true }));
                });
            }
            
            // Check button state after a moment
            return new Promise(resolve => {
                setTimeout(() => {
                    const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                                       Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                           btn.textContent.includes('Sign'));
                    
                    resolve({
                        emailValue: emailInput ? emailInput.value : '',
                        passwordLength: passwordInput ? passwordInput.value.length : 0,
                        buttonEnabled: submitButton ? !submitButton.disabled : false,
                        buttonClasses: submitButton ? submitButton.className : '',
                        formValid: iframeDoc.querySelector('form') ? 
                                  iframeDoc.querySelector('form').checkValidity() : null
                    });
                }, 1000);
            });
        }
    """)
    
    print(f"\nValidation result:")
    print(f"  Email: {validation_result['emailValue']}")
    print(f"  Password length: {validation_result['passwordLength']}")
    print(f"  Button enabled: {validation_result['buttonEnabled']}")
    print(f"  Form valid: {validation_result['formValid']}")
    
    await client.screenshot("login_5_after_validation.png")
    
    if validation_result['buttonEnabled']:
        print("\n✓ Button is now enabled! Clicking...")
        
        click_result = await client.evaluate("""
            () => {
                const loginIframe = Array.from(document.querySelectorAll('iframe'))
                    .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
                
                const iframeDoc = loginIframe.contentDocument;
                const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                                   Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                       btn.textContent.includes('Sign'));
                
                if (submitButton && !submitButton.disabled) {
                    submitButton.click();
                    return { success: true };
                }
                return { success: false };
            }
        """)
        
        if click_result['success']:
            print("✓ Clicked Sign In!")
            await client.wait(3000)
            await client.screenshot("login_6_after_submit.png")
    else:
        print("\n❌ Button still disabled. There might be additional validation requirements.")

if __name__ == "__main__":
    asyncio.run(trigger_validation())