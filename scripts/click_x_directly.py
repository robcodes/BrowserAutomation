#!/usr/bin/env python3
"""Click the X button directly based on known position"""
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
    
    print("Clicking X button at known position...")
    
    # Based on the annotated image, the X button is around x=1199, y=55
    # Try clicking there
    click_x = 1199
    click_y = 55
    
    print(f"Clicking at x={click_x}, y={click_y}")
    await client.evaluate(f"""
        (() => {{
            // Create and dispatch click event
            const event = new MouseEvent('click', {{
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: {click_x},
                clientY: {click_y}
            }});
            
            // Find element at position and click
            const element = document.elementFromPoint({click_x}, {click_y});
            if (element) {{
                console.log('Clicking element:', element.tagName, element.className);
                element.click();
                element.dispatchEvent(event);
            }}
        }})()
    """)
    
    await asyncio.sleep(1)
    
    # Check if modal is gone
    modal_check = await client.evaluate("""
        (() => {
            const popup = document.querySelector('.popup-overlay');
            const hasWelcome = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
            return {
                popupVisible: popup && popup.style.display !== 'none',
                welcomeVisible: hasWelcome
            };
        })()
    """)
    
    print(f"Popup visible: {modal_check['popupVisible']}")
    print(f"Welcome visible: {modal_check['welcomeVisible']}")
    
    if not modal_check['popupVisible'] and not modal_check['welcomeVisible']:
        print("✅ Modal successfully closed!")
        await client.screenshot("modal_closed_direct.png")
        return True
    else:
        print("❌ Modal still visible")
        # Try alternate positions
        for offset_x, offset_y in [(0, 0), (-10, 0), (10, 0), (0, -10), (0, 10)]:
            click_x_alt = 1199 + offset_x
            click_y_alt = 55 + offset_y
            print(f"Trying offset position: x={click_x_alt}, y={click_y_alt}")
            
            await client.evaluate(f"""
                document.elementFromPoint({click_x_alt}, {click_y_alt}).click();
            """)
            
            await asyncio.sleep(0.5)
            
            check = await client.evaluate("""
                (() => {
                    const popup = document.querySelector('.popup-overlay');
                    return !popup || popup.style.display === 'none';
                })()
            """)
            
            if check:
                print("✅ Modal closed with offset click!")
                return True
        
        return False

if __name__ == "__main__":
    asyncio.run(main())