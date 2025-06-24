#!/usr/bin/env python3
"""
Find profile in header area with more specific targeting
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def find_header_profile():
    """Find and click profile in header"""
    print("=== Finding Profile in Header ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # First, let's check the header structure
    print("\n→ Analyzing page header...")
    
    header_info = await client.evaluate("""
        () => {
            // Find header element
            const header = document.querySelector('header') || 
                          document.querySelector('nav') || 
                          document.querySelector('[role="navigation"]') ||
                          document.querySelector('.header') ||
                          document.querySelector('.navbar');
            
            if (!header) return { found: false };
            
            // Get all clickable elements in header
            const clickables = [];
            header.querySelectorAll('*').forEach(el => {
                if (el.tagName === 'IMG' || el.tagName === 'BUTTON' || 
                    el.tagName === 'A' || el.tagName === 'DIV') {
                    const rect = el.getBoundingClientRect();
                    const styles = window.getComputedStyle(el);
                    
                    // Only include visible elements on the right side
                    if (rect.width > 0 && rect.height > 0 && 
                        rect.x > window.innerWidth * 0.6) {
                        clickables.push({
                            tag: el.tagName,
                            class: el.className,
                            id: el.id,
                            src: el.src || '',
                            backgroundImage: styles.backgroundImage,
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            cursor: styles.cursor,
                            innerHTML: el.innerHTML.substring(0, 100)
                        });
                    }
                }
            });
            
            return {
                found: true,
                headerTag: header.tagName,
                headerClass: header.className,
                clickables: clickables
            };
        }
    """)
    
    if header_info['found']:
        print(f"Found header: {header_info['headerTag']}.{header_info['headerClass']}")
        print(f"\nClickable elements in right side of header: {len(header_info['clickables'])}")
        
        for i, elem in enumerate(header_info['clickables']):
            print(f"\n{i+1}. {elem['tag']} at ({elem['x']:.0f}, {elem['y']:.0f})")
            print(f"   Class: {elem['class']}")
            print(f"   Cursor: {elem['cursor']}")
            if elem['backgroundImage'] != 'none':
                print(f"   Background: {elem['backgroundImage'][:50]}...")
    
    # Look specifically in the top right corner area
    print("\n→ Checking top right corner specifically...")
    
    top_right_elements = await client.evaluate("""
        () => {
            const elements = [];
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            
            // Get all elements
            document.querySelectorAll('*').forEach(el => {
                const rect = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);
                
                // Check if element is in top right (within 200px of top and right edges)
                if (rect.x > viewportWidth - 200 && rect.y < 200 && 
                    rect.width > 0 && rect.height > 0) {
                    
                    // Check if it's likely clickable or has an image
                    const isClickable = el.tagName === 'BUTTON' || el.tagName === 'A' || 
                                      styles.cursor === 'pointer' ||
                                      el.onclick !== null ||
                                      el.hasAttribute('role');
                    
                    const hasImage = el.tagName === 'IMG' || 
                                   styles.backgroundImage !== 'none' ||
                                   el.querySelector('img') !== null;
                    
                    if (isClickable || hasImage) {
                        elements.push({
                            tag: el.tagName,
                            class: el.className,
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            backgroundImage: styles.backgroundImage,
                            cursor: styles.cursor,
                            role: el.getAttribute('role'),
                            hasImg: el.querySelector('img') !== null,
                            imgSrc: el.querySelector('img')?.src || '',
                            clickable: isClickable
                        });
                    }
                }
            });
            
            return elements.sort((a, b) => b.x - a.x);  // Rightmost first
        }
    """)
    
    print(f"\nFound {len(top_right_elements)} elements in top right corner:")
    for i, elem in enumerate(top_right_elements[:5]):
        print(f"\n{i+1}. {elem['tag']}.{elem['class']} at ({elem['x']:.0f}, {elem['y']:.0f})")
        print(f"   Size: {elem['width']}x{elem['height']}")
        print(f"   Clickable: {elem['clickable']}, Cursor: {elem['cursor']}")
        if elem['hasImg']:
            print(f"   Has image: {elem['imgSrc'][-30:] if elem['imgSrc'] else 'embedded'}")
    
    # Try clicking the most likely profile element
    if top_right_elements:
        target = top_right_elements[0]  # Rightmost element
        
        print(f"\n→ Clicking element at ({target['x']}, {target['y']})...")
        
        click_result = await client.evaluate(f"""
            () => {{
                const el = document.elementFromPoint({target['x'] + target['width']/2}, {target['y'] + target['height']/2});
                if (el) {{
                    console.log('Clicking element:', el);
                    el.click();
                    
                    // Also try dispatching click event
                    const event = new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true
                    }});
                    el.dispatchEvent(event);
                    
                    return true;
                }}
                return false;
            }}
        """)
        
        await client.wait(1500)
        await client.screenshot("fuzzycode_header_1_after_click.png")
        
        # Check if anything changed
        print("\n→ Checking for changes after click...")
        
        # Look for new dropdowns, menus, or modals
        new_ui = await client.evaluate("""
            () => {
                const found = [];
                
                // Check for various UI patterns
                const patterns = [
                    // Dropdowns and menus
                    '.dropdown-menu:not(.hidden)',
                    '[role="menu"]',
                    '.menu:not(.hidden)',
                    '.popover',
                    
                    // Modals and dialogs
                    '.modal:not(.hidden)',
                    '[role="dialog"]',
                    '.dialog',
                    
                    // Generic patterns
                    '[class*="dropdown"]:not(.hidden)',
                    '[class*="menu"]:not(.hidden)',
                    '[class*="popup"]:not(.hidden)'
                ];
                
                patterns.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        if (el.offsetParent !== null) {  // Visible
                            found.push({
                                selector: selector,
                                class: el.className,
                                content: el.textContent.substring(0, 200)
                            });
                        }
                    });
                });
                
                // Also check for any new visible links/buttons
                document.querySelectorAll('a, button').forEach(el => {
                    const text = el.textContent.toLowerCase();
                    if ((text.includes('login') || text.includes('sign') || 
                         text.includes('profile') || text.includes('account') ||
                         text.includes('settings')) && el.offsetParent !== null) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            found.push({
                                type: 'link',
                                tag: el.tagName,
                                text: el.textContent.trim(),
                                href: el.href || ''
                            });
                        }
                    }
                });
                
                return found;
            }
        """)
        
        if len(new_ui) > 0:
            print(f"\n✓ Found {len(new_ui)} new UI elements:")
            for item in new_ui:
                if item.get('type') == 'link':
                    print(f"  - {item['tag']}: {item['text']}")
                    if item.get('href'):
                        print(f"    → {item['href']}")
                else:
                    print(f"  - {item['selector']}: {item['content'][:50]}...")
        else:
            print("\n⚠️  No dropdown or menu appeared.")
    
    # Final check of page state
    print("\n→ Checking final page state...")
    
    final_state = await client.evaluate("""
        () => ({
            url: window.location.href,
            hasLoginForm: document.querySelector('input[type="password"]') !== null,
            visibleButtons: Array.from(document.querySelectorAll('button:not(.hidden)')).map(b => b.textContent.trim()).slice(0, 10),
            pageTitle: document.title
        })
    """)
    
    print(f"\nPage state:")
    print(f"  URL: {final_state['url']}")
    print(f"  Title: {final_state['pageTitle']}")
    print(f"  Has login form: {final_state['hasLoginForm']}")
    print(f"  Visible buttons: {final_state['visibleButtons'][:5]}")

if __name__ == "__main__":
    asyncio.run(find_header_profile())