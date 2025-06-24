#!/usr/bin/env python3
"""
Fill the visible login form
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def fill_visible_login():
    """Fill the visible login form"""
    print("=== Filling Visible Login Form ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # The form has placeholder text, so let's search by that
    print("→ Filling username/email field...")
    
    email_filled = await client.evaluate("""
        () => {
            // Look for input with "Username or Email" placeholder
            const emailInput = document.querySelector('input[placeholder*="Username"]') ||
                             document.querySelector('input[placeholder*="Email"]') ||
                             document.querySelector('input[type="text"]:not([type="password"])') ||
                             document.querySelector('input[name="email"]') ||
                             document.querySelector('input[name="username"]');
            
            if (emailInput) {
                emailInput.focus();
                emailInput.click();
                emailInput.value = 'robert.norbeau+test2@gmail.com';
                emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                emailInput.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }
            return false;
        }
    """)
    
    print(f"  Email filled: {email_filled}")
    
    await client.wait(500)
    
    # Fill password
    print("→ Filling password field...")
    
    password_filled = await client.evaluate("""
        () => {
            const passwordInput = document.querySelector('input[placeholder*="Password"]') ||
                                document.querySelector('input[type="password"]');
            
            if (passwordInput) {
                passwordInput.focus();
                passwordInput.click();
                passwordInput.value = 'robert.norbeau+test2';
                passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }
            return false;
        }
    """)
    
    print(f"  Password filled: {password_filled}")
    
    if email_filled and password_filled:
        await client.wait(1000)
        await client.screenshot("fuzzycode_login_filled_visible.png")
        print("✓ Screenshot taken after filling")
        
        # Click the Sign In button
        print("\n→ Clicking Sign In button...")
        
        sign_in_clicked = await client.evaluate("""
            () => {
                // Look for the Sign In button
                const buttons = Array.from(document.querySelectorAll('button'));
                const signInButton = buttons.find(btn => {
                    const text = btn.textContent.trim().toLowerCase();
                    return text === 'sign in' || text === 'login';
                });
                
                if (signInButton) {
                    signInButton.click();
                    return { clicked: true, text: signInButton.textContent };
                }
                
                // Try any button in the modal
                const modalButtons = document.querySelectorAll('.modal button, [role="dialog"] button');
                if (modalButtons.length > 0) {
                    modalButtons[0].click();
                    return { clicked: true, text: modalButtons[0].textContent };
                }
                
                return { clicked: false };
            }
        """)
        
        print(f"  Sign In clicked: {sign_in_clicked}")
        
        if sign_in_clicked['clicked']:
            print("\n✓ Login submitted! Waiting for response...")
            await client.wait(3000)
            
            # Take screenshot after login
            await client.screenshot("fuzzycode_after_login_submit.png")
            
            # Check if login was successful
            login_status = await client.evaluate("""
                () => {
                    // Check if modal is still visible
                    const modal = document.querySelector('.modal, [role="dialog"]');
                    const modalVisible = modal ? modal.offsetParent !== null : false;
                    
                    // Check for any error messages
                    const errorElements = Array.from(document.querySelectorAll('*')).filter(el => {
                        const text = el.textContent.toLowerCase();
                        return text.includes('error') || text.includes('invalid') || text.includes('incorrect');
                    });
                    
                    // Check current URL
                    const url = window.location.href;
                    
                    return {
                        modalStillVisible: modalVisible,
                        hasErrors: errorElements.length > 0,
                        currentUrl: url
                    };
                }
            """)
            
            print(f"\nLogin status:")
            print(f"  Modal still visible: {login_status['modalStillVisible']}")
            print(f"  Has error messages: {login_status['hasErrors']}")
            print(f"  Current URL: {login_status['currentUrl']}")
            
            # Check console for auth messages
            auth_logs = await client.get_console_logs(text_contains="auth", limit=5)
            if auth_logs["logs"]:
                print("\n📋 Recent auth logs:")
                for log in auth_logs["logs"]:
                    print(f"  [{log['type']}] {log['text'][:80]}...")
    
    else:
        print("\n⚠️  Could not fill login form")

if __name__ == "__main__":
    asyncio.run(fill_visible_login())