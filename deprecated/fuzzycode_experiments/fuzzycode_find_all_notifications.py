#!/usr/bin/env python3
"""
Find all fuzzycode-notifications elements and check their positions
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def find_all_notifications():
    """Find all instances of fuzzycode-notifications"""
    print("=== Finding All Notifications Elements ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Find all notifications elements
    print("\n→ Looking for all fuzzycode-notifications elements...")
    
    all_notifications = await client.evaluate("""
        () => {
            const notifications = document.querySelectorAll('fuzzycode-notifications');
            const results = [];
            
            notifications.forEach((notif, index) => {
                const box = notif.getBoundingClientRect();
                const styles = window.getComputedStyle(notif);
                
                // Try to access shadow DOM and find avatar
                let avatarInfo = null;
                if (notif.shadowRoot) {
                    const avatar = notif.shadowRoot.querySelector('fuzzy-avatar');
                    if (avatar) {
                        const avatarBox = avatar.getBoundingClientRect();
                        avatarInfo = {
                            found: true,
                            x: avatarBox.left,
                            y: avatarBox.top,
                            width: avatarBox.width,
                            height: avatarBox.height
                        };
                    }
                }
                
                results.push({
                    index: index,
                    id: notif.id,
                    position: {
                        x: box.left,
                        y: box.top,
                        width: box.width,
                        height: box.height
                    },
                    styles: {
                        position: styles.position,
                        display: styles.display,
                        visibility: styles.visibility,
                        top: styles.top,
                        right: styles.right,
                        left: styles.left,
                        bottom: styles.bottom,
                        zIndex: styles.zIndex
                    },
                    visible: notif.offsetParent !== null || styles.position === 'fixed',
                    hasShadowRoot: notif.shadowRoot !== null,
                    avatarInfo: avatarInfo
                });
            });
            
            return results;
        }
    """)
    
    print(f"Found {len(all_notifications)} fuzzycode-notifications elements:\n")
    
    for notif in all_notifications:
        print(f"#{notif['index']} - ID: {notif['id']}")
        print(f"  Position: ({notif['position']['x']}, {notif['position']['y']})")
        print(f"  Size: {notif['position']['width']}x{notif['position']['height']}")
        print(f"  CSS Position: {notif['styles']['position']}")
        print(f"  Display: {notif['styles']['display']}")
        print(f"  Visible: {notif['visible']}")
        print(f"  Has Shadow DOM: {notif['hasShadowRoot']}")
        if notif['avatarInfo']:
            print(f"  Avatar found at: ({notif['avatarInfo']['x']}, {notif['avatarInfo']['y']})")
        print()
    
    # Try clicking on the document at the expected profile location
    print("→ Trying to click at expected profile location (top-right)...")
    
    # Click in the top-right corner area
    click_result = await client.evaluate("""
        () => {
            const x = window.innerWidth - 50;  // 50px from right
            const y = 35;  // 35px from top
            
            console.log(`Clicking at coordinates: (${x}, ${y})`);
            
            // Get element at coordinates
            const element = document.elementFromPoint(x, y);
            console.log('Element at coordinates:', element);
            
            if (element) {
                // Click the element
                element.click();
                
                // Also try dispatching events
                const clickEvent = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: x,
                    clientY: y
                });
                element.dispatchEvent(clickEvent);
                
                // Check if it's inside a shadow DOM
                let current = element;
                while (current) {
                    if (current.shadowRoot) {
                        console.log('Found shadow root in:', current);
                    }
                    current = current.parentElement;
                }
                
                return {
                    success: true,
                    element: {
                        tag: element.tagName,
                        class: element.className,
                        id: element.id
                    }
                };
            }
            
            return { success: false };
        }
    """)
    
    print(f"Click result: {click_result}")
    
    # Wait and check for changes
    await client.wait(2000)
    await client.screenshot("fuzzycode_click_topright.png")
    
    # Check if login iframe appeared
    iframe_check = await client.evaluate("""
        () => {
            const iframes = document.querySelectorAll('iframe');
            const visible = Array.from(iframes).filter(
                iframe => iframe.offsetParent !== null && 
                         iframe.clientWidth > 100 && 
                         iframe.clientHeight > 100
            );
            
            return {
                total: iframes.length,
                visible: visible.length,
                visibleSrcs: visible.map(iframe => iframe.src)
            };
        }
    """)
    
    print(f"\n✓ Iframe check:")
    print(f"  Total: {iframe_check['total']}")
    print(f"  Visible: {iframe_check['visible']}")
    
    if iframe_check['visible'] > 0:
        print("  Visible iframe sources:")
        for src in iframe_check['visibleSrcs']:
            print(f"    - {src[:60]}...")
    
    # Check console logs
    recent_logs = await client.get_console_logs(limit=5)
    if recent_logs["logs"]:
        print("\n📋 Recent console logs:")
        for log in recent_logs["logs"]:
            if "click" in log['text'].lower() or "element" in log['text'].lower():
                print(f"  [{log['type']}] {log['text']}")

if __name__ == "__main__":
    asyncio.run(find_all_notifications())