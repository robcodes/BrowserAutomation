#!/usr/bin/env python3
"""
Test logging into FuzzyCode with provided credentials
"""
import asyncio
from browser_client_enhanced import EnhancedBrowserClient
from datetime import datetime

async def test_fuzzycode_login():
    """Test login and code generation with authenticated user"""
    print("=== Testing FuzzyCode Login ===\n")
    
    client = EnhancedBrowserClient()
    
    try:
        # Create session (visible browser for debugging)
        session_id = await client.create_session(headless=False)
        print(f"✓ Created session: {session_id}")
        
        # Navigate to fuzzycode
        page_id = await client.new_page("https://fuzzycode.dev")
        print(f"✓ Created page: {page_id}")
        
        # Wait for initial load
        await client.wait(3000)
        
        # Take initial screenshot
        await client.screenshot("fuzzycode_login_1_initial.png")
        
        # Check for any login button or link
        print("\n→ Looking for login elements...")
        
        # Try to find login-related elements
        login_elements = await client.evaluate("""
            () => {
                const elements = [];
                // Check for login buttons
                document.querySelectorAll('button, a').forEach(el => {
                    const text = el.textContent.toLowerCase();
                    if (text.includes('login') || text.includes('sign in') || text.includes('log in')) {
                        elements.push({
                            tag: el.tagName,
                            text: el.textContent.trim(),
                            href: el.href || '',
                            visible: el.offsetParent !== null
                        });
                    }
                });
                // Check for user/account elements
                document.querySelectorAll('[class*="user"], [class*="account"], [class*="auth"]').forEach(el => {
                    if (el.textContent.trim()) {
                        elements.push({
                            tag: el.tagName,
                            text: el.textContent.trim().substring(0, 50),
                            class: el.className,
                            visible: el.offsetParent !== null
                        });
                    }
                });
                return elements;
            }
        """)
        
        print(f"\nFound {len(login_elements)} login-related elements:")
        for elem in login_elements:
            if elem.get('visible'):
                print(f"  - {elem['tag']}: '{elem['text']}'")
        
        # Check current authentication state
        auth_state = await client.get_console_logs(text_contains="auth")
        print(f"\n📋 Auth-related console logs: {len(auth_state['logs'])}")
        
        # Look for a login button or link
        login_clicked = False
        for selector in ['button:has-text("Login")', 'a:has-text("Login")', 
                        'button:has-text("Sign in")', 'a:has-text("Sign in")',
                        '[class*="login"]', '[class*="signin"]']:
            try:
                # Check if element exists and is visible
                exists = await client.evaluate(f"""
                    () => {{
                        const el = document.querySelector('{selector}');
                        return el && el.offsetParent !== null;
                    }}
                """)
                
                if exists:
                    print(f"\n→ Clicking login element: {selector}")
                    await client.click(selector)
                    login_clicked = True
                    await client.wait(2000)
                    await client.screenshot("fuzzycode_login_2_after_login_click.png")
                    break
            except:
                continue
        
        if not login_clicked:
            print("\n⚠️  No login button found. Checking if already on login page or logged in...")
            
            # Check URL
            current_url = await client.evaluate("() => window.location.href")
            print(f"Current URL: {current_url}")
            
            # Check for username display
            username_display = await client.evaluate("""
                () => {
                    const texts = [];
                    document.querySelectorAll('*').forEach(el => {
                        if (el.textContent.includes('anonymous_user') || 
                            el.textContent.includes('@gmail.com')) {
                            texts.push(el.textContent.trim().substring(0, 100));
                        }
                    });
                    return texts.slice(0, 3);
                }
            """)
            
            if username_display:
                print("\nFound user references:")
                for text in username_display:
                    print(f"  - {text}")
        
        # Look for email/password fields
        print("\n→ Looking for login form fields...")
        
        form_fields = await client.evaluate("""
            () => {
                const fields = [];
                document.querySelectorAll('input').forEach(input => {
                    fields.push({
                        type: input.type,
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder,
                        visible: input.offsetParent !== null
                    });
                });
                return fields;
            }
        """)
        
        print(f"\nFound {len(form_fields)} input fields:")
        for field in form_fields:
            if field.get('visible'):
                print(f"  - type={field['type']}, name={field['name']}, placeholder={field['placeholder']}")
        
        # Try to fill login form if we find email/password fields
        email_filled = False
        password_filled = False
        
        # Try email field
        for selector in ['input[type="email"]', 'input[name="email"]', 'input[id="email"]',
                        'input[placeholder*="email"]', 'input[type="text"]']:
            try:
                if await client.evaluate(f"() => document.querySelector('{selector}') !== null"):
                    print(f"\n→ Filling email field: {selector}")
                    await client.fill(selector, "robert.norbeau+test2@gmail.com")
                    email_filled = True
                    break
            except:
                continue
        
        # Try password field
        for selector in ['input[type="password"]', 'input[name="password"]', 'input[id="password"]']:
            try:
                if await client.evaluate(f"() => document.querySelector('{selector}') !== null"):
                    print(f"→ Filling password field: {selector}")
                    await client.fill(selector, "robert.norbeau+test2")
                    password_filled = True
                    break
            except:
                continue
        
        if email_filled and password_filled:
            await client.screenshot("fuzzycode_login_3_form_filled.png")
            
            # Look for submit button
            print("\n→ Looking for submit button...")
            for selector in ['button[type="submit"]', 'button:has-text("Login")', 
                           'button:has-text("Sign in")', 'input[type="submit"]']:
                try:
                    if await client.evaluate(f"() => document.querySelector('{selector}') !== null"):
                        print(f"→ Clicking submit: {selector}")
                        await client.click(selector)
                        await client.wait(3000)
                        await client.screenshot("fuzzycode_login_4_after_submit.png")
                        break
                except:
                    continue
        
        # Check console for any errors during login
        await client.print_recent_errors()
        
        # Check if login was successful
        print("\n→ Checking authentication state after login attempt...")
        
        # Get all console logs to see auth state
        all_logs = await client.get_console_logs()
        auth_logs = [log for log in all_logs['logs'] if 'auth' in log['text'].lower() or 'user' in log['text'].lower()]
        
        if auth_logs:
            print(f"\n📋 Recent auth-related logs:")
            for log in auth_logs[-5:]:  # Last 5
                print(f"  [{log['type']}] {log['text'][:100]}...")
        
        # Save session for manual inspection
        with open("fuzzycode_login_session.json", "w") as f:
            import json
            json.dump({
                "session_id": session_id,
                "page_id": page_id,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n💾 Session saved: {session_id}")
        print("\nPlease check the screenshots to see the current state.")
        print("The browser window is still open for manual inspection.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to get error details
        try:
            await client.print_recent_errors()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(test_fuzzycode_login())