#!/usr/bin/env python3
"""Click with visual crosshair for debugging"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.fuzzycode_steps.common import *

async def click_with_crosshair(client, x, y, label=""):
    """Draw a crosshair at click position, take screenshot, then click"""
    
    # Inject crosshair
    await client.evaluate(f"""
        (() => {{
            // Remove any existing crosshair
            const existing = document.getElementById('debug-crosshair');
            if (existing) existing.remove();
            
            // Create crosshair container
            const crosshair = document.createElement('div');
            crosshair.id = 'debug-crosshair';
            crosshair.style.position = 'fixed';
            crosshair.style.left = '{x}px';
            crosshair.style.top = '{y}px';
            crosshair.style.width = '0';
            crosshair.style.height = '0';
            crosshair.style.zIndex = '999999';
            crosshair.style.pointerEvents = 'none';
            
            // Horizontal line
            const hLine = document.createElement('div');
            hLine.style.position = 'absolute';
            hLine.style.width = '40px';
            hLine.style.height = '2px';
            hLine.style.backgroundColor = 'red';
            hLine.style.left = '-20px';
            hLine.style.top = '-1px';
            hLine.style.boxShadow = '0 0 2px rgba(0,0,0,0.5)';
            
            // Vertical line
            const vLine = document.createElement('div');
            vLine.style.position = 'absolute';
            vLine.style.width = '2px';
            vLine.style.height = '40px';
            vLine.style.backgroundColor = 'red';
            vLine.style.left = '-1px';
            vLine.style.top = '-20px';
            vLine.style.boxShadow = '0 0 2px rgba(0,0,0,0.5)';
            
            // Center dot
            const dot = document.createElement('div');
            dot.style.position = 'absolute';
            dot.style.width = '6px';
            dot.style.height = '6px';
            dot.style.backgroundColor = 'yellow';
            dot.style.border = '1px solid red';
            dot.style.borderRadius = '50%';
            dot.style.left = '-3px';
            dot.style.top = '-3px';
            
            // Label
            const labelDiv = document.createElement('div');
            labelDiv.style.position = 'absolute';
            labelDiv.style.left = '10px';
            labelDiv.style.top = '10px';
            labelDiv.style.backgroundColor = 'yellow';
            labelDiv.style.color = 'black';
            labelDiv.style.padding = '2px 5px';
            labelDiv.style.fontSize = '12px';
            labelDiv.style.fontWeight = 'bold';
            labelDiv.style.border = '1px solid red';
            labelDiv.textContent = '{label} ({x}, {y})';
            
            crosshair.appendChild(hLine);
            crosshair.appendChild(vLine);
            crosshair.appendChild(dot);
            crosshair.appendChild(labelDiv);
            document.body.appendChild(crosshair);
        }})()
    """)
    
    # Wait a bit for rendering
    await asyncio.sleep(0.2)
    
    # Take screenshot with crosshair
    screenshot_name = f"crosshair_{label.replace(' ', '_')}_{x}_{y}.png"
    await client.screenshot(screenshot_name)
    print(f"📸 Screenshot saved: {screenshot_name}")
    
    # Now click at that position
    await client.evaluate(f"""
        (() => {{
            const element = document.elementFromPoint({x}, {y});
            console.log('Element at crosshair:', element ? element.tagName + '.' + element.className : 'none');
            
            if (element) {{
                element.click();
                // Also dispatch event
                element.dispatchEvent(new MouseEvent('click', {{
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: {x},
                    clientY: {y}
                }}));
            }}
            
            // Remove crosshair after click
            const crosshair = document.getElementById('debug-crosshair');
            if (crosshair) crosshair.remove();
        }})()
    """)

async def main():
    # Load session
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    print("Testing click positions with visual crosshairs...")
    
    # Based on the Gemini annotated image, try these positions
    positions = [
        (1199, 55, "X_button_center"),  # Center of detected X button
        (1190, 55, "X_button_left"),    # Slightly left
        (1208, 55, "X_button_right"),   # Slightly right
        (1175, 40, "Top_left_of_X"),    # Top-left corner
        (1223, 40, "Top_right_corner"), # Far top-right
    ]
    
    for x, y, label in positions:
        print(f"\n{label}: Clicking at ({x}, {y})")
        
        # Draw crosshair and click
        await click_with_crosshair(client, x, y, label)
        
        # Wait and check
        await asyncio.sleep(0.5)
        
        # Check if modal is gone
        modal_check = await client.evaluate("""
            (() => {
                const popup = document.querySelector('.popup-overlay');
                const hasWelcome = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
                return {
                    popupVisible: popup && popup.style.display !== 'none',
                    welcomeVisible: hasWelcome,
                    popupDisplay: popup ? popup.style.display : 'not found'
                };
            })()
        """)
        
        print(f"  Popup visible: {modal_check['popupVisible']} (display: {modal_check['popupDisplay']})")
        print(f"  Welcome visible: {modal_check['welcomeVisible']}")
        
        if not modal_check['popupVisible'] and not modal_check['welcomeVisible']:
            print("✅ Modal successfully closed!")
            await client.screenshot("modal_closed_success.png")
            return True
    
    # If none worked, try finding the popup-icons div
    print("\nLooking for popup-icons structure...")
    icons_info = await client.evaluate("""
        (() => {
            const icons = document.querySelector('.popup-icons');
            if (!icons) return null;
            
            const children = [];
            for (let i = 0; i < icons.children.length; i++) {
                const child = icons.children[i];
                const rect = child.getBoundingClientRect();
                children.push({
                    index: i,
                    tagName: child.tagName,
                    className: child.className,
                    innerHTML: child.innerHTML.substring(0, 50),
                    x: Math.round(rect.left + rect.width/2),
                    y: Math.round(rect.top + rect.height/2),
                    visible: child.offsetParent !== null
                });
            }
            return children;
        })()
    """)
    
    if icons_info:
        print(f"\nFound {len(icons_info)} icons in popup-icons:")
        for icon in icons_info:
            print(f"  Icon {icon['index']}: {icon['tagName']} at ({icon['x']}, {icon['y']})")
        
        # Click the last one (usually close button)
        if icons_info:
            last_icon = icons_info[-1]
            print(f"\nClicking last icon at ({last_icon['x']}, {last_icon['y']})")
            await click_with_crosshair(client, last_icon['x'], last_icon['y'], "last_icon")
    
    print("\n❌ Could not close modal with any position")
    return False

if __name__ == "__main__":
    asyncio.run(main())