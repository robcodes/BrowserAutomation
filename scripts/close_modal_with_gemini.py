#!/usr/bin/env python3
"""Close the modal using Gemini with the improved prompt"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.fuzzycode_steps.common import *
from clients.gemini_detector import GeminiDetector

GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def main():
    # Load session
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    # Take screenshot
    screenshot_path = "/home/ubuntu/browser_automation/screenshots/modal_to_close.png"
    await client.screenshot("modal_to_close.png")
    
    # Use Gemini with improved prompt
    detector = GeminiDetector(GEMINI_API_KEY)
    
    print("Finding all clickable elements with improved prompt...")
    result = await detector.detect_elements(
        screenshot_path,
        "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc",
        save_annotated=True
    )
    
    print(f"Found {len(result['coordinates'])} elements")
    
    # Look for X button in top-right
    print("\nAll detected elements:")
    for i, coords in enumerate(result['coordinates']):
        ymin, xmin, ymax, xmax = coords
        center_x = int((xmin + xmax) / 2)
        center_y = int((ymin + ymax) / 2)
        print(f"Element {i+1}: {coords} - Center: x={center_x}, y={center_y}")
    
    print("\nLooking for X button in top-right area...")
    for i, coords in enumerate(result['coordinates']):
        ymin, xmin, ymax, xmax = coords
        if xmin > 900 and ymin < 100:  # Broader search area
            center_x = int((xmin + xmax) / 2)
            center_y = int((ymin + ymax) / 2)
            print(f"Element {i+1}: {coords} - Center: x={center_x}, y={center_y}")
            
            # Click it
            print(f"Clicking at x={center_x}, y={center_y}")
            await client.evaluate(f"""
                (() => {{
                    const event = new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: {center_x},
                        clientY: {center_y}
                    }});
                    document.elementFromPoint({center_x}, {center_y}).dispatchEvent(event);
                }})()
            """)
            
            await asyncio.sleep(1)
            
            # Check if modal is gone
            modal_check = await client.evaluate("""
                (() => {
                    const popup = document.querySelector('.popup-overlay');
                    const hasWelcome = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
                    return {
                        popupGone: !popup || popup.style.display === 'none',
                        welcomeGone: !hasWelcome
                    };
                })()
            """)
            
            if modal_check['popupGone'] and modal_check['welcomeGone']:
                print("✅ Modal successfully closed!")
                await client.screenshot("modal_closed.png")
                return True
            else:
                print("Modal still visible, trying next element...")
    
    print("❌ Could not find X button in expected area")
    return False

if __name__ == "__main__":
    asyncio.run(main())