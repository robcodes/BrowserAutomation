#!/usr/bin/env python3
"""
Find login button on FuzzyCode
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def find_login():
    """Find and click login button"""
    print("=== Finding Login Button ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Step 11: Look more carefully for profile/login elements
    print("\n→ Step 11: Searching for login/profile elements...")
    
    # Take screenshot to see current state
    await client.screenshot("fuzzy_explore_04_looking_for_login.png")
    
    # Search for profile in top-right corner
    profile_search = await client.evaluate("""
        () => {
            // Get all elements in viewport
            const allElements = Array.from(document.querySelectorAll('*'));
            
            // Filter for top-right elements
            const topRightElements = allElements.filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.top >= 0 && rect.top < 150 && 
                       rect.right > window.innerWidth - 200 && 
                       rect.left > window.innerWidth - 300 &&
                       el.offsetParent !== null;
            });
            
            // Look for clickable elements
            const clickableElements = topRightElements.filter(el => {
                const isClickable = el.tagName === 'BUTTON' || 
                                  el.tagName === 'A' || 
                                  el.onclick !== null ||
                                  window.getComputedStyle(el).cursor === 'pointer';
                const hasContent = el.textContent.trim().length > 0 || 
                                 el.querySelector('img, svg, i');
                return isClickable && hasContent;
            });
            
            // Get details
            return {
                topRightCount: topRightElements.length,
                clickableCount: clickableElements.length,
                elements: clickableElements.slice(0, 5).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.trim().substring(0, 50),
                    classes: el.className,
                    id: el.id,
                    hasImage: el.querySelector('img') !== null,
                    hasSvg: el.querySelector('svg') !== null,
                    rect: {
                        top: Math.round(el.getBoundingClientRect().top),
                        right: Math.round(el.getBoundingClientRect().right),
                        width: Math.round(el.getBoundingClientRect().width),
                        height: Math.round(el.getBoundingClientRect().height)
                    }
                }))
            };
        }
    """)
    
    print(f"  Found {profile_search['topRightCount']} top-right elements")
    print(f"  {profile_search['clickableCount']} are clickable")
    
    if profile_search['elements']:
        print("\n  Clickable elements found:")
        for i, elem in enumerate(profile_search['elements']):
            print(f"    {i+1}. {elem['tag']} at ({elem['rect']['right']}, {elem['rect']['top']})")
            print(f"       Size: {elem['rect']['width']}x{elem['rect']['height']}")
            print(f"       Text: '{elem['text']}'")
            print(f"       Has image: {elem['hasImage']}, Has SVG: {elem['hasSvg']}")
    
    # Step 12: Look for any avatar or circular element
    print("\n→ Step 12: Looking for avatar/circular elements...")
    
    avatar_search = await client.evaluate("""
        () => {
            // Look for circular elements (common for avatars)
            const allElements = Array.from(document.querySelectorAll('*'));
            const circularElements = allElements.filter(el => {
                const styles = window.getComputedStyle(el);
                const borderRadius = styles.borderRadius;
                const isCircular = borderRadius === '50%' || 
                                 borderRadius === '100%' ||
                                 borderRadius.includes('999');
                const hasSize = el.offsetWidth > 20 && el.offsetHeight > 20;
                const isVisible = el.offsetParent !== null;
                return isCircular && hasSize && isVisible;
            });
            
            // Also look for custom elements
            const customElements = Array.from(document.querySelectorAll('fuzzy-avatar, [class*="avatar"], [id*="avatar"]'));
            
            return {
                circularCount: circularElements.length,
                circularElements: circularElements.slice(0, 3).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    classes: el.className,
                    rect: {
                        top: Math.round(el.getBoundingClientRect().top),
                        right: Math.round(el.getBoundingClientRect().right),
                        width: Math.round(el.getBoundingClientRect().width)
                    }
                })),
                customCount: customElements.length,
                customTags: [...new Set(customElements.map(el => el.tagName.toLowerCase()))]
            };
        }
    """)
    
    print(f"  Circular elements: {avatar_search['circularCount']}")
    if avatar_search['circularElements']:
        for elem in avatar_search['circularElements']:
            print(f"    - {elem['tag']} at ({elem['rect']['right']}, {elem['rect']['top']}) - {elem['rect']['width']}px")
    
    print(f"  Custom elements: {avatar_search['customCount']}")
    if avatar_search['customTags']:
        print(f"    Tags: {', '.join(avatar_search['customTags'])}")
    
    # Step 13: Try clicking the most likely profile element
    if profile_search['clickableCount'] > 0:
        print("\n→ Step 13: Clicking the top-right element...")
        
        # Click the first clickable element in top-right
        click_result = await client.evaluate("""
            () => {
                const allElements = Array.from(document.querySelectorAll('*'));
                const topRightClickable = allElements.filter(el => {
                    const rect = el.getBoundingClientRect();
                    const isTopRight = rect.top >= 0 && rect.top < 150 && 
                                     rect.right > window.innerWidth - 200;
                    const isClickable = el.tagName === 'BUTTON' || 
                                      el.tagName === 'A' || 
                                      el.onclick !== null ||
                                      window.getComputedStyle(el).cursor === 'pointer';
                    return isTopRight && isClickable && el.offsetParent !== null;
                });
                
                if (topRightClickable.length > 0) {
                    const elem = topRightClickable[0];
                    elem.click();
                    return { success: true, clicked: elem.tagName.toLowerCase() };
                }
                return { success: false };
            }
        """)
        
        if click_result['success']:
            print(f"  ✓ Clicked {click_result['clicked']} element")
            await client.wait(1000)
            await client.screenshot("fuzzy_explore_05_after_profile_click.png")
            print("  ✓ Screenshot: fuzzy_explore_05_after_profile_click.png")
            
            # Check what appeared
            modal_check = await client.evaluate("""
                () => {
                    const iframes = Array.from(document.querySelectorAll('iframe'));
                    const modals = Array.from(document.querySelectorAll('[role="dialog"], .modal, [class*="modal"]'));
                    const dropdowns = Array.from(document.querySelectorAll('[role="menu"], .dropdown-menu, [class*="dropdown"]'));
                    
                    return {
                        hasIframe: iframes.some(f => f.offsetParent !== null),
                        iframeSrc: iframes.find(f => f.offsetParent !== null)?.src,
                        hasModal: modals.some(m => m.offsetParent !== null),
                        hasDropdown: dropdowns.some(d => d.offsetParent !== null)
                    };
                }
            """)
            
            print("\n  After click:")
            print(f"    Has iframe: {modal_check['hasIframe']}")
            if modal_check['iframeSrc']:
                print(f"    Iframe URL: {modal_check['iframeSrc']}")
            print(f"    Has modal: {modal_check['hasModal']}")
            print(f"    Has dropdown: {modal_check['hasDropdown']}")

if __name__ == "__main__":
    asyncio.run(find_login())