#!/usr/bin/env python3
"""
Example: Using Gemini Vision to close modal dialogs
This is particularly useful when modal close buttons have:
- No good CSS selectors
- Dynamic classes
- Are visually obvious but programmatically difficult to target
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from clients.gemini_detector import GeminiDetector
from PIL import Image

# API Configuration
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"  # Replace with your key

async def close_modal_with_gemini(client: EnhancedBrowserClient, 
                                 session_id: str, 
                                 page_id: str):
    """
    Example of closing a modal using Gemini Vision
    """
    # Take screenshot
    screenshot_path = Path(__file__).parent.parent.parent / "screenshots" / "modal_detection.png"
    await client.screenshot("modal_detection.png")
    print(f"Screenshot saved: {screenshot_path}")
    
    # Initialize Gemini detector
    detector = GeminiDetector(GEMINI_API_KEY)
    
    # Find the close button
    print("\nLooking for modal close button...")
    result = await detector.find_element(
        str(screenshot_path),
        "close button (X or × symbol) in the modal dialog, typically in the top-right corner"
    )
    
    print(f"\nGemini response: {result['raw_response']}")
    
    if not result['coordinates']:
        print("❌ No close button found")
        return False
    
    # Get image dimensions for coordinate conversion
    img = Image.open(screenshot_path)
    width, height = img.size
    
    # Convert to click coordinates
    coords = result['coordinates'][0]
    click_pos = detector.convert_to_playwright_coords(coords, width, height)
    
    print(f"\nFound close button at: {coords}")
    print(f"Clicking at position: x={click_pos['x']}, y={click_pos['y']}")
    
    # Click the button
    click_result = await client.evaluate(
        session_id,
        page_id,
        f"""
        (() => {{
            // Create click event at the detected coordinates
            const event = new MouseEvent('click', {{
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: {click_pos['x']},
                clientY: {click_pos['y']}
            }});
            
            // Find and click element at coordinates
            const element = document.elementFromPoint({click_pos['x']}, {click_pos['y']});
            if (element) {{
                console.log('Clicking element:', element);
                element.dispatchEvent(event);
                
                // Also try direct click method
                if (typeof element.click === 'function') {{
                    element.click();
                }}
                
                return {{
                    success: true,
                    element: {{
                        tag: element.tagName,
                        classes: element.className,
                        text: element.textContent?.slice(0, 30)
                    }}
                }};
            }}
            return {{ success: false, reason: 'No element at coordinates' }};
        }})()
        """
    )
    
    print(f"\nClick result: {click_result}")
    
    if result['annotated_image_path']:
        print(f"Annotated image saved: {result['annotated_image_path']}")
    
    return click_result.get('success', False)

async def main():
    """
    Complete example of modal handling with Gemini
    """
    # This example assumes you have a page with a modal open
    # Adjust the URL and modal trigger as needed
    
    client = EnhancedBrowserClient()
    session_id = await client.create_session(headless=False)
    
    # Navigate to a page with a modal (example)
    page_id = await client.new_page("https://getbootstrap.com/docs/4.0/components/modal/")
    
    # Trigger a modal (Bootstrap example)
    await client.evaluate(
        session_id,
        page_id,
        """
        // Find and click the demo modal button
        const button = document.querySelector('[data-target="#exampleModal"]');
        if (button) button.click();
        """
    )
    
    # Wait for modal to appear
    await asyncio.sleep(1)
    
    # Try to close it with Gemini
    success = await close_modal_with_gemini(client, session_id, page_id)
    
    if success:
        print("\n✅ Modal closed successfully!")
        
        # Verify modal is gone
        await asyncio.sleep(0.5)
        modal_check = await client.evaluate(
            session_id,
            page_id,
            """
            (() => {
                const modal = document.querySelector('.modal.show');
                return { modalVisible: modal !== null };
            })()
            """
        )
        print(f"Modal still visible: {modal_check['modalVisible']}")
    else:
        print("\n❌ Failed to close modal")

if __name__ == "__main__":
    asyncio.run(main())