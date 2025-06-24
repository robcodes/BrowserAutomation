#!/usr/bin/env python3
"""
Check for login form and fill it
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def check_and_fill_login():
    """Check for login form and fill it"""
    print("=== Checking for Login Form ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Take screenshot
    await client.screenshot("fuzzycode_login_open.png")
    print("✓ Screenshot taken")
    
    # Check for visible iframes and login elements
    login_check = await client.evaluate("""
        () => {
            // Check all iframes
            const iframes = Array.from(document.querySelectorAll('iframe'));
            const visibleIframes = iframes.filter(iframe => {
                const box = iframe.getBoundingClientRect();
                const styles = window.getComputedStyle(iframe);
                return iframe.offsetParent !== null && 
                       box.width > 100 && box.height > 100 &&
                       styles.display !== 'none' &&
                       styles.visibility !== 'hidden' &&
                       styles.opacity !== '0';
            });
            
            // Check for login form elements in main document
            const emailInput = document.querySelector('input[type="email"], input[name="email"], input[placeholder*="email" i]');
            const passwordInput = document.querySelector('input[type="password"], input[name="password"], input[placeholder*="password" i]');
            const submitButton = document.querySelector('button[type="submit"], input[type="submit"], button:contains("Login"), button:contains("Sign")') ||
                               Array.from(document.querySelectorAll('button')).find(btn => 
                                   /login|sign\s*in/i.test(btn.textContent));
            
            // Check for any modal/popup containers
            const modals = document.querySelectorAll('.modal, [role="dialog"], .popup, [class*="modal"], [class*="popup"], .overlay');
            const visibleModals = Array.from(modals).filter(m => {
                const box = m.getBoundingClientRect();
                const styles = window.getComputedStyle(m);
                return m.offsetParent !== null && box.width > 100 && box.height > 100;
            });
            
            return {
                visibleIframes: visibleIframes.map(iframe => ({
                    src: iframe.src,
                    id: iframe.id,
                    class: iframe.className,
                    position: {
                        x: iframe.getBoundingClientRect().left,
                        y: iframe.getBoundingClientRect().top,
                        width: iframe.getBoundingClientRect().width,
                        height: iframe.getBoundingClientRect().height
                    }
                })),
                loginFormInMainDoc: {
                    hasEmail: emailInput !== null,
                    hasPassword: passwordInput !== null,
                    hasSubmit: submitButton !== null
                },
                visibleModals: visibleModals.length
            };
        }
    """)
    
    print(f"\nLogin form check:")
    print(f"  Visible iframes: {len(login_check['visibleIframes'])}")
    print(f"  Visible modals: {login_check['visibleModals']}")
    print(f"  Login form in main document: {login_check['loginFormInMainDoc']}")
    
    if login_check['visibleIframes']:
        print("\nVisible iframes:")
        for iframe in login_check['visibleIframes']:
            print(f"  - {iframe['src'][:60]}...")
            print(f"    Position: ({iframe['position']['x']}, {iframe['position']['y']})")
            print(f"    Size: {iframe['position']['width']}x{iframe['position']['height']}")
    
    # If login form is in main document, fill it
    if login_check['loginFormInMainDoc']['hasEmail'] and login_check['loginFormInMainDoc']['hasPassword']:
        print("\n✓ Found login form in main document! Filling...")
        
        fill_result = await client.evaluate("""
            () => {
                const results = { emailFilled: false, passwordFilled: false };
                
                // Fill email
                const emailInput = document.querySelector('input[type="email"], input[name="email"], input[placeholder*="email" i]');
                if (emailInput) {
                    emailInput.value = 'robert.norbeau+test2@gmail.com';
                    emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                    emailInput.dispatchEvent(new Event('change', { bubbles: true }));
                    results.emailFilled = true;
                }
                
                // Fill password
                const passwordInput = document.querySelector('input[type="password"], input[name="password"], input[placeholder*="password" i]');
                if (passwordInput) {
                    passwordInput.value = 'robert.norbeau+test2';
                    passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                    passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                    results.passwordFilled = true;
                }
                
                return results;
            }
        """)
        
        print(f"Fill result: {fill_result}")
        
        if fill_result['emailFilled'] and fill_result['passwordFilled']:
            await client.wait(1000)
            await client.screenshot("fuzzycode_login_filled.png")
            
            # Click submit
            print("\n→ Clicking submit button...")
            submit_result = await client.evaluate("""
                () => {
                    const submitButton = document.querySelector('button[type="submit"], input[type="submit"]') ||
                                       Array.from(document.querySelectorAll('button')).find(btn => 
                                           /login|sign\s*in/i.test(btn.textContent));
                    
                    if (submitButton) {
                        submitButton.click();
                        return { success: true, buttonText: submitButton.textContent };
                    }
                    return { success: false };
                }
            """)
            
            print(f"Submit result: {submit_result}")
            
            if submit_result['success']:
                await client.wait(3000)
                await client.screenshot("fuzzycode_after_login.png")
                print("\n✓ Login form submitted!")
    
    # If login is in an iframe, we need to handle it differently
    elif login_check['visibleIframes']:
        for i, iframe in enumerate(login_check['visibleIframes']):
            if 'login' in iframe['src'].lower():
                print(f"\n→ Found login iframe: {iframe['src'][:60]}...")
                print("\n⚠️  Login form is in a cross-origin iframe.")
                print("Due to browser security, I cannot automatically fill it.")
                print("\nPlease manually enter:")
                print("  Email: robert.norbeau+test2@gmail.com")
                print("  Password: robert.norbeau+test2")
                break
    
    # Check console for auth events
    auth_logs = await client.get_console_logs(text_contains="auth", limit=5)
    if auth_logs["logs"]:
        print("\n📋 Recent auth logs:")
        for log in auth_logs["logs"]:
            print(f"  [{log['type']}] {log['text'][:80]}...")

if __name__ == "__main__":
    asyncio.run(check_and_fill_login())