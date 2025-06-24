#!/usr/bin/env python3
"""
Check if login is in iframe
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def check_login_iframe():
    """Check if login form is in an iframe"""
    print("=== Checking Login Iframe ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Check for iframes
    iframe_check = await client.evaluate("""
        () => {
            const iframes = Array.from(document.querySelectorAll('iframe'));
            return iframes.map(iframe => ({
                src: iframe.src,
                visible: iframe.offsetParent !== null,
                rect: {
                    top: Math.round(iframe.getBoundingClientRect().top),
                    left: Math.round(iframe.getBoundingClientRect().left),
                    width: Math.round(iframe.getBoundingClientRect().width),
                    height: Math.round(iframe.getBoundingClientRect().height)
                }
            }));
        }
    """)
    
    print("  Iframes found:")
    for i, iframe in enumerate(iframe_check):
        print(f"    {i+1}. Visible: {iframe['visible']}")
        print(f"       Source: {iframe['src']}")
        print(f"       Position: ({iframe['rect']['left']}, {iframe['rect']['top']})")
        print(f"       Size: {iframe['rect']['width']}x{iframe['rect']['height']}")
    
    # If there's an iframe, try to access it
    if iframe_check and any(f['visible'] for f in iframe_check):
        print("\n→ Accessing login iframe...")
        
        login_form_check = await client.evaluate("""
            () => {
                const iframes = Array.from(document.querySelectorAll('iframe'));
                const visibleIframe = iframes.find(f => f.offsetParent !== null);
                
                if (!visibleIframe) return { error: 'No visible iframe' };
                
                try {
                    const iframeDoc = visibleIframe.contentDocument || visibleIframe.contentWindow.document;
                    
                    // Find inputs in iframe
                    const inputs = Array.from(iframeDoc.querySelectorAll('input'));
                    const buttons = Array.from(iframeDoc.querySelectorAll('button'));
                    
                    return {
                        accessible: true,
                        inputCount: inputs.length,
                        inputs: inputs.map(i => ({
                            type: i.type,
                            placeholder: i.placeholder,
                            id: i.id,
                            name: i.name
                        })),
                        buttonCount: buttons.length,
                        buttons: buttons.map(b => b.textContent.trim())
                    };
                } catch (e) {
                    return {
                        accessible: false,
                        error: e.message,
                        iframeSrc: visibleIframe.src
                    };
                }
            }
        """)
        
        print(f"\n  Iframe access result: {login_form_check}")
        
        if login_form_check.get('accessible'):
            print("\n  ✅ Can access iframe content!")
            print(f"  Inputs: {login_form_check['inputs']}")
            print(f"  Buttons: {login_form_check['buttons']}")
            
            # Now fill the form
            print("\n→ Filling login form in iframe...")
            
            fill_result = await client.evaluate("""
                () => {
                    const iframe = Array.from(document.querySelectorAll('iframe')).find(f => f.offsetParent !== null);
                    if (!iframe) return { error: 'No iframe' };
                    
                    const iframeDoc = iframe.contentDocument;
                    const usernameField = iframeDoc.querySelector('input[type="text"], input[type="email"]');
                    const passwordField = iframeDoc.querySelector('input[type="password"]');
                    
                    if (usernameField && passwordField) {
                        // Fill username
                        usernameField.focus();
                        usernameField.value = 'robert.norbeau+test2@gmail.com';
                        usernameField.dispatchEvent(new Event('input', { bubbles: true }));
                        usernameField.dispatchEvent(new Event('change', { bubbles: true }));
                        
                        // Fill password
                        passwordField.focus();
                        passwordField.value = 'robert.norbeau+test2';
                        passwordField.dispatchEvent(new Event('input', { bubbles: true }));
                        passwordField.dispatchEvent(new Event('change', { bubbles: true }));
                        
                        return {
                            success: true,
                            username: usernameField.value,
                            passwordFilled: passwordField.value.length > 0
                        };
                    }
                    
                    return { success: false };
                }
            """)
            
            print(f"  Fill result: {fill_result}")
            
            if fill_result.get('success'):
                await client.wait(500)
                await client.screenshot("fuzzy_explore_13_iframe_filled.png")
                print("  ✓ Screenshot: fuzzy_explore_13_iframe_filled.png")
                
                # Click Sign In
                print("\n→ Clicking Sign In in iframe...")
                
                click_result = await client.evaluate("""
                    () => {
                        const iframe = Array.from(document.querySelectorAll('iframe')).find(f => f.offsetParent !== null);
                        const iframeDoc = iframe.contentDocument;
                        
                        const signInBtn = Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                            btn.textContent.includes('Sign In')
                        );
                        
                        if (signInBtn && !signInBtn.disabled) {
                            signInBtn.click();
                            return { success: true };
                        }
                        
                        return { success: false, disabled: signInBtn ? signInBtn.disabled : null };
                    }
                """)
                
                print(f"  Click result: {click_result}")
                
                if click_result.get('success'):
                    await client.wait(3000)
                    await client.screenshot("fuzzy_explore_14_after_iframe_login.png")
                    print("  ✓ Screenshot: fuzzy_explore_14_after_iframe_login.png")

if __name__ == "__main__":
    asyncio.run(check_login_iframe())