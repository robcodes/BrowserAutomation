#!/usr/bin/env python3
"""
Click profile icon and handle login iframe
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def login_via_iframe():
    """Click profile and login through iframe"""
    print("=== Login via Iframe ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Look for the profile icon in the blue header area
    print("\n→ Looking for profile icon in header...")
    
    # The profile icon should be in the top right of the page header
    profile_found = await client.evaluate("""
        () => {
            // Look for circular elements in top right
            const elements = [];
            document.querySelectorAll('*').forEach(el => {
                const rect = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);
                
                // Check if element is circular (border-radius 50%) and in top right
                if (rect.y < 100 && rect.x > window.innerWidth - 200 && 
                    rect.width > 20 && rect.height > 20 &&
                    (styles.borderRadius === '50%' || 
                     styles.borderRadius.includes('50%') ||
                     el.className.includes('avatar') ||
                     el.className.includes('profile') ||
                     el.className.includes('user'))) {
                    elements.push({
                        tag: el.tagName,
                        class: el.className,
                        id: el.id,
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        borderRadius: styles.borderRadius,
                        cursor: styles.cursor,
                        background: styles.background
                    });
                }
            });
            return elements;
        }
    """)
    
    print(f"Found {len(profile_found)} circular elements in top right:")
    for elem in profile_found:
        print(f"  - {elem['tag']}.{elem['class']} at ({elem['x']}, {elem['y']}) - {elem['width']}x{elem['height']}")
    
    # Try to click on the profile icon - it might be outside the fuzzycode container
    print("\n→ Clicking in top right area where profile should be...")
    
    # Click at specific coordinates in the top right
    click_result = await client.evaluate("""
        () => {
            // Try clicking at coordinates where profile icon typically is
            const x = window.innerWidth - 50;  // 50px from right
            const y = 30;  // 30px from top
            
            const element = document.elementFromPoint(x, y);
            console.log('Element at profile location:', element);
            
            if (element) {
                element.click();
                
                // Also try parent elements
                let parent = element.parentElement;
                while (parent && parent !== document.body) {
                    if (parent.onclick || parent.style.cursor === 'pointer') {
                        parent.click();
                        break;
                    }
                    parent = parent.parentElement;
                }
                
                return {
                    clicked: true,
                    element: element.tagName + '.' + element.className
                };
            }
            return { clicked: false };
        }
    """)
    
    print(f"Click result: {click_result}")
    
    # Wait for iframe to appear
    await client.wait(2000)
    await client.screenshot("fuzzycode_iframe_1_after_profile_click.png")
    
    # Check for iframes
    print("\n→ Checking for iframes...")
    
    iframes_info = await client.evaluate("""
        () => {
            const iframes = Array.from(document.querySelectorAll('iframe'));
            return iframes.map(iframe => ({
                src: iframe.src,
                id: iframe.id,
                class: iframe.className,
                visible: iframe.offsetParent !== null,
                width: iframe.clientWidth,
                height: iframe.clientHeight,
                display: window.getComputedStyle(iframe).display
            }));
        }
    """)
    
    print(f"\nFound {len(iframes_info)} iframes:")
    for i, iframe in enumerate(iframes_info):
        print(f"\n{i+1}. Iframe:")
        print(f"   src: {iframe['src'][:50]}...")
        print(f"   visible: {iframe['visible']}")
        print(f"   size: {iframe['width']}x{iframe['height']}")
    
    # If we found a visible iframe, we need to switch to it
    if any(iframe['visible'] for iframe in iframes_info):
        print("\n→ Found visible iframe! Attempting to access it...")
        
        # Get the iframe element handle
        iframe_handle = await client.evaluate("""
            () => {
                const visibleIframe = Array.from(document.querySelectorAll('iframe'))
                    .find(iframe => iframe.offsetParent !== null);
                
                if (visibleIframe) {
                    // Check if we can access the iframe content
                    try {
                        const iframeDoc = visibleIframe.contentDocument || visibleIframe.contentWindow.document;
                        
                        // Look for login form elements in iframe
                        const emailInput = iframeDoc.querySelector('input[type="email"], input[name="email"], input[type="text"]');
                        const passwordInput = iframeDoc.querySelector('input[type="password"]');
                        
                        return {
                            accessible: true,
                            hasEmailInput: emailInput !== null,
                            hasPasswordInput: passwordInput !== null,
                            iframeUrl: visibleIframe.src
                        };
                    } catch (e) {
                        // Cross-origin iframe - we can't access it directly
                        return {
                            accessible: false,
                            error: e.message,
                            iframeUrl: visibleIframe.src
                        };
                    }
                }
                return { found: false };
            }
        """)
        
        print(f"\nIframe access result: {iframe_handle}")
        
        if iframe_handle.get('accessible'):
            print("\n✓ Can access iframe content! Filling login form...")
            
            # Fill the login form inside the iframe
            fill_result = await client.evaluate("""
                () => {
                    const iframe = Array.from(document.querySelectorAll('iframe'))
                        .find(iframe => iframe.offsetParent !== null);
                    
                    if (iframe) {
                        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                        
                        // Fill email
                        const emailInput = iframeDoc.querySelector('input[type="email"], input[name="email"], input[type="text"]');
                        if (emailInput) {
                            emailInput.value = 'robert.norbeau+test2@gmail.com';
                            emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                        
                        // Fill password
                        const passwordInput = iframeDoc.querySelector('input[type="password"]');
                        if (passwordInput) {
                            passwordInput.value = 'robert.norbeau+test2';
                            passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                        
                        return {
                            emailFilled: emailInput !== null,
                            passwordFilled: passwordInput !== null
                        };
                    }
                    return { error: 'No iframe found' };
                }
            """)
            
            print(f"Fill result: {fill_result}")
            
            await client.wait(1000)
            await client.screenshot("fuzzycode_iframe_2_form_filled.png")
            
            # Click submit button in iframe
            print("\n→ Looking for submit button in iframe...")
            
            submit_result = await client.evaluate("""
                () => {
                    const iframe = Array.from(document.querySelectorAll('iframe'))
                        .find(iframe => iframe.offsetParent !== null);
                    
                    if (iframe) {
                        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                        
                        // Look for submit button
                        const submitBtn = iframeDoc.querySelector(
                            'button[type="submit"], button:contains("Login"), button:contains("Sign in"), input[type="submit"]'
                        ) || Array.from(iframeDoc.querySelectorAll('button')).find(
                            btn => btn.textContent.toLowerCase().includes('login') || 
                                   btn.textContent.toLowerCase().includes('sign')
                        );
                        
                        if (submitBtn) {
                            submitBtn.click();
                            return { clicked: true, buttonText: submitBtn.textContent };
                        }
                    }
                    return { clicked: false };
                }
            """)
            
            print(f"Submit result: {submit_result}")
            
        else:
            print("\n⚠️  Cannot access iframe directly (cross-origin). This is expected for security reasons.")
            print("The iframe URL is:", iframe_handle.get('iframeUrl', 'unknown'))
            print("\nI cannot fill the login form automatically due to browser security restrictions.")
            print("The login iframe is from a different domain and browsers prevent cross-origin access.")
    
    else:
        print("\n⚠️  No visible iframe found. The profile click might not have worked.")
        
        # Check if there's a modal or popup instead
        modal_check = await client.evaluate("""
            () => {
                const modals = document.querySelectorAll('.modal, [role="dialog"], .popup, .overlay');
                return Array.from(modals).filter(m => m.offsetParent !== null).length;
            }
        """)
        
        print(f"Found {modal_check} visible modals/popups")
    
    # Check console for any errors
    await client.print_recent_errors()
    
    # Final screenshot
    await client.wait(2000)
    await client.screenshot("fuzzycode_iframe_3_final_state.png")

if __name__ == "__main__":
    asyncio.run(login_via_iframe())