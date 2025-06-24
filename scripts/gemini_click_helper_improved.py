#!/usr/bin/env python3
"""
Improved Gemini Click Helper that uses the "find all elements" approach
for better accuracy when looking for specific elements
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional
sys.path.append(str(Path(__file__).parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from clients.gemini_detector import GeminiDetector
from PIL import Image

class ImprovedGeminiClickHelper:
    def __init__(self, browser_client: EnhancedBrowserClient, gemini_api_key: str):
        self.client = browser_client
        self.detector = GeminiDetector(gemini_api_key)
        self.screenshot_dir = Path(__file__).parent.parent / "screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)
    
    async def click_element_by_finding_all(self,
                                         session_id: str,
                                         page_id: str,
                                         element_description: str,
                                         screenshot_name: str = "gemini_find_all.png") -> bool:
        """
        Find element by first detecting ALL elements, then selecting the right one
        This approach has shown better accuracy than targeting a single element
        
        Args:
            session_id: Browser session ID
            page_id: Page ID
            element_description: What element we're looking for
            screenshot_name: Name for the screenshot
            
        Returns:
            True if element was found and clicked
        """
        # Take screenshot
        screenshot_path = self.screenshot_dir / screenshot_name
        await self.client.screenshot(screenshot_name)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # First, find ALL clickable elements
        print("\n1. Finding ALL clickable elements in the page...")
        result = await self.detector.detect_elements(
            str(screenshot_path),
            """Find ALL clickable elements including:
            - ALL buttons (especially close/X buttons and expand/fullscreen buttons)
            - Links
            - Interactive icons
            - Any element that looks clickable
            Label each element clearly. For buttons with symbols, describe the symbol (X, ×, expand icon, etc).
            Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax]"""
        )
        
        print(f"Found {len(result['coordinates'])} clickable elements")
        
        if result['annotated_image_path']:
            print(f"Check annotated image: {result['annotated_image_path']}")
        
        # Now ask Gemini which element matches our description
        if result['coordinates']:
            print(f"\n2. Asking Gemini to identify which element is: {element_description}")
            
            # Build a prompt with the coordinates
            identify_prompt = f"""Given these detected elements with their bounding boxes:
            {[f"Element {i+1}: {coords}" for i, coords in enumerate(result['coordinates'])]}
            
            Which element number (1-{len(result['coordinates'])}) is the {element_description}?
            
            Important: 
            - Look for the X or × symbol for close buttons
            - Distinguish between close (X) and expand/fullscreen buttons
            - Consider position (close buttons are usually in top-right)
            
            Return ONLY the element number."""
            
            # Ask Gemini to identify the right element
            identify_result = await self.detector.detect_elements(
                str(screenshot_path),
                identify_prompt,
                save_annotated=False
            )
            
            # Extract element number from response
            import re
            numbers = re.findall(r'\b(\d+)\b', identify_result['raw_response'])
            if numbers:
                element_idx = int(numbers[0]) - 1  # Convert to 0-based index
                
                if 0 <= element_idx < len(result['coordinates']):
                    target_coords = result['coordinates'][element_idx]
                    print(f"Selected Element {element_idx + 1} at: {target_coords}")
                    
                    # Get image dimensions
                    img = Image.open(screenshot_path)
                    width, height = img.size
                    
                    # Convert to click position
                    click_pos = self.detector.convert_to_playwright_coords(
                        target_coords, width, height
                    )
                    
                    print(f"Clicking at position: {click_pos}")
                    
                    # Click
                    click_result = await self.client.evaluate(f"""
                        (() => {{
                            const element = document.elementFromPoint({click_pos['x']}, {click_pos['y']});
                            if (element) {{
                                console.log('Clicking:', element);
                                element.click();
                                return {{
                                    success: true,
                                    element: element.tagName + (element.className ? '.' + element.className : ''),
                                    text: element.textContent?.slice(0, 50)
                                }};
                            }}
                            return {{ success: false }};
                        }})()
                    """)
                    
                    print(f"Click result: {click_result}")
                    
                    # Verify the action worked
                    await asyncio.sleep(1)
                    
                    # Take screenshot after click
                    after_screenshot = f"{screenshot_name.replace('.png', '')}_after.png"
                    await self.client.screenshot(after_screenshot)
                    print(f"After-click screenshot: {after_screenshot}")
                    
                    return click_result.get('success', False)
        
        return False


async def test_improved_approach():
    """Test the improved approach on FuzzyCode modal"""
    from scripts.fuzzycode_steps.common import load_session_info, save_session_info
    
    # Load session
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    # Check current state
    print("Checking current page state...")
    modal_check = await client.evaluate("""
        (() => {
            // Check for both .modal and .popup-overlay elements
            const modal = document.querySelector('.modal');
            const popup = document.querySelector('.popup-overlay');
            const hasWelcome = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
            const userLoginText = document.body.textContent.includes('User Login');
            
            // Check if popup is visible
            let popupVisible = false;
            if (popup) {
                const style = window.getComputedStyle(popup);
                popupVisible = style.display !== 'none' && style.visibility !== 'hidden';
            }
            
            return {
                modalVisible: (modal && modal.offsetParent !== null) || popupVisible,
                hasWelcome: hasWelcome,
                hasUserLogin: userLoginText,
                popupClass: popup ? popup.className : 'not found'
            };
        })()
    """)
    
    print(f"Modal visible: {modal_check['modalVisible']}")
    print(f"Has welcome text: {modal_check['hasWelcome']}")
    print(f"Has User Login text: {modal_check['hasUserLogin']}")
    print(f"Popup class: {modal_check['popupClass']}")
    
    if not (modal_check['modalVisible'] or modal_check['hasWelcome']):
        print("No modal to close!")
        return
    
    # Use improved helper
    helper = ImprovedGeminiClickHelper(client, "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA")
    
    success = await helper.click_element_by_finding_all(
        session_info['session_id'],
        session_info['page_id'],
        "X close button (not the expand/fullscreen button)",
        "improved_modal_close.png"
    )
    
    if success:
        # Verify modal is actually gone
        final_check = await client.evaluate("""
            (() => {
                const modal = document.querySelector('.modal');
                return {
                    modalGone: !modal || modal.offsetParent === null
                };
            })()
        """)
        
        if final_check['modalGone']:
            print("\n✅ VERIFIED: Modal is actually closed!")
            await save_session_info(session_info['session_id'], session_info['page_id'], 5)
        else:
            print("\n❌ VERIFICATION FAILED: Modal is still visible!")
    else:
        print("\n❌ Click failed")


if __name__ == "__main__":
    asyncio.run(test_improved_approach())