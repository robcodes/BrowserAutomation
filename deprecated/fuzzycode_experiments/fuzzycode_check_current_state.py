#!/usr/bin/env python3
"""
Check current state and take screenshot
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def check_current_state():
    """Check current state of the page"""
    print("=== Checking Current State ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Take screenshot
    await client.screenshot("fuzzycode_current_state.png")
    print("✓ Screenshot taken: fuzzycode_current_state.png")
    
    # Check page state
    page_state = await client.evaluate("""
        () => {
            // Check for any visible modals or overlays
            const modals = document.querySelectorAll('.modal, [role="dialog"], .popup, .overlay, [class*="modal"], [class*="popup"]');
            const visibleModals = Array.from(modals).filter(m => m.offsetParent !== null);
            
            // Check iframes
            const iframes = document.querySelectorAll('iframe');
            const iframeInfo = Array.from(iframes).map(iframe => {
                const box = iframe.getBoundingClientRect();
                return {
                    src: iframe.src,
                    visible: iframe.offsetParent !== null && box.width > 0 && box.height > 0,
                    width: box.width,
                    height: box.height,
                    top: box.top,
                    left: box.left
                };
            });
            
            // Check for login-related elements
            const loginElements = [];
            document.querySelectorAll('*').forEach(el => {
                const text = el.textContent || '';
                if (text.match(/login|sign\s*in|email|password/i) && 
                    el.offsetParent !== null &&
                    !el.querySelector('*')) { // Leaf nodes only
                    const box = el.getBoundingClientRect();
                    if (box.width > 0 && box.height > 0) {
                        loginElements.push({
                            tag: el.tagName,
                            text: text.substring(0, 50),
                            x: box.left,
                            y: box.top
                        });
                    }
                }
            });
            
            return {
                url: window.location.href,
                visibleModals: visibleModals.length,
                iframes: iframeInfo,
                loginElements: loginElements.slice(0, 10)
            };
        }
    """)
    
    print(f"\nPage State:")
    print(f"  URL: {page_state['url']}")
    print(f"  Visible modals: {page_state['visibleModals']}")
    print(f"\n  Iframes ({len(page_state['iframes'])}):")
    for i, iframe in enumerate(page_state['iframes']):
        if iframe['visible']:
            print(f"    #{i}: {iframe['src'][:50]}... (visible at {iframe['left']}, {iframe['top']})")
        else:
            print(f"    #{i}: {iframe['src'][:50]}... (hidden)")
    
    if page_state['loginElements']:
        print(f"\n  Login-related elements found:")
        for elem in page_state['loginElements']:
            print(f"    - {elem['tag']}: {elem['text']} at ({elem['x']}, {elem['y']})")

if __name__ == "__main__":
    asyncio.run(check_current_state())