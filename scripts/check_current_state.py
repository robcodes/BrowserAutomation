#!/usr/bin/env python3
"""Quick check of current page state"""
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
    
    # Take screenshot
    await client.screenshot("current_state.png")
    print("Screenshot saved: current_state.png")
    
    # Check state
    state = await client.evaluate("""
        (() => {
            const modals = document.querySelectorAll('.modal');
            const modalInfo = [];
            modals.forEach((m, i) => {
                const style = window.getComputedStyle(m);
                modalInfo.push({
                    index: i,
                    className: m.className,
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    offsetParent: m.offsetParent !== null
                });
            });
            
            return {
                modalCount: modals.length,
                modals: modalInfo,
                bodyText: document.body.textContent.slice(0, 200),
                hasWelcome: document.body.textContent.includes('Welcome'),
                url: window.location.href
            };
        })()
    """)
    
    print(f"\nPage URL: {state['url']}")
    print(f"Modal count: {state['modalCount']}")
    for modal in state['modals']:
        print(f"\nModal {modal['index']}:")
        print(f"  Class: {modal['className']}")
        print(f"  Display: {modal['display']}")
        print(f"  Visibility: {modal['visibility']}")
        print(f"  Has offsetParent: {modal['offsetParent']}")
    
    print(f"\nHas Welcome text: {state['hasWelcome']}")
    print(f"Body text preview: {state['bodyText']}")

if __name__ == "__main__":
    asyncio.run(main())