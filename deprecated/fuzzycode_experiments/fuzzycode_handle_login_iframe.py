#!/usr/bin/env python3
"""
Handle the login iframe that appeared
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def handle_login_iframe():
    """Find and fill the login iframe"""
    print("=== Handling Login Iframe ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Find visible iframes
    print("\n→ Looking for visible iframes...")
    
    iframe_info = await client.evaluate("""
        () => {
            const iframes = Array.from(document.querySelectorAll('iframe'));
            const results = [];
            
            iframes.forEach((iframe, index) => {
                const box = iframe.getBoundingClientRect();
                const styles = window.getComputedStyle(iframe);
                const visible = iframe.offsetParent !== null && 
                               box.width > 0 && box.height > 0 &&
                               styles.display !== 'none' &&
                               styles.visibility !== 'hidden';
                
                results.push({
                    index: index,
                    src: iframe.src,
                    id: iframe.id,
                    class: iframe.className,
                    visible: visible,
                    position: {
                        x: box.left,
                        y: box.top,
                        width: box.width,
                        height: box.height
                    },
                    styles: {
                        display: styles.display,
                        visibility: styles.visibility,
                        opacity: styles.opacity,
                        zIndex: styles.zIndex
                    }
                });
            });
            
            return results;
        }
    """)
    
    print(f"Found {len(iframe_info)} iframes:\n")
    
    visible_iframes = [iframe for iframe in iframe_info if iframe['visible']]
    
    for iframe in iframe_info:
        print(f"Iframe #{iframe['index']}:")
        print(f"  Src: {iframe['src'][:60]}...")
        print(f"  Visible: {iframe['visible']}")
        if iframe['visible']:
            print(f"  Position: ({iframe['position']['x']}, {iframe['position']['y']})")
            print(f"  Size: {iframe['position']['width']}x{iframe['position']['height']}")
        print()
    
    if visible_iframes:
        # Try to interact with the visible iframe
        target_iframe = visible_iframes[0]
        print(f"→ Attempting to fill login form in iframe #{target_iframe['index']}...")
        
        # Since we can't directly access cross-origin iframes, let's try to:
        # 1. Check if it's same-origin
        # 2. If not, we'll have to work around it
        
        can_access = await client.evaluate(f"""
            () => {{
                const iframe = document.querySelectorAll('iframe')[{target_iframe['index']}];
                try {{
                    // Try to access iframe document
                    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                    return {{ canAccess: true, url: iframe.src }};
                }} catch (e) {{
                    return {{ canAccess: false, error: e.message, url: iframe.src }};
                }}
            }}
        """)
        
        print(f"Can access iframe: {can_access['canAccess']}")
        
        if not can_access['canAccess']:
            print(f"⚠️  Cannot access iframe directly (cross-origin)")
            print(f"  URL: {can_access['url']}")
            
            # Let's try to at least make the iframe more visible
            print("\n→ Checking if login form is visible in current viewport...")
            
            # Take a screenshot to see current state
            await client.screenshot("fuzzycode_login_iframe_visible.png")
            
            # Try scrolling or focusing on the iframe
            await client.evaluate(f"""
                () => {{
                    const iframe = document.querySelectorAll('iframe')[{target_iframe['index']}];
                    iframe.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    iframe.focus();
                }}
            """)
            
            print("\n⚠️  Due to browser security, I cannot automatically fill cross-origin iframes.")
            print("The login form should be visible now. You'll need to manually:")
            print("1. Enter email: robert.norbeau+test2@gmail.com")
            print("2. Enter password: robert.norbeau+test2")
            print("3. Click the login/submit button")
            
        else:
            # We can access the iframe, so let's fill it
            print("✓ Can access iframe content! Attempting to fill form...")
            
            fill_result = await client.evaluate(f"""
                () => {{
                    const iframe = document.querySelectorAll('iframe')[{target_iframe['index']}];
                    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                    
                    // Look for email and password fields
                    const emailField = iframeDoc.querySelector('input[type="email"], input[name="email"], input[placeholder*="email" i]');
                    const passwordField = iframeDoc.querySelector('input[type="password"]');
                    
                    const results = {{
                        emailFound: false,
                        passwordFound: false,
                        emailFilled: false,
                        passwordFilled: false
                    }};
                    
                    if (emailField) {{
                        results.emailFound = true;
                        emailField.value = 'robert.norbeau+test2@gmail.com';
                        emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        emailField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        results.emailFilled = true;
                    }}
                    
                    if (passwordField) {{
                        results.passwordFound = true;
                        passwordField.value = 'robert.norbeau+test2';
                        passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        passwordField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        results.passwordFilled = true;
                    }}
                    
                    return results;
                }}
            """)
            
            print(f"Fill result: {fill_result}")
            
            # Look for submit button
            if fill_result['emailFilled'] and fill_result['passwordFilled']:
                await client.wait(1000)
                
                submit_result = await client.evaluate(f"""
                    () => {{
                        const iframe = document.querySelectorAll('iframe')[{target_iframe['index']}];
                        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                        
                        // Look for submit button
                        const submitButton = iframeDoc.querySelector(
                            'button[type="submit"], ' +
                            'input[type="submit"], ' +
                            'button:contains("Login"), ' +
                            'button:contains("Sign in")'
                        ) || Array.from(iframeDoc.querySelectorAll('button')).find(
                            btn => /login|sign\\s*in/i.test(btn.textContent)
                        );
                        
                        if (submitButton) {{
                            submitButton.click();
                            return {{ success: true, buttonText: submitButton.textContent }};
                        }}
                        
                        return {{ success: false }};
                    }}
                """)
                
                print(f"Submit result: {submit_result}")
    
    else:
        print("⚠️  No visible iframes found. The login popup might have closed.")
    
    # Check console logs for any login-related messages
    auth_logs = await client.get_console_logs(text_contains="auth", limit=10)
    if auth_logs["logs"]:
        print("\n📋 Recent auth logs:")
        for log in auth_logs["logs"][-5:]:
            print(f"  [{log['type']}] {log['text'][:80]}...")

if __name__ == "__main__":
    asyncio.run(handle_login_iframe())