#!/usr/bin/env python3
"""Find and click close button using multiple strategies"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.fuzzycode_steps.common import *

async def main():
    # Load session
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    print("Finding close button elements...")
    
    # Find all potential close buttons
    close_elements = await client.evaluate("""
        (() => {
            const results = [];
            
            // Strategy 1: Look for buttons with close-related classes
            const closeButtons = document.querySelectorAll(
                'button.close, .close-button, .btn-close, [aria-label*="close"], [aria-label*="Close"], button[title*="close"], button[title*="Close"]'
            );
            
            closeButtons.forEach((btn, idx) => {
                const rect = btn.getBoundingClientRect();
                results.push({
                    type: 'button',
                    selector: \`closeButton[\${idx}]\`,
                    text: btn.textContent.trim(),
                    ariaLabel: btn.getAttribute('aria-label'),
                    title: btn.getAttribute('title'),
                    className: btn.className,
                    x: rect.left + rect.width/2,
                    y: rect.top + rect.height/2,
                    visible: btn.offsetParent !== null
                });
            });
            
            // Strategy 2: Look for X symbols
            const allElements = document.querySelectorAll('*');
            allElements.forEach((el, idx) => {
                const text = el.textContent.trim();
                if ((text === 'X' || text === '×' || text === 'x' || text === '✕') && 
                    el.children.length === 0) {
                    const rect = el.getBoundingClientRect();
                    if (rect.left > 900 && rect.top < 100) {  // Top-right area
                        results.push({
                            type: 'text',
                            selector: \`xSymbol[\${idx}]\`,
                            text: text,
                            tagName: el.tagName,
                            className: el.className,
                            x: rect.left + rect.width/2,
                            y: rect.top + rect.height/2,
                            visible: el.offsetParent !== null
                        });
                    }
                }
            });
            
            // Strategy 3: Check popup-specific elements
            const popupIcons = document.querySelectorAll('.popup-icons *');
            popupIcons.forEach((icon, idx) => {
                const rect = icon.getBoundingClientRect();
                results.push({
                    type: 'popup-icon',
                    selector: \`.popup-icons > :nth-child(\${idx + 1})\`,
                    tagName: icon.tagName,
                    className: icon.className,
                    x: rect.left + rect.width/2,
                    y: rect.top + rect.height/2,
                    visible: icon.offsetParent !== null
                });
            });
            
            return results;
        })()
    """)
    
    print(f"\nFound {len(close_elements)} potential close elements:")
    for el in close_elements:
        if el['visible']:
            print(f"  {el['type']}: {el.get('text', 'no text')} at ({el['x']}, {el['y']}) - {el.get('className', 'no class')}")
    
    # Try clicking each visible element in the top-right
    for el in close_elements:
        if el['visible'] and el['x'] > 900 and el['y'] < 100:
            print(f"\nTrying to click {el['type']} at ({el['x']}, {el['y']})")
            
            await client.evaluate(f"""
                (() => {{
                    const el = document.querySelector('{el['selector']}');
                    if (el) {{
                        el.click();
                        // Also try dispatching event
                        el.dispatchEvent(new MouseEvent('click', {{
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }}));
                    }}
                }})()
            """)
            
            await asyncio.sleep(0.5)
            
            # Check if popup is gone
            check = await client.evaluate("""
                (() => {
                    const popup = document.querySelector('.popup-overlay');
                    return !popup || popup.style.display === 'none';
                })()
            """)
            
            if check:
                print("✅ Modal closed!")
                await client.screenshot("modal_closed_found.png")
                return True
    
    # Last resort: try clicking in the icon area
    print("\nTrying to click in popup-icons area...")
    result = await client.evaluate("""
        (() => {
            const icons = document.querySelector('.popup-icons');
            if (icons) {
                const children = icons.children;
                // Try clicking the last child (usually the close button)
                if (children.length > 0) {
                    const lastIcon = children[children.length - 1];
                    lastIcon.click();
                    return true;
                }
            }
            return false;
        })()
    """)
    
    if result:
        await asyncio.sleep(0.5)
        check = await client.evaluate("""
            (() => {
                const popup = document.querySelector('.popup-overlay');
                return !popup || popup.style.display === 'none';
            })()
        """)
        
        if check:
            print("✅ Modal closed by clicking last icon!")
            return True
    
    print("❌ Could not close modal")
    return False

if __name__ == "__main__":
    asyncio.run(main())