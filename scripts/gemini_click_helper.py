#!/usr/bin/env python3
"""
Helper script that uses Gemini Vision API to find and click elements
when traditional selectors fail.
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict
sys.path.append(str(Path(__file__).parent.parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from clients.gemini_detector import GeminiDetector
from PIL import Image

class GeminiClickHelper:
    def __init__(self, browser_client: EnhancedBrowserClient, gemini_api_key: str):
        self.client = browser_client
        self.detector = GeminiDetector(gemini_api_key)
        self.screenshot_dir = Path(__file__).parent.parent / "screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)
    
    async def click_element_by_description(self, 
                                         session_id: str, 
                                         page_id: str,
                                         element_description: str,
                                         screenshot_name: str = "gemini_detection.png") -> bool:
        """
        Take a screenshot, use Gemini to find an element, and click it
        
        Args:
            session_id: Browser session ID
            page_id: Page ID
            element_description: Natural language description of element
            screenshot_name: Name for the screenshot
            
        Returns:
            True if element was found and clicked
        """
        # Take screenshot
        screenshot_path = self.screenshot_dir / screenshot_name
        await self.client.screenshot(screenshot_name)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Use Gemini to find element
        print(f"Looking for: {element_description}")
        result = await self.detector.find_element(
            str(screenshot_path),
            element_description
        )
        
        print(f"Gemini response: {result['raw_response']}")
        
        if not result['coordinates']:
            print("No element found!")
            return False
        
        # Get image dimensions
        img = Image.open(screenshot_path)
        width, height = img.size
        
        # Convert coordinates to click position
        coords = result['coordinates'][0]  # Use first match
        click_pos = self.detector.convert_to_playwright_coords(
            coords, width, height
        )
        
        print(f"Found element at bounding box: {coords}")
        print(f"Clicking at position: {click_pos}")
        
        # Click using coordinates
        click_result = await self.client.evaluate(
            f"""
            (() => {{
                // Create and dispatch click event at coordinates
                const event = new MouseEvent('click', {{
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: {click_pos['x']},
                    clientY: {click_pos['y']}
                }});
                
                // Find element at coordinates
                const element = document.elementFromPoint({click_pos['x']}, {click_pos['y']});
                if (element) {{
                    element.dispatchEvent(event);
                    return {{
                        success: true,
                        clicked: element.tagName + (element.className ? '.' + element.className : ''),
                        text: element.textContent?.slice(0, 50)
                    }};
                }}
                return {{ success: false, reason: 'No element at coordinates' }};
            }})()
            """
        )
        
        print(f"Click result: {click_result}")
        
        if result['annotated_image_path']:
            print(f"Annotated image saved to: {result['annotated_image_path']}")
        
        return click_result.get('success', False)
    
    async def find_all_clickable_elements(self,
                                        session_id: str,
                                        page_id: str,
                                        screenshot_name: str = "all_elements.png") -> Dict:
        """Find all clickable elements in the current page"""
        screenshot_path = self.screenshot_dir / screenshot_name
        await self.client.screenshot(screenshot_name)
        
        result = await self.detector.detect_elements(
            str(screenshot_path),
            """Find ALL clickable elements including:
            - Buttons (including X/close buttons)
            - Links
            - Input fields
            - Dropdowns
            - Any interactive elements
            Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax]"""
        )
        
        print(f"Found {len(result['coordinates'])} clickable elements")
        if result['annotated_image_path']:
            print(f"See annotated image: {result['annotated_image_path']}")
        
        return result


# Example usage for closing the FuzzyCode modal
async def close_fuzzycode_modal_with_gemini():
    from scripts.fuzzycode_steps.common import load_session_info
    
    # Load session
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    # Initialize Gemini helper
    # API key: AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA
    # Model: gemini-2.5-flash
    helper = GeminiClickHelper(client, "YOUR_GEMINI_API_KEY")
    
    # Try to find and click the X button
    success = await helper.click_element_by_description(
        session_info['session_id'],
        session_info['page_id'],
        "X button or close button in the modal header",
        "modal_close_detection.png"
    )
    
    if success:
        print("Successfully clicked the close button!")
    else:
        print("Could not find or click the close button")


if __name__ == "__main__":
    print("Gemini Click Helper loaded. Requires API key to use.")
    # To test: asyncio.run(close_fuzzycode_modal_with_gemini())