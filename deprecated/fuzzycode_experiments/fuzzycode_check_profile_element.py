#!/usr/bin/env python3
"""
Check the profile element we found
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def check_profile_element():
    """Check the element with profile class"""
    print("=== Checking Profile Element ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Step 19: Examine the profile element
    print("\n→ Step 19: Examining element with 'profile' class...")
    
    profile_details = await client.evaluate("""
        () => {
            const profileElements = Array.from(document.querySelectorAll('[class*="profile"]'));
            
            return profileElements.map(el => ({
                tag: el.tagName.toLowerCase(),
                className: el.className,
                id: el.id,
                text: el.textContent.trim(),
                innerHTML: el.innerHTML.substring(0, 200),
                rect: {
                    top: Math.round(el.getBoundingClientRect().top),
                    left: Math.round(el.getBoundingClientRect().left),
                    right: Math.round(el.getBoundingClientRect().right),
                    bottom: Math.round(el.getBoundingClientRect().bottom),
                    width: Math.round(el.getBoundingClientRect().width),
                    height: Math.round(el.getBoundingClientRect().height)
                },
                visible: el.offsetParent !== null,
                parent: {
                    tag: el.parentElement?.tagName.toLowerCase(),
                    className: el.parentElement?.className
                },
                clickable: el.onclick !== null || 
                          window.getComputedStyle(el).cursor === 'pointer' ||
                          el.parentElement?.onclick !== null
            }));
        }
    """)
    
    for i, elem in enumerate(profile_details):
        print(f"\n  Profile element {i+1}:")
        print(f"    Tag: {elem['tag']}")
        print(f"    Class: {elem['className']}")
        print(f"    Text: '{elem['text']}'")
        print(f"    Position: ({elem['rect']['left']}, {elem['rect']['top']}) to ({elem['rect']['right']}, {elem['rect']['bottom']})")
        print(f"    Size: {elem['rect']['width']}x{elem['rect']['height']}")
        print(f"    Clickable: {elem['clickable']}")
        print(f"    Parent: {elem['parent']['tag']} ({elem['parent']['className']})")
    
    # Step 20: Look at the header/nav area more carefully
    print("\n\n→ Step 20: Examining header/navigation area...")
    
    header_analysis = await client.evaluate("""
        () => {
            // Find header/nav elements
            const headers = Array.from(document.querySelectorAll('header, nav, [role="navigation"], [class*="header"], [class*="nav"]'));
            
            // Also look at the top 100px of the page
            const topElements = Array.from(document.querySelectorAll('*')).filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.top >= 0 && rect.top < 100 && el.offsetParent !== null;
            });
            
            // Find elements with background images
            const withBgImages = topElements.filter(el => {
                const bg = window.getComputedStyle(el).backgroundImage;
                return bg && bg !== 'none';
            });
            
            return {
                headerCount: headers.length,
                topElementCount: topElements.length,
                withBgImageCount: withBgImages.length,
                bgImages: withBgImages.slice(0, 3).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    bgImage: window.getComputedStyle(el).backgroundImage,
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
    
    print(f"  Headers found: {header_analysis['headerCount']}")
    print(f"  Elements in top 100px: {header_analysis['topElementCount']}")
    print(f"  Elements with background images: {header_analysis['withBgImageCount']}")
    
    if header_analysis['bgImages']:
        print("\n  Elements with background images:")
        for elem in header_analysis['bgImages']:
            print(f"    - {elem['tag']} at ({elem['rect']['right']}, {elem['rect']['top']}) - {elem['rect']['width']}x{elem['rect']['height']}")
            print(f"      Background: {elem['bgImage'][:60]}...")
    
    # Step 21: Look for the Play Now button that might lead to login
    print("\n\n→ Step 21: Looking for 'Play Now' button...")
    
    play_button = await client.evaluate("""
        () => {
            const buttons = Array.from(document.querySelectorAll('button, a'));
            const playButton = buttons.find(btn => 
                btn.textContent.toLowerCase().includes('play') &&
                btn.offsetParent !== null
            );
            
            if (playButton) {
                return {
                    found: true,
                    tag: playButton.tagName.toLowerCase(),
                    text: playButton.textContent.trim(),
                    rect: {
                        top: Math.round(playButton.getBoundingClientRect().top),
                        left: Math.round(playButton.getBoundingClientRect().left),
                        width: Math.round(playButton.getBoundingClientRect().width),
                        height: Math.round(playButton.getBoundingClientRect().height)
                    }
                };
            }
            return { found: false };
        }
    """)
    
    if play_button['found']:
        print(f"  Found '{play_button['text']}' button")
        print(f"  Position: ({play_button['rect']['left']}, {play_button['rect']['top']})")
        print(f"  Size: {play_button['rect']['width']}x{play_button['rect']['height']}")
        
        # Click it
        print("\n  → Clicking 'Play Now' button...")
        click_result = await client.evaluate("""
            () => {
                const buttons = Array.from(document.querySelectorAll('button, a'));
                const playButton = buttons.find(btn => 
                    btn.textContent.toLowerCase().includes('play') &&
                    btn.offsetParent !== null
                );
                
                if (playButton) {
                    playButton.click();
                    return { success: true };
                }
                return { success: false };
            }
        """)
        
        if click_result['success']:
            await client.wait(2000)
            await client.screenshot("fuzzy_explore_08_after_play_now.png")
            print("  ✓ Clicked Play Now")
            print("  ✓ Screenshot: fuzzy_explore_08_after_play_now.png")

if __name__ == "__main__":
    asyncio.run(check_profile_element())