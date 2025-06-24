#!/usr/bin/env python3
"""
Find the real profile button - it's visible in the screenshot
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def find_real_profile():
    """Find and click the actual profile avatar"""
    print("=== Finding Real Profile Avatar ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Step 14: Look at the extreme top-right corner
    print("\n→ Step 14: Looking at extreme top-right corner...")
    
    extreme_top_right = await client.evaluate("""
        () => {
            // Look at the very top-right corner (top 50px, right 100px)
            const allElements = Array.from(document.querySelectorAll('*'));
            const extremeTopRight = allElements.filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.top >= 0 && rect.top < 50 && 
                       rect.right > window.innerWidth - 100 &&
                       el.offsetParent !== null;
            });
            
            // Map details
            return extremeTopRight.map(el => ({
                tag: el.tagName.toLowerCase(),
                classes: el.className,
                id: el.id,
                text: el.textContent.trim().substring(0, 20),
                hasImage: el.querySelector('img') !== null || el.tagName === 'IMG',
                src: el.tagName === 'IMG' ? el.src : (el.querySelector('img')?.src || ''),
                rect: {
                    top: Math.round(el.getBoundingClientRect().top),
                    left: Math.round(el.getBoundingClientRect().left),
                    right: Math.round(el.getBoundingClientRect().right),
                    width: Math.round(el.getBoundingClientRect().width),
                    height: Math.round(el.getBoundingClientRect().height)
                },
                isClickable: el.onclick !== null || 
                            window.getComputedStyle(el).cursor === 'pointer' ||
                            el.tagName === 'BUTTON' || 
                            el.tagName === 'A',
                borderRadius: window.getComputedStyle(el).borderRadius
            }));
        }
    """)
    
    print(f"  Found {len(extreme_top_right)} elements in extreme top-right")
    
    for i, elem in enumerate(extreme_top_right[:10]):
        print(f"\n  Element {i+1}:")
        print(f"    Tag: {elem['tag']}")
        print(f"    Position: ({elem['rect']['left']}-{elem['rect']['right']}, {elem['rect']['top']})")
        print(f"    Size: {elem['rect']['width']}x{elem['rect']['height']}")
        print(f"    Clickable: {elem['isClickable']}")
        print(f"    Border radius: {elem['borderRadius']}")
        if elem['hasImage']:
            print(f"    Has image: {elem['src'][:50]}...")
    
    # Step 15: Click on the circular profile image
    print("\n→ Step 15: Clicking on profile avatar...")
    
    click_result = await client.evaluate("""
        () => {
            // Find circular elements in top-right
            const allElements = Array.from(document.querySelectorAll('*'));
            const profileCandidates = allElements.filter(el => {
                const rect = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);
                const isTopRight = rect.top >= 0 && rect.top < 60 && 
                                 rect.right > window.innerWidth - 100;
                const isCircular = styles.borderRadius === '50%' || 
                                 styles.borderRadius === '100%' ||
                                 styles.borderRadius.includes('999');
                return isTopRight && isCircular && el.offsetParent !== null;
            });
            
            if (profileCandidates.length > 0) {
                // Click the first circular element
                const profile = profileCandidates[0];
                profile.click();
                return { 
                    success: true, 
                    clicked: profile.tagName.toLowerCase(),
                    classes: profile.className 
                };
            }
            
            // If no circular element, look for img in top-right
            const imgs = allElements.filter(el => {
                const rect = el.getBoundingClientRect();
                return el.tagName === 'IMG' && 
                       rect.top >= 0 && rect.top < 60 && 
                       rect.right > window.innerWidth - 100;
            });
            
            if (imgs.length > 0) {
                imgs[0].click();
                return { 
                    success: true, 
                    clicked: 'img',
                    src: imgs[0].src.substring(imgs[0].src.lastIndexOf('/') + 1)
                };
            }
            
            return { success: false, message: 'No profile element found' };
        }
    """)
    
    print(f"\n  Click result: {click_result}")
    
    if click_result['success']:
        await client.wait(1500)
        await client.screenshot("fuzzy_explore_06_profile_clicked.png")
        print("  ✓ Screenshot: fuzzy_explore_06_profile_clicked.png")
        
        # Check what appeared
        after_click = await client.evaluate("""
            () => {
                const iframes = Array.from(document.querySelectorAll('iframe'));
                const visibleIframe = iframes.find(f => f.offsetParent !== null);
                
                return {
                    hasIframe: visibleIframe !== undefined,
                    iframeSrc: visibleIframe?.src,
                    iframeSize: visibleIframe ? {
                        width: visibleIframe.offsetWidth,
                        height: visibleIframe.offsetHeight
                    } : null
                };
            }
        """)
        
        print("\n  After profile click:")
        print(f"    Has iframe: {after_click['hasIframe']}")
        if after_click['iframeSrc']:
            print(f"    Iframe URL: {after_click['iframeSrc']}")
            print(f"    Iframe size: {after_click['iframeSize']['width']}x{after_click['iframeSize']['height']}")

if __name__ == "__main__":
    asyncio.run(find_real_profile())