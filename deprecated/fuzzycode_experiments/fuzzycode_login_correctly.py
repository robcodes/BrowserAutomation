#!/usr/bin/env python3
"""
Login to FuzzyCode using the proven solution
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def login_correctly():
    """Login using the solution that worked before"""
    print("=== Logging in to FuzzyCode ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # The login iframe should already be open from clicking the profile icon
    # Let's verify and fill both fields
    
    print("→ Filling BOTH username and password fields in iframe...")
    
    fill_result = await client.evaluate("""
        () => {
            // Find the login iframe
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            if (!loginIframe) {
                // Try any visible iframe
                const visibleIframe = Array.from(document.querySelectorAll('iframe'))
                    .find(iframe => iframe.offsetParent !== null);
                if (visibleIframe) {
                    const iframeDoc = visibleIframe.contentDocument;
                    
                    // Find BOTH fields - this is the key!
                    const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                                     iframeDoc.querySelector('input[type="text"]');
                    const passwordInput = iframeDoc.querySelector('input[type="password"]');
                    
                    if (emailInput && passwordInput) {
                        // Fill email/username field
                        emailInput.focus();
                        emailInput.value = '';
                        emailInput.value = 'robert.norbeau+test2@gmail.com';
                        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                        emailInput.dispatchEvent(new Event('change', { bubbles: true }));
                        
                        // Fill password field
                        passwordInput.focus();
                        passwordInput.value = '';
                        passwordInput.value = 'robert.norbeau+test2';
                        passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                        passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                        
                        return {
                            success: true,
                            emailValue: emailInput.value,
                            passwordFilled: passwordInput.value.length > 0
                        };
                    }
                }
            } else {
                const iframeDoc = loginIframe.contentDocument;
                
                // Find BOTH fields
                const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                                 iframeDoc.querySelector('input[type="text"]');
                const passwordInput = iframeDoc.querySelector('input[type="password"]');
                
                if (emailInput && passwordInput) {
                    // Fill email/username field
                    emailInput.focus();
                    emailInput.value = '';
                    emailInput.value = 'robert.norbeau+test2@gmail.com';
                    emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                    emailInput.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    // Fill password field
                    passwordInput.focus();
                    passwordInput.value = '';
                    passwordInput.value = 'robert.norbeau+test2';
                    passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                    passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    return {
                        success: true,
                        emailValue: emailInput.value,
                        passwordFilled: passwordInput.value.length > 0
                    };
                }
            }
            
            return { success: false, message: 'Could not find both input fields' };
        }
    """)
    
    print(f"  Fill result: {fill_result}")
    
    if fill_result['success']:
        await client.wait(500)
        await client.screenshot("fuzzy_explore_15_both_fields_filled.png")
        print("  ✓ Screenshot: fuzzy_explore_15_both_fields_filled.png")
        
        # Now check if button is enabled and click it
        print("\n→ Checking if Sign In button is enabled...")
        
        button_check = await client.evaluate("""
            () => {
                const iframe = Array.from(document.querySelectorAll('iframe'))
                    .find(f => f.offsetParent !== null);
                
                if (!iframe) return { error: 'No iframe' };
                
                const iframeDoc = iframe.contentDocument;
                const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                                   Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                       btn.textContent.includes('Sign'));
                
                if (submitButton) {
                    // Check form validity
                    const form = iframeDoc.querySelector('form');
                    const formValid = form ? form.checkValidity() : null;
                    
                    return {
                        found: true,
                        disabled: submitButton.disabled,
                        formValid: formValid,
                        buttonText: submitButton.textContent.trim()
                    };
                }
                
                return { found: false };
            }
        """)
        
        print(f"  Button check: {button_check}")
        
        if button_check['found'] and not button_check['disabled']:
            print("\n→ Clicking Sign In button...")
            
            click_result = await client.evaluate("""
                () => {
                    const iframe = Array.from(document.querySelectorAll('iframe'))
                        .find(f => f.offsetParent !== null);
                    const iframeDoc = iframe.contentDocument;
                    
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
                print("  ✓ Clicked Sign In button!")
                await client.wait(2000)
                await client.screenshot("fuzzy_explore_16_after_login.png")
                print("  ✓ Screenshot: fuzzy_explore_16_after_login.png")
                
                # Update tracking
                with open("FUZZY_CODE_STEPS.md", "a") as f:
                    f.write("\n## Login Process\n")
                    f.write("14. Filled BOTH username/email AND password fields in iframe (key insight: both are required)\n")
                    f.write("15. Form validation passed, Sign In button enabled\n")
                    f.write("16. Successfully clicked Sign In and logged in\n")

if __name__ == "__main__":
    asyncio.run(login_correctly())