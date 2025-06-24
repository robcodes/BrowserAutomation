#!/usr/bin/env python3
"""
Investigate why we can't access the iframe
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def investigate_iframe_access():
    """Investigate iframe access issue"""
    print("=== Investigating Iframe Access ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Get detailed info about the page and iframe
    investigation = await client.evaluate("""
        () => {
            const mainPageInfo = {
                url: window.location.href,
                origin: window.location.origin,
                protocol: window.location.protocol,
                hostname: window.location.hostname,
                port: window.location.port
            };
            
            // Find the login iframe
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login'));
            
            if (!loginIframe) {
                return { error: 'Login iframe not found' };
            }
            
            const iframeInfo = {
                src: loginIframe.src,
                srcURL: (() => {
                    try {
                        const url = new URL(loginIframe.src);
                        return {
                            origin: url.origin,
                            protocol: url.protocol,
                            hostname: url.hostname,
                            port: url.port,
                            pathname: url.pathname
                        };
                    } catch (e) {
                        return { error: e.message };
                    }
                })()
            };
            
            // Try to access the iframe
            let accessTest = { canAccess: false };
            try {
                const iframeDoc = loginIframe.contentDocument || loginIframe.contentWindow.document;
                accessTest.canAccess = true;
                accessTest.docReady = iframeDoc.readyState;
                
                // If we can access it, try to find form elements
                if (iframeDoc) {
                    const inputs = iframeDoc.querySelectorAll('input');
                    accessTest.inputCount = inputs.length;
                    accessTest.inputs = Array.from(inputs).map(input => ({
                        type: input.type,
                        name: input.name,
                        placeholder: input.placeholder
                    }));
                }
            } catch (e) {
                accessTest.error = e.toString();
                accessTest.errorName = e.name;
                accessTest.errorMessage = e.message;
            }
            
            // Check iframe attributes
            const iframeAttributes = {
                sandbox: loginIframe.getAttribute('sandbox'),
                allow: loginIframe.getAttribute('allow'),
                id: loginIframe.id,
                className: loginIframe.className
            };
            
            return {
                mainPage: mainPageInfo,
                iframe: iframeInfo,
                accessTest: accessTest,
                attributes: iframeAttributes,
                sameOrigin: mainPageInfo.origin === iframeInfo.srcURL.origin
            };
        }
    """)
    
    print("Investigation Results:\n")
    
    print("Main Page:")
    print(f"  URL: {investigation['mainPage']['url']}")
    print(f"  Origin: {investigation['mainPage']['origin']}")
    print(f"  Protocol: {investigation['mainPage']['protocol']}")
    print(f"  Hostname: {investigation['mainPage']['hostname']}")
    
    print("\nIframe:")
    print(f"  Src: {investigation['iframe']['src']}")
    print(f"  Origin: {investigation['iframe']['srcURL']['origin']}")
    print(f"  Protocol: {investigation['iframe']['srcURL']['protocol']}")
    print(f"  Hostname: {investigation['iframe']['srcURL']['hostname']}")
    
    print(f"\nSame Origin: {investigation['sameOrigin']}")
    
    print("\nAccess Test:")
    print(f"  Can Access: {investigation['accessTest']['canAccess']}")
    if 'error' in investigation['accessTest']:
        print(f"  Error: {investigation['accessTest']['error']}")
        print(f"  Error Type: {investigation['accessTest']['errorName']}")
    else:
        print(f"  Document Ready: {investigation['accessTest'].get('docReady', 'N/A')}")
        print(f"  Input Count: {investigation['accessTest'].get('inputCount', 'N/A')}")
        if 'inputs' in investigation['accessTest']:
            print("  Inputs found:")
            for inp in investigation['accessTest']['inputs']:
                print(f"    - {inp['type']}: {inp['name']} (placeholder: {inp['placeholder']})")
    
    print("\nIframe Attributes:")
    print(f"  Sandbox: {investigation['attributes']['sandbox']}")
    print(f"  Allow: {investigation['attributes']['allow']}")
    print(f"  ID: {investigation['attributes']['id']}")
    print(f"  Class: {investigation['attributes']['className']}")
    
    # If we CAN access it, let's fill the form!
    if investigation['accessTest']['canAccess']:
        print("\n✅ We CAN access the iframe! Let's fill the form...")
        
        fill_result = await client.evaluate("""
            () => {
                const loginIframe = Array.from(document.querySelectorAll('iframe'))
                    .find(iframe => iframe.src.includes('user_login'));
                
                if (!loginIframe) return { error: 'Iframe not found' };
                
                try {
                    const iframeDoc = loginIframe.contentDocument || loginIframe.contentWindow.document;
                    
                    // Fill email
                    const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                                     iframeDoc.querySelector('input[type="text"]') ||
                                     iframeDoc.querySelector('input[name="email"]') ||
                                     iframeDoc.querySelector('input[name="username"]');
                    
                    let emailFilled = false;
                    if (emailInput) {
                        emailInput.value = 'robert.norbeau+test2@gmail.com';
                        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                        emailInput.dispatchEvent(new Event('change', { bubbles: true }));
                        emailFilled = true;
                    }
                    
                    // Fill password
                    const passwordInput = iframeDoc.querySelector('input[type="password"]');
                    let passwordFilled = false;
                    if (passwordInput) {
                        passwordInput.value = 'robert.norbeau+test2';
                        passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                        passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                        passwordFilled = true;
                    }
                    
                    return {
                        success: true,
                        emailFilled: emailFilled,
                        passwordFilled: passwordFilled
                    };
                } catch (e) {
                    return {
                        success: false,
                        error: e.toString()
                    };
                }
            }
        """)
        
        print(f"\nFill result: {fill_result}")
        
        if fill_result.get('success') and fill_result.get('emailFilled') and fill_result.get('passwordFilled'):
            await client.wait(1000)
            await client.screenshot("fuzzycode_iframe_filled.png")
            
            # Try to submit
            print("\n→ Attempting to submit form...")
            
            submit_result = await client.evaluate("""
                () => {
                    const loginIframe = Array.from(document.querySelectorAll('iframe'))
                        .find(iframe => iframe.src.includes('user_login'));
                    
                    if (!loginIframe) return { error: 'Iframe not found' };
                    
                    try {
                        const iframeDoc = loginIframe.contentDocument || loginIframe.contentWindow.document;
                        
                        // Find submit button
                        const submitBtn = iframeDoc.querySelector('button[type="submit"]') ||
                                        Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                            /sign\s*in|login/i.test(btn.textContent));
                        
                        if (submitBtn) {
                            submitBtn.click();
                            return { success: true, buttonText: submitBtn.textContent };
                        }
                        
                        return { success: false, error: 'Submit button not found' };
                    } catch (e) {
                        return { success: false, error: e.toString() };
                    }
                }
            """)
            
            print(f"Submit result: {submit_result}")

if __name__ == "__main__":
    asyncio.run(investigate_iframe_access())