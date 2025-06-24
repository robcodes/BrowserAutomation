#!/usr/bin/env python3
"""
Deep inspection of fuzzycode-notifications element
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def inspect_notifications():
    """Inspect the fuzzycode-notifications element in detail"""
    print("=== Inspecting fuzzycode-notifications ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Deep inspection of the notifications element
    print("\n→ Inspecting fuzzycode-notifications element...")
    
    notifications_info = await client.evaluate("""
        () => {
            const notifications = document.querySelector('fuzzycode-notifications');
            if (!notifications) return { found: false };
            
            const box = notifications.getBoundingClientRect();
            const styles = window.getComputedStyle(notifications);
            
            // Check shadow DOM
            const hasShadowRoot = notifications.shadowRoot !== null;
            let shadowContent = null;
            
            if (hasShadowRoot) {
                // Try to access shadow DOM content
                const shadowElements = [];
                notifications.shadowRoot.querySelectorAll('*').forEach(el => {
                    shadowElements.push({
                        tag: el.tagName,
                        id: el.id,
                        class: el.className
                    });
                });
                shadowContent = shadowElements;
            }
            
            // Get all children
            const children = [];
            notifications.querySelectorAll('*').forEach(child => {
                const childBox = child.getBoundingClientRect();
                children.push({
                    tag: child.tagName,
                    id: child.id,
                    class: child.className,
                    position: {
                        x: childBox.left,
                        y: childBox.top,
                        width: childBox.width,
                        height: childBox.height
                    },
                    visible: child.offsetParent !== null
                });
            });
            
            // Check innerHTML
            const innerHTML = notifications.innerHTML;
            
            return {
                found: true,
                position: {
                    x: box.left,
                    y: box.top,
                    width: box.width,
                    height: box.height
                },
                styles: {
                    display: styles.display,
                    visibility: styles.visibility,
                    position: styles.position,
                    zIndex: styles.zIndex,
                    overflow: styles.overflow
                },
                hasShadowRoot: hasShadowRoot,
                shadowContent: shadowContent,
                children: children,
                innerHTML: innerHTML.substring(0, 500),
                parent: notifications.parentElement ? {
                    tag: notifications.parentElement.tagName,
                    id: notifications.parentElement.id,
                    class: notifications.parentElement.className
                } : null
            };
        }
    """)
    
    if notifications_info['found']:
        print(f"\nfuzzycode-notifications details:")
        print(f"  Position: ({notifications_info['position']['x']}, {notifications_info['position']['y']})")
        print(f"  Size: {notifications_info['position']['width']}x{notifications_info['position']['height']}")
        print(f"  Display: {notifications_info['styles']['display']}")
        print(f"  Visibility: {notifications_info['styles']['visibility']}")
        print(f"  Position type: {notifications_info['styles']['position']}")
        print(f"  z-index: {notifications_info['styles']['zIndex']}")
        print(f"  Has shadow DOM: {notifications_info['hasShadowRoot']}")
        print(f"  Children count: {len(notifications_info['children'])}")
        print(f"  innerHTML preview: {notifications_info['innerHTML'][:100]}...")
        
        if notifications_info['parent']:
            print(f"  Parent: {notifications_info['parent']['tag']}.{notifications_info['parent']['class']}")
        
        if notifications_info['children']:
            print("\n  Children elements:")
            for child in notifications_info['children']:
                print(f"    - {child['tag']}.{child['class']} at ({child['position']['x']}, {child['position']['y']})")
    
    # Look for avatar in the entire document more thoroughly
    print("\n→ Searching for avatar elements anywhere...")
    
    avatar_search = await client.evaluate("""
        () => {
            const results = {
                fuzzyAvatar: [],
                avatarClasses: [],
                circularElements: [],
                topRightElements: []
            };
            
            // Search for fuzzy-avatar
            document.querySelectorAll('fuzzy-avatar').forEach(el => {
                const box = el.getBoundingClientRect();
                results.fuzzyAvatar.push({
                    position: { x: box.left, y: box.top, width: box.width, height: box.height },
                    parent: el.parentElement ? el.parentElement.tagName : null
                });
            });
            
            // Search for elements with avatar in class name
            document.querySelectorAll('[class*="avatar"]').forEach(el => {
                const box = el.getBoundingClientRect();
                if (box.width > 0 && box.height > 0) {
                    results.avatarClasses.push({
                        tag: el.tagName,
                        class: el.className,
                        position: { x: box.left, y: box.top, width: box.width, height: box.height }
                    });
                }
            });
            
            // Search for circular elements in top-right
            const viewportWidth = window.innerWidth;
            document.querySelectorAll('*').forEach(el => {
                const box = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);
                
                if (box.right > viewportWidth - 200 && box.top < 100 && 
                    box.width > 20 && box.height > 20 &&
                    (styles.borderRadius === '50%' || styles.borderRadius.includes('50%'))) {
                    results.circularElements.push({
                        tag: el.tagName,
                        class: el.className,
                        position: { x: box.left, y: box.top, width: box.width, height: box.height },
                        cursor: styles.cursor
                    });
                }
            });
            
            // Get all elements in top-right corner
            document.querySelectorAll('*').forEach(el => {
                const box = el.getBoundingClientRect();
                if (box.right > viewportWidth - 100 && box.top < 60 && 
                    box.width > 10 && box.height > 10) {
                    results.topRightElements.push({
                        tag: el.tagName,
                        class: el.className || '',
                        id: el.id || '',
                        x: Math.round(box.left),
                        y: Math.round(box.top)
                    });
                }
            });
            
            return results;
        }
    """)
    
    print(f"\nSearch results:")
    print(f"  fuzzy-avatar elements: {len(avatar_search['fuzzyAvatar'])}")
    print(f"  Elements with 'avatar' class: {len(avatar_search['avatarClasses'])}")
    print(f"  Circular elements in top-right: {len(avatar_search['circularElements'])}")
    print(f"  All elements in top-right: {len(avatar_search['topRightElements'])}")
    
    if avatar_search['avatarClasses']:
        print("\n  Avatar class elements:")
        for elem in avatar_search['avatarClasses']:
            print(f"    - {elem['tag']}.{elem['class']} at ({elem['position']['x']}, {elem['position']['y']})")
    
    if avatar_search['circularElements']:
        print("\n  Circular elements in top-right:")
        for elem in avatar_search['circularElements']:
            print(f"    - {elem['tag']}.{elem['class']} at ({elem['position']['x']}, {elem['position']['y']})")
    
    if avatar_search['topRightElements']:
        print("\n  Elements in top-right corner:")
        for elem in avatar_search['topRightElements'][:10]:
            print(f"    - {elem['tag']}.{elem['class']} #{elem['id']} at ({elem['x']}, {elem['y']})")

if __name__ == "__main__":
    asyncio.run(inspect_notifications())