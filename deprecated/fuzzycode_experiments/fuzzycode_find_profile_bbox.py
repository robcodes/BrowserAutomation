#!/usr/bin/env python3
"""
Find profile icon using bounding box detection with wiggle room
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def find_profile_with_bbox():
    """Find profile icon using improved bounding box detection"""
    print("=== Finding Profile with Bounding Box Detection ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # First, let's identify where we expect the profile icon to be
    print("\n→ Searching for interactive elements in top-right area...")
    
    # Find all potentially clickable elements in the top-right area with wiggle room
    candidates = await client.evaluate("""
        () => {
            // Define search area - top right with wiggle room
            const viewportWidth = window.innerWidth;
            const searchArea = {
                left: viewportWidth - 250,  // 250px from right edge
                right: viewportWidth,
                top: 0,
                bottom: 150  // Top 150px of page
            };
            
            // Get all potentially interactive elements
            const selectors = [
                'button', 'a', '[role="button"]', 'input', 
                '[onclick]', '[style*="cursor: pointer"]',
                'img', 'svg', 'i',  // Icons
                '[class*="profile"]', '[class*="user"]', '[class*="avatar"]',
                '[class*="account"]', '[class*="icon"]',
                'div', 'span'  // Generic containers that might be clickable
            ];
            
            const candidates = [];
            const seen = new Set();
            
            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    if (seen.has(el)) return;
                    seen.add(el);
                    
                    const box = el.getBoundingClientRect();
                    const styles = window.getComputedStyle(el);
                    
                    // Check if element overlaps with search area (with wiggle room)
                    const wiggle = 20;  // 20px wiggle room
                    const overlaps = 
                        box.right >= searchArea.left - wiggle &&
                        box.left <= searchArea.right + wiggle &&
                        box.bottom >= searchArea.top - wiggle &&
                        box.top <= searchArea.bottom + wiggle;
                    
                    if (overlaps && box.width > 0 && box.height > 0) {
                        // Calculate how "clickable" this element seems
                        let score = 0;
                        
                        // Interactive elements get higher scores
                        if (['BUTTON', 'A', 'INPUT'].includes(el.tagName)) score += 10;
                        if (el.getAttribute('role') === 'button') score += 10;
                        if (el.onclick || el.hasAttribute('onclick')) score += 10;
                        if (styles.cursor === 'pointer') score += 8;
                        
                        // Profile-related classes/attributes
                        const classAndId = (el.className + ' ' + el.id).toLowerCase();
                        if (classAndId.includes('profile')) score += 15;
                        if (classAndId.includes('user')) score += 12;
                        if (classAndId.includes('avatar')) score += 15;
                        if (classAndId.includes('account')) score += 10;
                        
                        // Circular elements (likely profile pics)
                        if (styles.borderRadius === '50%' || 
                            styles.borderRadius === '100%' ||
                            styles.borderRadius.includes('50%')) score += 20;
                        
                        // Has image or background image
                        if (el.tagName === 'IMG') score += 5;
                        if (styles.backgroundImage !== 'none') score += 5;
                        
                        // Reasonable size for a profile icon (20-80px)
                        if (box.width >= 20 && box.width <= 80 && 
                            box.height >= 20 && box.height <= 80) score += 5;
                        
                        // Square or circular shape
                        const aspectRatio = box.width / box.height;
                        if (aspectRatio >= 0.8 && aspectRatio <= 1.2) score += 5;
                        
                        // Distance from top-right corner (closer is better)
                        const distanceFromCorner = Math.sqrt(
                            Math.pow(viewportWidth - box.right, 2) + 
                            Math.pow(box.top, 2)
                        );
                        score += Math.max(0, 20 - distanceFromCorner / 10);
                        
                        candidates.push({
                            element: el,
                            tag: el.tagName,
                            class: el.className,
                            id: el.id,
                            box: {
                                left: box.left,
                                top: box.top,
                                right: box.right,
                                bottom: box.bottom,
                                width: box.width,
                                height: box.height
                            },
                            center: {
                                x: box.left + box.width / 2,
                                y: box.top + box.height / 2
                            },
                            styles: {
                                cursor: styles.cursor,
                                borderRadius: styles.borderRadius,
                                backgroundImage: styles.backgroundImage !== 'none'
                            },
                            score: score,
                            text: el.textContent.trim().substring(0, 20),
                            isVisible: el.offsetParent !== null,
                            path: getElementPath(el)
                        });
                    }
                });
            });
            
            // Helper function to get element path
            function getElementPath(el) {
                const path = [];
                while (el && el !== document.body) {
                    path.push(el.tagName.toLowerCase() + 
                             (el.className ? '.' + el.className.split(' ')[0] : '') +
                             (el.id ? '#' + el.id : ''));
                    el = el.parentElement;
                }
                return path.join(' > ');
            }
            
            // Sort by score (highest first)
            return candidates.sort((a, b) => b.score - a.score);
        }
    """)
    
    print(f"Found {len(candidates)} candidates in top-right area\n")
    
    # Show top 5 candidates
    print("Top 5 candidates by score:")
    for i, cand in enumerate(candidates[:5]):
        print(f"\n{i+1}. Score: {cand['score']}")
        print(f"   Element: {cand['tag']}.{cand['class']} #{cand['id']}")
        print(f"   Position: ({cand['center']['x']:.0f}, {cand['center']['y']:.0f})")
        print(f"   Size: {cand['box']['width']:.0f}x{cand['box']['height']:.0f}")
        print(f"   Circular: {cand['styles']['borderRadius']}")
        print(f"   Cursor: {cand['styles']['cursor']}")
        print(f"   Path: {cand['path']}")
    
    # Try clicking the highest scoring element
    if candidates:
        best = candidates[0]
        print(f"\n→ Clicking best candidate at ({best['center']['x']:.0f}, {best['center']['y']:.0f})...")
        
        # Store element info for clicking
        await client.evaluate(f"""
            () => {{
                window.targetElement = document.elementFromPoint({best['center']['x']}, {best['center']['y']});
                console.log('Target element:', window.targetElement);
            }}
        """)
        
        # Click using multiple methods
        click_result = await client.evaluate("""
            () => {
                const el = window.targetElement;
                if (!el) return { success: false, error: 'Element not found' };
                
                try {
                    // Method 1: Direct click
                    el.click();
                    
                    // Method 2: Dispatch mouse events
                    const mouseDown = new MouseEvent('mousedown', {
                        view: window,
                        bubbles: true,
                        cancelable: true
                    });
                    const mouseUp = new MouseEvent('mouseup', {
                        view: window,
                        bubbles: true,
                        cancelable: true
                    });
                    const click = new MouseEvent('click', {
                        view: window,
                        bubbles: true,
                        cancelable: true
                    });
                    
                    el.dispatchEvent(mouseDown);
                    el.dispatchEvent(mouseUp);
                    el.dispatchEvent(click);
                    
                    // Method 3: Check parent elements for click handlers
                    let parent = el.parentElement;
                    let clickedParent = false;
                    while (parent && !clickedParent) {
                        if (parent.onclick || parent.hasAttribute('onclick') || 
                            window.getComputedStyle(parent).cursor === 'pointer') {
                            parent.click();
                            clickedParent = true;
                        }
                        parent = parent.parentElement;
                    }
                    
                    return { 
                        success: true, 
                        element: el.tagName + '.' + el.className,
                        clickedParent: clickedParent
                    };
                } catch (e) {
                    return { success: false, error: e.message };
                }
            }
        """)
        
        print(f"Click result: {click_result}")
        
        # Wait for potential popup/iframe
        await client.wait(2000)
        await client.screenshot("fuzzycode_bbox_1_after_click.png")
        
        # Check for iframes or modals
        ui_check = await client.evaluate("""
            () => {
                const iframes = Array.from(document.querySelectorAll('iframe'))
                    .filter(iframe => iframe.offsetParent !== null);
                
                const modals = Array.from(document.querySelectorAll(
                    '.modal, [role="dialog"], .popup, .overlay, [class*="modal"], [class*="popup"]'
                )).filter(el => el.offsetParent !== null);
                
                return {
                    visibleIframes: iframes.length,
                    visibleModals: modals.length,
                    iframeInfo: iframes.map(iframe => ({
                        src: iframe.src,
                        width: iframe.clientWidth,
                        height: iframe.clientHeight
                    }))
                };
            }
        """)
        
        print(f"\n✓ UI Check:")
        print(f"  Visible iframes: {ui_check['visibleIframes']}")
        print(f"  Visible modals: {ui_check['visibleModals']}")
        
        if ui_check['visibleIframes'] > 0:
            print("\n✓ Login iframe appeared!")
            for iframe in ui_check['iframeInfo']:
                print(f"  - {iframe['src'][:50]}... ({iframe['width']}x{iframe['height']})")
    
    else:
        print("\n⚠️  No candidates found in top-right area")
    
    # Check console logs for clues
    recent_logs = await client.get_console_logs(limit=5)
    if recent_logs["logs"]:
        print("\n📋 Recent console logs:")
        for log in recent_logs["logs"]:
            print(f"  [{log['type']}] {log['text'][:80]}...")

if __name__ == "__main__":
    asyncio.run(find_profile_with_bbox())