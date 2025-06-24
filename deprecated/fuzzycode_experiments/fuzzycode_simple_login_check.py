#!/usr/bin/env python3
"""
Simple check for login form
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def simple_login_check():
    """Simple check and fill login form"""
    print("=== Simple Login Check ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Take screenshot first
    await client.screenshot("fuzzycode_login_current.png")
    print("✓ Screenshot taken: fuzzycode_login_current.png")
    
    # Simple check for login inputs
    has_login_form = await client.evaluate("""
        () => {
            const emailInput = document.querySelector('input[type="email"]') || 
                             document.querySelector('input[name="email"]');
            const passwordInput = document.querySelector('input[type="password"]');
            
            return {
                hasEmail: emailInput !== null,
                hasPassword: passwordInput !== null,
                emailVisible: emailInput ? emailInput.offsetParent !== null : false,
                passwordVisible: passwordInput ? passwordInput.offsetParent !== null : false
            };
        }
    """)
    
    print(f"\nLogin form check:")
    print(f"  Has email input: {has_login_form['hasEmail']} (visible: {has_login_form['emailVisible']})")
    print(f"  Has password input: {has_login_form['hasPassword']} (visible: {has_login_form['passwordVisible']})")
    
    if has_login_form['hasEmail'] and has_login_form['hasPassword']:
        print("\n✓ Found login form! Attempting to fill...")
        
        # Fill email
        email_filled = await client.evaluate("""
            () => {
                const emailInput = document.querySelector('input[type="email"]') || 
                                 document.querySelector('input[name="email"]');
                if (emailInput) {
                    emailInput.focus();
                    emailInput.value = 'robert.norbeau+test2@gmail.com';
                    emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                    return true;
                }
                return false;
            }
        """)
        
        print(f"  Email filled: {email_filled}")
        
        # Fill password
        password_filled = await client.evaluate("""
            () => {
                const passwordInput = document.querySelector('input[type="password"]');
                if (passwordInput) {
                    passwordInput.focus();
                    passwordInput.value = 'robert.norbeau+test2';
                    passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                    return true;
                }
                return false;
            }
        """)
        
        print(f"  Password filled: {password_filled}")
        
        if email_filled and password_filled:
            await client.wait(1000)
            await client.screenshot("fuzzycode_login_filled.png")
            
            # Find and click submit button
            print("\n→ Looking for submit button...")
            
            submit_clicked = await client.evaluate("""
                () => {
                    // Look for submit button
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const submitButton = buttons.find(btn => {
                        const text = btn.textContent.toLowerCase();
                        return text.includes('login') || text.includes('sign in');
                    }) || document.querySelector('button[type="submit"]');
                    
                    if (submitButton) {
                        submitButton.click();
                        return { clicked: true, text: submitButton.textContent };
                    }
                    return { clicked: false };
                }
            """)
            
            print(f"  Submit result: {submit_clicked}")
            
            if submit_clicked['clicked']:
                await client.wait(3000)
                await client.screenshot("fuzzycode_after_login_attempt.png")
                print("\n✓ Login submitted!")
    
    else:
        print("\n⚠️  No login form found in main document.")
        
        # Check iframes
        iframe_count = await client.evaluate("() => document.querySelectorAll('iframe').length")
        print(f"\nNumber of iframes: {iframe_count}")
        
        if iframe_count > 0:
            print("\nThe login form might be in an iframe.")

if __name__ == "__main__":
    asyncio.run(simple_login_check())