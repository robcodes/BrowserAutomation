#!/usr/bin/env python3
"""
Debug iframe access issue
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def debug_iframe():
    """Debug why we can't access iframe content"""
    print("=== Debugging Iframe Access ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Check all iframes
    iframe_debug = await client.evaluate("""
        () => {
            const iframes = Array.from(document.querySelectorAll('iframe'));
            return iframes.map((iframe, idx) => {
                let accessible = false;
                let docInfo = null;
                
                try {
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    accessible = true;
                    docInfo = {
                        hasBody: doc.body !== null,
                        bodyHTML: doc.body ? doc.body.innerHTML.substring(0, 100) : null,
                        inputCount: doc.querySelectorAll('input').length
                    };
                } catch (e) {
                    // Cross-origin
                }
                
                return {
                    index: idx,
                    src: iframe.src,
                    visible: iframe.offsetParent !== null,
                    accessible: accessible,
                    sameOrigin: iframe.src.includes(window.location.hostname) || !iframe.src,
                    width: iframe.offsetWidth,
                    height: iframe.offsetHeight,
                    docInfo: docInfo
                };
            });
        }
    """)
    
    print("  Iframe analysis:")
    for frame in iframe_debug:
        print(f"\n  Iframe {frame['index']}:")
        print(f"    Source: {frame['src'] or '(no src)'}") 
        print(f"    Visible: {frame['visible']}")
        print(f"    Accessible: {frame['accessible']}")
        print(f"    Same origin: {frame['sameOrigin']}")
        print(f"    Size: {frame['width']}x{frame['height']}")
        if frame['docInfo']:
            print(f"    Has body: {frame['docInfo']['hasBody']}")
            print(f"    Input count: {frame['docInfo']['inputCount']}")
    
    # Try a different approach - wait and then access
    print("\n→ Waiting 2 seconds and trying again...")
    await client.wait(2000)
    
    # Try to fill the form directly without checking first
    direct_fill = await client.evaluate("""
        () => {
            // Get the second iframe (the login one)
            const iframes = Array.from(document.querySelectorAll('iframe'));
            const loginIframe = iframes[1]; // Based on previous output, second iframe has login
            
            if (!loginIframe) return { error: 'No second iframe' };
            
            try {
                const iframeDoc = loginIframe.contentDocument;
                
                // Try to find any inputs
                const inputs = iframeDoc.querySelectorAll('input');
                
                if (inputs.length >= 2) {
                    // Assume first is username, second is password
                    inputs[0].focus();
                    inputs[0].value = 'robert.norbeau+test2@gmail.com';
                    inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                    
                    inputs[1].focus();
                    inputs[1].value = 'robert.norbeau+test2';
                    inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
                    
                    return {
                        success: true,
                        filled: true,
                        inputCount: inputs.length
                    };
                }
                
                return { success: false, inputCount: inputs.length };
            } catch (e) {
                return { error: e.message };
            }
        }
    """)
    
    print(f"\n  Direct fill result: {direct_fill}")
    
    if direct_fill.get('success'):
        await client.screenshot("fuzzy_explore_19_direct_fill.png")
        print("  ✓ Screenshot: fuzzy_explore_19_direct_fill.png")
        
        # Try to click submit
        submit_click = await client.evaluate("""
            () => {
                const loginIframe = Array.from(document.querySelectorAll('iframe'))[1];
                const iframeDoc = loginIframe.contentDocument;
                
                const buttons = Array.from(iframeDoc.querySelectorAll('button'));
                const signInBtn = buttons.find(btn => btn.textContent.includes('Sign'));
                
                if (signInBtn && !signInBtn.disabled) {
                    signInBtn.click();
                    return { success: true };
                }
                
                return { 
                    success: false, 
                    found: signInBtn !== null,
                    disabled: signInBtn ? signInBtn.disabled : null
                };
            }
        """)
        
        print(f"  Submit click: {submit_click}")

if __name__ == "__main__":
    asyncio.run(debug_iframe())