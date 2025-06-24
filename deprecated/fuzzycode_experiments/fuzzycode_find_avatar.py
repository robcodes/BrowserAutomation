#!/usr/bin/env python3
"""
Find and click the fuzzy-avatar element inside fuzzycode-notifications
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def find_fuzzy_avatar():
    """Find and click the fuzzy-avatar element"""
    print("=== Finding Fuzzy Avatar ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Look for the specific custom elements
    print("\n→ Looking for fuzzycode-notifications and fuzzy-avatar elements...")
    
    custom_elements = await client.evaluate("""
        () => {
            const results = {
                notifications: null,
                avatar: null,
                allCustomElements: []
            };
            
            // Find fuzzycode-notifications
            const notifications = document.querySelector('fuzzycode-notifications');
            if (notifications) {
                const box = notifications.getBoundingClientRect();
                results.notifications = {
                    found: true,
                    id: notifications.id,
                    position: {
                        x: box.left,
                        y: box.top,
                        width: box.width,
                        height: box.height
                    },
                    visible: notifications.offsetParent !== null
                };
            }
            
            // Find fuzzy-avatar
            const avatar = document.querySelector('fuzzy-avatar');
            if (avatar) {
                const box = avatar.getBoundingClientRect();
                const styles = window.getComputedStyle(avatar);
                results.avatar = {
                    found: true,
                    position: {
                        x: box.left,
                        y: box.top,
                        width: box.width,
                        height: box.height,
                        centerX: box.left + box.width / 2,
                        centerY: box.top + box.height / 2
                    },
                    styles: {
                        cursor: styles.cursor,
                        display: styles.display,
                        visibility: styles.visibility,
                        borderRadius: styles.borderRadius
                    },
                    visible: avatar.offsetParent !== null,
                    parent: avatar.parentElement ? avatar.parentElement.tagName : null
                };
            }
            
            // Also look for any custom elements (elements with hyphens in tag name)
            document.querySelectorAll('*').forEach(el => {
                if (el.tagName.includes('-')) {
                    const box = el.getBoundingClientRect();
                    if (box.width > 0 && box.height > 0) {
                        results.allCustomElements.push({
                            tag: el.tagName,
                            id: el.id,
                            x: box.left,
                            y: box.top,
                            width: box.width,
                            height: box.height
                        });
                    }
                }
            });
            
            return results;
        }
    """)
    
    print(f"\nResults:")
    print(f"fuzzycode-notifications found: {custom_elements['notifications'] is not None}")
    if custom_elements['notifications']:
        print(f"  - ID: {custom_elements['notifications']['id']}")
        print(f"  - Position: {custom_elements['notifications']['position']}")
        print(f"  - Visible: {custom_elements['notifications']['visible']}")
    
    print(f"\nfuzzy-avatar found: {custom_elements['avatar'] is not None}")
    if custom_elements['avatar']:
        print(f"  - Position: ({custom_elements['avatar']['position']['centerX']:.0f}, {custom_elements['avatar']['position']['centerY']:.0f})")
        print(f"  - Size: {custom_elements['avatar']['position']['width']}x{custom_elements['avatar']['position']['height']}")
        print(f"  - Visible: {custom_elements['avatar']['visible']}")
        print(f"  - Cursor: {custom_elements['avatar']['styles']['cursor']}")
    
    print(f"\nAll custom elements found: {len(custom_elements['allCustomElements'])}")
    for elem in custom_elements['allCustomElements'][:10]:
        print(f"  - {elem['tag']} at ({elem['x']}, {elem['y']}) - {elem['width']}x{elem['height']}")
    
    # If we found the avatar, click it
    if custom_elements['avatar'] and custom_elements['avatar']['found']:
        print(f"\n→ Clicking fuzzy-avatar at ({custom_elements['avatar']['position']['centerX']:.0f}, {custom_elements['avatar']['position']['centerY']:.0f})...")
        
        # Click the avatar
        click_result = await client.evaluate("""
            () => {
                const avatar = document.querySelector('fuzzy-avatar');
                if (avatar) {
                    console.log('Clicking fuzzy-avatar:', avatar);
                    avatar.click();
                    
                    // Also dispatch click event
                    const clickEvent = new MouseEvent('click', {
                        view: window,
                        bubbles: true,
                        cancelable: true
                    });
                    avatar.dispatchEvent(clickEvent);
                    
                    return { success: true };
                }
                return { success: false, error: 'Avatar not found' };
            }
        """)
        
        print(f"Click result: {click_result}")
        
        # Wait for popup
        await client.wait(2000)
        await client.screenshot("fuzzycode_avatar_clicked.png")
        
        # Check for login iframe
        iframe_check = await client.evaluate("""
            () => {
                const iframes = Array.from(document.querySelectorAll('iframe'));
                const visibleIframes = iframes.filter(iframe => 
                    iframe.offsetParent !== null && 
                    iframe.clientWidth > 100 && 
                    iframe.clientHeight > 100
                );
                
                return {
                    total: iframes.length,
                    visible: visibleIframes.length,
                    visibleInfo: visibleIframes.map(iframe => ({
                        src: iframe.src,
                        width: iframe.clientWidth,
                        height: iframe.clientHeight
                    }))
                };
            }
        """)
        
        print(f"\n✓ Iframe check after avatar click:")
        print(f"  Total iframes: {iframe_check['total']}")
        print(f"  Visible iframes: {iframe_check['visible']}")
        
        if iframe_check['visible'] > 0:
            print("\n✓ Login iframe appeared!")
            for iframe in iframe_check['visibleInfo']:
                print(f"  - {iframe['src'][:60]}... ({iframe['width']}x{iframe['height']})")
    
    else:
        print("\n⚠️  fuzzy-avatar element not found!")
        
        # Let's check the page structure to understand why
        print("\n→ Checking page structure...")
        
        page_info = await client.evaluate("""
            () => {
                // Check if we're in an iframe
                const inIframe = window.self !== window.top;
                
                // Get all elements in the top area
                const topElements = [];
                document.querySelectorAll('*').forEach(el => {
                    const box = el.getBoundingClientRect();
                    if (box.top < 100 && box.width > 0 && box.height > 0) {
                        topElements.push({
                            tag: el.tagName,
                            id: el.id,
                            class: el.className,
                            x: box.left,
                            y: box.top
                        });
                    }
                });
                
                return {
                    inIframe: inIframe,
                    url: window.location.href,
                    topElementsCount: topElements.length,
                    topElements: topElements.slice(0, 20)
                };
            }
        """)
        
        print(f"\nPage info:")
        print(f"  In iframe: {page_info['inIframe']}")
        print(f"  URL: {page_info['url']}")
        print(f"  Elements in top area: {page_info['topElementsCount']}")
        
        # Check console for errors
        await client.print_recent_errors()

if __name__ == "__main__":
    asyncio.run(find_fuzzy_avatar())