#!/usr/bin/env python3
"""Find the actual modal that's visible"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from scripts.fuzzycode_steps.common import load_session_info

async def main():
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    # Find all potential modal elements
    modal_info = await client.evaluate("""
        (() => {
            const selectors = [
                '.modal',
                '.popup',
                '.popup-overlay',
                '.popup-content',
                '[role="dialog"]',
                '.dialog',
                '.overlay',
                '[class*="modal"]',
                '[class*="popup"]'
            ];
            
            const elements = [];
            
            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    
                    if (style.display !== 'none' && rect.width > 0 && rect.height > 0) {
                        elements.push({
                            selector: selector,
                            className: el.className,
                            tagName: el.tagName,
                            display: style.display,
                            visibility: style.visibility,
                            position: style.position,
                            zIndex: style.zIndex,
                            width: rect.width,
                            height: rect.height,
                            hasWelcome: el.textContent.includes('Welcome'),
                            hasUserLogin: el.textContent.includes('User Login'),
                            textPreview: el.textContent.slice(0, 100).replace(/\\s+/g, ' ').trim()
                        });
                    }
                });
            });
            
            return elements;
        })()
    """)
    
    print("Found visible modal-like elements:")
    for i, el in enumerate(modal_info):
        if el['hasWelcome'] or el['hasUserLogin']:
            print(f"\n=== Element {i} (LIKELY THE MODAL) ===")
        else:
            print(f"\n--- Element {i} ---")
        print(f"Selector: {el['selector']}")
        print(f"Class: {el['className']}")
        print(f"Tag: {el['tagName']}")
        print(f"Display: {el['display']}")
        print(f"Position: {el['position']}")
        print(f"Z-index: {el['zIndex']}")
        print(f"Size: {el['width']}x{el['height']}")
        print(f"Has Welcome: {el['hasWelcome']}")
        print(f"Has User Login: {el['hasUserLogin']}")
        print(f"Text: {el['textPreview']}")

if __name__ == "__main__":
    asyncio.run(main())