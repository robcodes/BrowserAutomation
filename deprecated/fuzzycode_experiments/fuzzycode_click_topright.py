#!/usr/bin/env python3
"""
Click on the top right profile area
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def click_topright_profile():
    """Click the profile icon in top right"""
    print("=== Clicking Top Right Profile ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Get all images on the page
    print("\n→ Finding all images on page...")
    
    images = await client.evaluate("""
        () => {
            const imgs = [];
            document.querySelectorAll('img').forEach(img => {
                const rect = img.getBoundingClientRect();
                imgs.push({
                    src: img.src,
                    alt: img.alt,
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    visible: img.offsetParent !== null
                });
            });
            return imgs.sort((a, b) => b.x - a.x);  // Sort by x position (rightmost first)
        }
    """)
    
    print(f"Found {len(images)} images:")
    for i, img in enumerate(images[:5]):  # Show top 5
        print(f"  {i+1}. x={img['x']:.0f}, y={img['y']:.0f}, src={img['src'][-30:] if img['src'] else 'none'}")
    
    # Click the rightmost visible image (likely the profile)
    if images and images[0]['visible']:
        print(f"\n→ Clicking rightmost image at ({images[0]['x']}, {images[0]['y']})")
        
        # Click using coordinates
        await client.evaluate(f"""
            () => {{
                const img = document.elementFromPoint({images[0]['x'] + images[0]['width']/2}, {images[0]['y'] + images[0]['height']/2});
                if (img) {{
                    img.click();
                    return true;
                }}
                return false;
            }}
        """)
        
        await client.wait(1500)
        await client.screenshot("fuzzycode_profile_1_clicked.png")
        
        # Check what appeared
        print("\n→ Checking for menu or modal...")
        
        # Look for any newly visible elements
        new_elements = await client.evaluate("""
            () => {
                const elements = [];
                
                // Check for modals, dropdowns, menus
                const selectors = [
                    '[role="menu"]',
                    '[role="dialog"]',
                    '.dropdown',
                    '.modal',
                    '.menu',
                    '.popover',
                    '[class*="menu"]',
                    '[class*="dropdown"]'
                ];
                
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        if (el.offsetParent !== null) {
                            elements.push({
                                tag: el.tagName,
                                class: el.className,
                                text: el.textContent.substring(0, 100)
                            });
                        }
                    });
                });
                
                // Also check for any links/buttons with auth-related text
                document.querySelectorAll('a, button').forEach(el => {
                    const text = el.textContent.toLowerCase();
                    if ((text.includes('login') || text.includes('sign') || 
                         text.includes('logout') || text.includes('profile')) && 
                        el.offsetParent !== null) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            elements.push({
                                tag: el.tagName,
                                text: el.textContent.trim(),
                                href: el.href || ''
                            });
                        }
                    }
                });
                
                return elements;
            }
        """)
        
        print(f"\nFound {len(new_elements)} potentially relevant elements:")
        for elem in new_elements:
            print(f"  - {elem['tag']}: {elem.get('text', '')[:50]}...")
            if elem.get('href'):
                print(f"    href: {elem['href']}")
        
        # Try to find and click login
        login_clicked = False
        for text in ['Login', 'Sign in', 'Log in', 'Sign In', 'LOG IN']:
            try:
                selector = f'*:has-text("{text}")'
                exists = await client.evaluate(f"""
                    () => {{
                        const els = Array.from(document.querySelectorAll('a, button'));
                        return els.some(el => el.textContent.includes('{text}') && el.offsetParent !== null);
                    }}
                """)
                
                if exists:
                    print(f"\n→ Found '{text}' - clicking it")
                    await client.evaluate(f"""
                        () => {{
                            const els = Array.from(document.querySelectorAll('a, button'));
                            const el = els.find(el => el.textContent.includes('{text}'));
                            if (el) el.click();
                        }}
                    """)
                    login_clicked = True
                    await client.wait(2000)
                    await client.screenshot("fuzzycode_profile_2_after_login_click.png")
                    break
            except:
                continue
        
        if not login_clicked:
            print("\n⚠️  No login option found. Let me check the page structure...")
            
            # Get the current user state from the page
            user_info = await client.evaluate("""
                () => {
                    // Check for username displays
                    const userTexts = [];
                    document.querySelectorAll('*').forEach(el => {
                        const text = el.textContent;
                        if (text && (text.includes('anonymous') || text.includes('@') || 
                                    text.includes('user') || text.includes('User'))) {
                            userTexts.push(text.trim().substring(0, 50));
                        }
                    });
                    
                    // Check localStorage/sessionStorage
                    const storage = {
                        local: Object.keys(localStorage),
                        session: Object.keys(sessionStorage)
                    };
                    
                    return {
                        userTexts: userTexts.slice(0, 5),
                        storage: storage
                    };
                }
            """)
            
            print("\nUser-related text on page:")
            for text in user_info['userTexts']:
                print(f"  - {text}")
            
            print("\nStorage keys:")
            print(f"  localStorage: {user_info['storage']['local'][:5]}")
            print(f"  sessionStorage: {user_info['storage']['session'][:5]}")
    
    # Check URL again
    current_url = await client.evaluate("() => window.location.href")
    print(f"\nCurrent URL: {current_url}")
    
    # Get console logs to understand auth state
    auth_logs = await client.get_console_logs(text_contains="auth", limit=10)
    if auth_logs["logs"]:
        print("\n📋 Recent auth logs:")
        for log in auth_logs["logs"][-3:]:
            print(f"  [{log['type']}] {log['text'][:100]}...")

if __name__ == "__main__":
    asyncio.run(click_topright_profile())