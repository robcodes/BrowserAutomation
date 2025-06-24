#!/usr/bin/env python3
"""
Enhanced Gemini Click Helper with retry logic and manual corrections
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
sys.path.append(str(Path(__file__).parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from clients.gemini_detector import GeminiDetector
from PIL import Image

class EnhancedGeminiClickHelper:
    def __init__(self, browser_client: EnhancedBrowserClient, gemini_api_key: str):
        self.client = browser_client
        self.detector = GeminiDetector(gemini_api_key)
        self.screenshot_dir = Path(__file__).parent.parent / "screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)
    
    async def click_element_with_retry(self,
                                     session_id: str,
                                     page_id: str,
                                     element_description: str,
                                     max_attempts: int = 2,
                                     manual_corrections: Optional[List[Tuple[int, int]]] = None) -> bool:
        """
        Try to click element with retry logic and manual corrections
        
        Args:
            session_id: Browser session ID
            page_id: Page ID
            element_description: Natural language description
            max_attempts: Number of Gemini detection attempts
            manual_corrections: List of (x_offset, y_offset) to try if Gemini fails
            
        Returns:
            True if element was clicked successfully
        """
        screenshot_name = f"gemini_retry_{int(asyncio.get_event_loop().time())}.png"
        screenshot_path = self.screenshot_dir / screenshot_name
        
        # Take screenshot
        await self.client.screenshot(screenshot_name)
        print(f"Screenshot saved: {screenshot_path}")
        
        # Try Gemini detection multiple times
        for attempt in range(max_attempts):
            print(f"\nAttempt {attempt + 1} of {max_attempts}")
            print(f"Looking for: {element_description}")
            
            try:
                result = await self.detector.find_element(
                    str(screenshot_path),
                    element_description
                )
                
                print(f"Gemini response: {result['raw_response'][:200]}...")
                
                if result['coordinates']:
                    coords = result['coordinates'][0]
                    print(f"Found at: {coords}")
                    
                    # Try clicking
                    success = await self._try_click_at_coords(
                        screenshot_path, coords, f"attempt_{attempt + 1}"
                    )
                    
                    if success:
                        return True
                    else:
                        print("Click didn't work, trying different description...")
                        # Modify description for next attempt
                        if "X button" in element_description:
                            element_description = "the × (multiplication sign or X) symbol button for closing the modal, located in the top right corner"
                        elif "close button" in element_description:
                            element_description = "the button with an X or × symbol used to dismiss or close the dialog"
                else:
                    print("No coordinates found")
                    
            except Exception as e:
                print(f"Gemini error: {e}")
        
        # If Gemini fails, try manual corrections
        if manual_corrections:
            print("\nTrying manual corrections based on typical positions...")
            
            # Get the last detected coordinates or use a default
            base_coords = result.get('coordinates', [[50, 900, 70, 920]])[0] if 'result' in locals() else [50, 900, 70, 920]
            
            for i, (x_offset, y_offset) in enumerate(manual_corrections):
                print(f"\nManual correction {i + 1}: offset ({x_offset}, {y_offset})")
                
                # Adjust coordinates
                adjusted_coords = [
                    base_coords[0] + y_offset,  # ymin
                    base_coords[1] + x_offset,   # xmin
                    base_coords[2] + y_offset,   # ymax
                    base_coords[3] + x_offset    # xmax
                ]
                
                success = await self._try_click_at_coords(
                    screenshot_path, adjusted_coords, f"manual_{i + 1}"
                )
                
                if success:
                    return True
        
        return False
    
    async def _try_click_at_coords(self, 
                                 screenshot_path: Path,
                                 coords: List[int],
                                 attempt_name: str) -> bool:
        """Try clicking at specific coordinates and verify if it worked"""
        # Get image dimensions
        img = Image.open(screenshot_path)
        width, height = img.size
        
        # Convert coordinates
        click_pos = self.detector.convert_to_playwright_coords(coords, width, height)
        print(f"Clicking at: {click_pos}")
        
        # Click
        click_result = await self.client.evaluate(f"""
            (() => {{
                const element = document.elementFromPoint({click_pos['x']}, {click_pos['y']});
                if (element) {{
                    // Log what we're clicking
                    console.log('Clicking element:', element.tagName, element.className, element.textContent?.slice(0, 20));
                    
                    // Try multiple click methods
                    element.click();
                    element.dispatchEvent(new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: {click_pos['x']},
                        clientY: {click_pos['y']}
                    }}));
                    
                    return {{
                        success: true,
                        element: element.tagName + (element.className ? '.' + element.className : ''),
                        text: element.textContent?.slice(0, 50)
                    }};
                }}
                return {{ success: false, reason: 'No element at coordinates' }};
            }})()
        """)
        
        print(f"Click result: {click_result}")
        
        # Wait a bit
        await asyncio.sleep(0.5)
        
        # Check if modal is gone
        modal_check = await self.client.evaluate("""
            (() => {
                const modal = document.querySelector('.modal');
                const hasWelcome = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
                return {
                    modalGone: !modal || modal.offsetParent === null,
                    welcomeGone: !hasWelcome
                };
            })()
        """)
        
        success = modal_check['modalGone'] or modal_check['welcomeGone']
        print(f"Modal gone: {modal_check['modalGone']}, Welcome gone: {modal_check['welcomeGone']}")
        
        return success


async def close_fuzzycode_modal_smart():
    """Smart approach to closing the FuzzyCode modal"""
    from scripts.fuzzycode_steps.common import load_session_info, save_session_info
    
    # Load session
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    # Initialize enhanced helper
    helper = EnhancedGeminiClickHelper(client, "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA")
    
    # Try to close with retry and manual corrections
    # Based on the screenshot, the X is about 20-40 pixels to the right of where Gemini detected
    success = await helper.click_element_with_retry(
        session_info['session_id'],
        session_info['page_id'],
        "the X close button in the modal header, not the expand button",
        max_attempts=2,
        manual_corrections=[
            (40, 0),   # 40 pixels to the right
            (60, 0),   # 60 pixels to the right
            (20, -10), # 20 right, 10 up
            (40, -10), # 40 right, 10 up
        ]
    )
    
    if success:
        print("\n✅ Successfully closed the modal!")
        await save_session_info(session_info['session_id'], session_info['page_id'], 5)
    else:
        print("\n❌ Could not close the modal")
        # Last resort - try ESC key
        print("Trying ESC key as last resort...")
        await client.evaluate("""
            document.dispatchEvent(new KeyboardEvent('keydown', {
                key: 'Escape',
                code: 'Escape',
                keyCode: 27,
                bubbles: true
            }));
        """)
        
        await asyncio.sleep(0.5)
        
        final_check = await client.evaluate("""
            (() => {
                const modal = document.querySelector('.modal');
                return !modal || modal.offsetParent === null;
            })()
        """)
        
        if final_check:
            print("✅ ESC key worked!")
            await save_session_info(session_info['session_id'], session_info['page_id'], 5)
        else:
            print("❌ Even ESC didn't work")


if __name__ == "__main__":
    print("Enhanced Gemini Click Helper with retry logic")
    # asyncio.run(close_fuzzycode_modal_smart())