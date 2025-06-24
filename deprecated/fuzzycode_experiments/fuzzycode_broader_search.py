#!/usr/bin/env python3
"""
Broader search for interactive elements
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def broader_search():
    """Do a broader search for all interactive elements"""
    print("=== Broader Element Search ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Take screenshot first
    await client.screenshot("fuzzy_explore_07_current_state.png")
    
    # Step 16: Find ALL images on the page
    print("\n→ Step 16: Finding all images...")
    
    all_images = await client.evaluate("""
        () => {
            const imgs = Array.from(document.querySelectorAll('img'));
            return imgs.map(img => ({
                src: img.src,
                alt: img.alt,
                title: img.title,
                width: img.width,
                height: img.height,
                rect: {
                    top: Math.round(img.getBoundingClientRect().top),
                    left: Math.round(img.getBoundingClientRect().left),
                    right: Math.round(img.getBoundingClientRect().right)
                },
                visible: img.offsetParent !== null,
                clickable: img.onclick !== null || 
                          img.parentElement?.onclick !== null ||
                          window.getComputedStyle(img).cursor === 'pointer' ||
                          window.getComputedStyle(img.parentElement || img).cursor === 'pointer',
                parentTag: img.parentElement?.tagName.toLowerCase()
            })).filter(img => img.visible);
        }
    """)
    
    print(f"  Found {len(all_images)} visible images")
    for i, img in enumerate(all_images[:5]):
        print(f"\n  Image {i+1}:")
        print(f"    Source: ...{img['src'][-40:]}")
        print(f"    Position: ({img['rect']['left']}, {img['rect']['top']})")
        print(f"    Size: {img['width']}x{img['height']}")
        print(f"    Clickable: {img['clickable']}")
        print(f"    Parent: {img['parentTag']}")
    
    # Step 17: Find ALL clickable elements
    print("\n\n→ Step 17: Finding all clickable elements...")
    
    clickable_elements = await client.evaluate("""
        () => {
            const allElements = Array.from(document.querySelectorAll('*'));
            const clickable = allElements.filter(el => {
                if (!el.offsetParent) return false;
                
                const tag = el.tagName.toLowerCase();
                const cursor = window.getComputedStyle(el).cursor;
                const hasClick = el.onclick !== null;
                const isLink = tag === 'a' && el.href;
                const isButton = tag === 'button';
                const isClickable = cursor === 'pointer';
                
                return (hasClick || isLink || isButton || isClickable) && 
                       el.getBoundingClientRect().width > 0 &&
                       el.getBoundingClientRect().height > 0;
            });
            
            // Group by position
            const topElements = clickable.filter(el => el.getBoundingClientRect().top < 100);
            const rightElements = clickable.filter(el => el.getBoundingClientRect().right > window.innerWidth - 150);
            
            return {
                totalClickable: clickable.length,
                topClickable: topElements.length,
                rightClickable: rightElements.length,
                topRightClickable: clickable.filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.top < 100 && rect.right > window.innerWidth - 150;
                }).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.trim().substring(0, 30),
                    classes: el.className,
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
    
    print(f"  Total clickable: {clickable_elements['totalClickable']}")
    print(f"  Top area: {clickable_elements['topClickable']}")
    print(f"  Right area: {clickable_elements['rightClickable']}")
    print(f"  Top-right area: {len(clickable_elements['topRightClickable'])}")
    
    if clickable_elements['topRightClickable']:
        print("\n  Top-right clickable elements:")
        for elem in clickable_elements['topRightClickable']:
            print(f"    - {elem['tag']} at ({elem['rect']['right']}, {elem['rect']['top']}) - {elem['rect']['width']}x{elem['rect']['height']}")
            print(f"      Text: '{elem['text']}'")
    
    # Step 18: Look for the actual profile element by examining the page more carefully
    print("\n\n→ Step 18: Examining page structure for profile...")
    
    profile_hunt = await client.evaluate("""
        () => {
            // Look in common locations for profile
            const selectors = [
                'fuzzy-avatar',
                '[class*="profile"]',
                '[class*="avatar"]',
                '[class*="user"]',
                '[id*="profile"]',
                '[id*="avatar"]',
                '[id*="user"]',
                'img[alt*="profile"]',
                'img[alt*="avatar"]',
                'img[alt*="user"]'
            ];
            
            const found = [];
            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    found.push({
                        selector: selector,
                        count: elements.length,
                        first: {
                            tag: elements[0].tagName.toLowerCase(),
                            visible: elements[0].offsetParent !== null,
                            rect: elements[0].getBoundingClientRect()
                        }
                    });
                }
            }
            
            return found;
        }
    """)
    
    if profile_hunt:
        print("  Found potential profile elements:")
        for item in profile_hunt:
            print(f"    - Selector '{item['selector']}' found {item['count']} element(s)")
            print(f"      First: {item['first']['tag']}, visible: {item['first']['visible']}")

if __name__ == "__main__":
    asyncio.run(broader_search())