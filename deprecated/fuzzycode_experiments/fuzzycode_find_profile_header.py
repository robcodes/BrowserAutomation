#!/usr/bin/env python3
"""
Find profile icon specifically in the blue header area
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def find_profile_in_header():
    """Find profile icon in the blue header at top of page"""
    print("=== Finding Profile in Blue Header ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Search specifically in the very top area where the blue header is
    print("\n→ Searching in top header area (0-60px from top)...")
    
    header_elements = await client.evaluate("""
        () => {
            const candidates = [];
            const viewportWidth = window.innerWidth;
            
            // Search in the very top area (blue header region)
            const searchArea = {
                left: viewportWidth - 300,  // Right side
                right: viewportWidth,
                top: 0,
                bottom: 60  // Just the header area
            };
            
            // Get ALL elements, not just specific tags
            document.querySelectorAll('*').forEach(el => {
                const box = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);
                
                // Check if element is in the header area
                if (box.left >= searchArea.left && box.right <= searchArea.right &&
                    box.top >= searchArea.top && box.bottom <= searchArea.bottom &&
                    box.width > 10 && box.height > 10) {
                    
                    // Check for profile-like characteristics
                    const isCircular = styles.borderRadius === '50%' || 
                                     styles.borderRadius === '100%' ||
                                     styles.borderRadius.includes('50%') ||
                                     styles.borderRadius.includes('100%');
                    
                    const hasProfileClass = (el.className && typeof el.className === 'string' && 
                                           (el.className.toLowerCase().includes('profile') ||
                                            el.className.toLowerCase().includes('avatar') ||
                                            el.className.toLowerCase().includes('user')));
                    
                    const isClickable = styles.cursor === 'pointer' || 
                                      el.onclick !== null ||
                                      el.hasAttribute('onclick') ||
                                      ['A', 'BUTTON'].includes(el.tagName);
                    
                    const hasImage = el.tagName === 'IMG' || 
                                   styles.backgroundImage !== 'none' ||
                                   el.querySelector('img') !== null;
                    
                    // Calculate score
                    let score = 0;
                    if (isCircular) score += 30;
                    if (hasProfileClass) score += 20;
                    if (isClickable) score += 15;
                    if (hasImage) score += 10;
                    if (box.width >= 30 && box.width <= 60 && 
                        box.height >= 30 && box.height <= 60) score += 10; // Profile icon size
                    
                    // Distance from top-right corner
                    const distanceFromCorner = Math.sqrt(
                        Math.pow(viewportWidth - box.right, 2) + 
                        Math.pow(box.top, 2)
                    );
                    score += Math.max(0, 20 - distanceFromCorner / 10);
                    
                    if (score > 0 || box.top < 60) {  // Include all elements in header area
                        candidates.push({
                            tag: el.tagName,
                            class: el.className || '',
                            id: el.id || '',
                            box: {
                                left: box.left,
                                top: box.top,
                                right: box.right,
                                bottom: box.bottom,
                                width: box.width,
                                height: box.height,
                                centerX: box.left + box.width / 2,
                                centerY: box.top + box.height / 2
                            },
                            styles: {
                                cursor: styles.cursor,
                                borderRadius: styles.borderRadius,
                                backgroundColor: styles.backgroundColor,
                                backgroundImage: styles.backgroundImage !== 'none',
                                zIndex: styles.zIndex
                            },
                            score: score,
                            isCircular: isCircular,
                            hasImage: hasImage,
                            parent: el.parentElement ? el.parentElement.tagName + '.' + el.parentElement.className : ''
                        });
                    }
                }
            });
            
            return candidates.sort((a, b) => b.score - a.score);
        }
    """)
    
    print(f"Found {len(header_elements)} elements in header area\n")
    
    # Show top candidates
    print("Top candidates in header:")
    for i, elem in enumerate(header_elements[:10]):
        if elem['score'] > 10:  # Only show promising candidates
            print(f"\n{i+1}. Score: {elem['score']:.1f}")
            print(f"   Element: {elem['tag']}.{elem['class']}")
            print(f"   Position: ({elem['box']['centerX']:.0f}, {elem['box']['centerY']:.0f})")
            print(f"   Size: {elem['box']['width']:.0f}x{elem['box']['height']:.0f}")
            print(f"   Circular: {elem['isCircular']}, Has Image: {elem['hasImage']}")
            print(f"   Cursor: {elem['styles']['cursor']}")
            print(f"   Parent: {elem['parent']}")
    
    # Try clicking the best candidate that looks like a profile
    profile_candidate = None
    for elem in header_elements:
        if elem['isCircular'] and elem['score'] > 20:
            profile_candidate = elem
            break
    
    if not profile_candidate:
        # Look for any circular element in the header
        for elem in header_elements:
            if elem['isCircular'] or elem['hasImage']:
                profile_candidate = elem
                break
    
    if profile_candidate:
        print(f"\n→ Found likely profile icon at ({profile_candidate['box']['centerX']:.0f}, {profile_candidate['box']['centerY']:.0f})")
        print(f"   Element: {profile_candidate['tag']}.{profile_candidate['class']}")
        
        # Click it
        click_result = await client.evaluate(f"""
            () => {{
                const el = document.elementFromPoint({profile_candidate['box']['centerX']}, {profile_candidate['box']['centerY']});
                if (el) {{
                    console.log('Clicking element:', el);
                    el.click();
                    
                    // Also try clicking parent if it exists
                    if (el.parentElement) {{
                        el.parentElement.click();
                    }}
                    
                    return {{
                        success: true,
                        clicked: el.tagName + '.' + el.className
                    }};
                }}
                return {{ success: false }};
            }}
        """)
        
        print(f"Click result: {click_result}")
        
        # Wait for popup
        await client.wait(2000)
        await client.screenshot("fuzzycode_header_profile_1.png")
        
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
                        height: iframe.clientHeight,
                        id: iframe.id,
                        class: iframe.className
                    }))
                };
            }
        """)
        
        print(f"\n✓ Iframe check:")
        print(f"  Total iframes: {iframe_check['total']}")
        print(f"  Visible iframes: {iframe_check['visible']}")
        
        if iframe_check['visible'] > 0:
            print("\n✓ Login iframe appeared!")
            for iframe in iframe_check['visibleInfo']:
                print(f"  - {iframe['src'][:60]}... ({iframe['width']}x{iframe['height']})")
        
    else:
        print("\n⚠️  No profile-like element found in header")
        
        # Let's try a different approach - look for the element by color/appearance
        print("\n→ Looking for circular elements anywhere on page...")
        
        circular_elements = await client.evaluate("""
            () => {
                const elements = [];
                document.querySelectorAll('*').forEach(el => {
                    const box = el.getBoundingClientRect();
                    const styles = window.getComputedStyle(el);
                    
                    if (styles.borderRadius === '50%' || styles.borderRadius === '100%' ||
                        styles.borderRadius.includes('50%') || styles.borderRadius.includes('100%')) {
                        if (box.width > 20 && box.height > 20 && box.width < 100 && box.height < 100) {
                            elements.push({
                                tag: el.tagName,
                                class: el.className,
                                x: box.left + box.width/2,
                                y: box.top + box.height/2,
                                size: box.width + 'x' + box.height,
                                visible: el.offsetParent !== null
                            });
                        }
                    }
                });
                return elements.filter(el => el.visible);
            }
        """)
        
        print(f"\nFound {len(circular_elements)} circular elements:")
        for elem in circular_elements[:5]:
            print(f"  - {elem['tag']}.{elem['class']} at ({elem['x']:.0f}, {elem['y']:.0f}) - {elem['size']}")

if __name__ == "__main__":
    asyncio.run(find_profile_in_header())