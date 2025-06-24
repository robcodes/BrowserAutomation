#!/usr/bin/env python3
"""Debug what's on the page"""
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
    
    # Debug what's on the page
    debug_info = await client.evaluate("""
        (() => {
            const allDivs = document.querySelectorAll('div');
            const popupClasses = [];
            const modalClasses = [];
            
            allDivs.forEach(div => {
                const classes = div.className;
                if (classes.includes('popup') || classes.includes('modal') || classes.includes('overlay')) {
                    if (classes.includes('popup')) popupClasses.push(classes);
                    if (classes.includes('modal')) modalClasses.push(classes);
                }
            });
            
            // Check specific selectors
            const selectors = [
                '.popup-overlay',
                '.modal',
                '.modal-content',
                '.popup',
                '[role="dialog"]',
                '.overlay'
            ];
            
            const found = {};
            selectors.forEach(sel => {
                const el = document.querySelector(sel);
                found[sel] = el ? {
                    exists: true,
                    visible: el.offsetParent !== null,
                    display: window.getComputedStyle(el).display,
                    className: el.className
                } : { exists: false };
            });
            
            return {
                popupClasses: popupClasses.slice(0, 5),
                modalClasses: modalClasses.slice(0, 5),
                welcomeText: document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!'),
                selectors: found,
                bodyClasses: document.body.className
            };
        })()
    """)
    
    print("DEBUG INFO:")
    print(f"Welcome text visible: {debug_info['welcomeText']}")
    print(f"Body classes: {debug_info['bodyClasses']}")
    print(f"\nPopup classes found: {debug_info['popupClasses']}")
    print(f"Modal classes found: {debug_info['modalClasses']}")
    print("\nSelector results:")
    for sel, info in debug_info['selectors'].items():
        if info['exists']:
            print(f"  {sel}: exists={info['exists']}, visible={info['visible']}, display={info['display']}")

if __name__ == "__main__":
    asyncio.run(main())