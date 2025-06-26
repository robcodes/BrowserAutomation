#!/usr/bin/env python3
"""
Improved Gemini element matcher using crosshairs instead of bounding boxes.
This approach draws numbered crosshairs at element centers for better identification.
"""
from pathlib import Path
import sys
import base64
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

sys.path.append(str(Path(__file__).parent.parent.parent))

from clients.gemini_detector import GeminiDetector


class GeminiCrosshairMatcher:
    def __init__(self, api_key: str):
        self.detector = GeminiDetector(api_key)
        
    def _draw_crosshair(self, draw: ImageDraw.Draw, x: int, y: int, 
                       number: int, size: int = 20, thickness: int = 2,
                       color: str = "red", text_color: str = "yellow"):
        """Draw a crosshair at the specified position with a number label"""
        # Draw horizontal line
        draw.line([(x - size, y), (x + size, y)], fill=color, width=thickness)
        # Draw vertical line
        draw.line([(x, y - size), (x, y + size)], fill=color, width=thickness)
        
        # Draw center dot
        dot_size = 3
        draw.ellipse([(x - dot_size, y - dot_size), (x + dot_size, y + dot_size)], 
                     fill="yellow", outline=color, width=1)
        
        # Draw number label
        # Try to get a font, fall back to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Draw text with background for better visibility
        text = str(number)
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position text offset from crosshair
        text_x = x + size + 5
        text_y = y - text_height // 2
        
        # Draw background rectangle
        padding = 3
        draw.rectangle(
            [(text_x - padding, text_y - padding), 
             (text_x + text_width + padding, text_y + text_height + padding)],
            fill="black"
        )
        
        # Draw text
        draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    def _create_crosshair_image(self, image_path: str, coordinates: List[List[int]], 
                               output_path: Optional[str] = None) -> str:
        """Create an image with numbered crosshairs at element centers"""
        # Open image
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # Draw crosshairs for each element
        for idx, coords in enumerate(coordinates):
            ymin, xmin, ymax, xmax = coords
            
            # Convert from 1000-scale to actual pixels and find center
            center_x = int((xmin + xmax) / 2 * img.width / 1000)
            center_y = int((ymin + ymax) / 2 * img.height / 1000)
            
            # Draw crosshair with number (1-indexed for user clarity)
            self._draw_crosshair(draw, center_x, center_y, idx + 1)
        
        # Save the crosshair image
        if output_path is None:
            base_path = Path(image_path)
            output_path = base_path.parent / f"{base_path.stem}_crosshairs{base_path.suffix}"
        
        img.save(output_path)
        return str(output_path)
    
    async def find_element_with_crosshairs(self, screenshot_path: str, 
                                          element_description: str) -> Optional[Dict]:
        """
        Find an element using the crosshair approach:
        1. Detect all elements
        2. Draw numbered crosshairs at their centers
        3. Ask Gemini which crosshair number matches the description
        """
        
        # Step 1: Find all elements
        print("Step 1: Detecting all elements...")
        all_elements = await self.detector.detect_elements(
            screenshot_path,
            """Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for ALL:
            - Clickable elements (buttons, links, icons)
            - Input fields and form elements
            - Close/X buttons and modal controls
            - Any interactive UI elements
            Be comprehensive - include everything that looks clickable.""",
            save_annotated=False  # We'll create our own visualization
        )
        
        if not all_elements['coordinates']:
            print("No elements found in the image")
            return None
        
        print(f"Found {len(all_elements['coordinates'])} elements")
        
        # Step 2: Create crosshair image
        print("Step 2: Creating crosshair visualization...")
        crosshair_image_path = self._create_crosshair_image(
            screenshot_path, 
            all_elements['coordinates']
        )
        print(f"Crosshair image saved to: {crosshair_image_path}")
        
        # Step 3: Ask Gemini to identify the correct crosshair
        print(f"\nStep 3: Asking Gemini to identify: '{element_description}'")
        
        identification_prompt = f"""Look at this image with numbered crosshairs marking different UI elements.

I need to find: {element_description}

Each crosshair has a number next to it. Examine the UI element at each crosshair position carefully.

Return ONLY the number of the crosshair that marks the {element_description}.
- If you find it, return just the number (e.g., "5")
- If none match, return "NONE"
- If multiple could match, return the most likely one

Just the number or "NONE", nothing else."""
        
        # Send the crosshair image to Gemini
        match_result = await self.detector.detect_elements(
            crosshair_image_path,
            identification_prompt,
            save_annotated=False
        )
        
        # Parse the response
        response_text = match_result.get('raw_response', '').strip()
        print(f"Gemini response: '{response_text}'")
        
        if not response_text or response_text.upper() == "NONE":
            print("No matching element found")
            return None
        
        try:
            # Convert response to index (1-indexed to 0-indexed)
            crosshair_number = int(response_text)
            element_index = crosshair_number - 1
            
            if 0 <= element_index < len(all_elements['coordinates']):
                coords = all_elements['coordinates'][element_index]
                ymin, xmin, ymax, xmax = coords
                
                # Get image dimensions for proper scaling
                img = Image.open(screenshot_path)
                
                # Calculate center position
                center_x = int((xmin + xmax) / 2 * img.width / 1000)
                center_y = int((ymin + ymax) / 2 * img.height / 1000)
                
                print(f"✓ Identified crosshair #{crosshair_number} at ({center_x}, {center_y})")
                
                return {
                    'crosshair_number': crosshair_number,
                    'element_index': element_index,
                    'coordinates': coords,
                    'center': (center_x, center_y),
                    'crosshair_image': crosshair_image_path
                }
            else:
                print(f"Invalid crosshair number: {crosshair_number}")
                return None
                
        except ValueError:
            print(f"Could not parse Gemini's response: '{response_text}'")
            return None


# Helper function for browser automation
async def click_element_with_crosshairs(client, element_description: str, 
                                       api_key: str, screenshot_name: str = "crosshair_search.png"):
    """
    Use crosshair matching to find and click an element
    
    Args:
        client: Browser client instance
        element_description: Natural language description of element
        api_key: Gemini API key
        screenshot_name: Name for the screenshot
    
    Returns:
        True if element was found and clicked, False otherwise
    """
    # Take screenshot
    await client.screenshot(screenshot_name)
    screenshot_path = f"/home/ubuntu/browser_automation/screenshots/{screenshot_name}"
    
    # Initialize matcher
    matcher = GeminiCrosshairMatcher(api_key)
    
    # Find element using crosshairs
    element = await matcher.find_element_with_crosshairs(screenshot_path, element_description)
    
    if not element:
        print(f"Could not find: {element_description}")
        return False
    
    # Click at the center position
    x, y = element['center']
    await client.click_at(x=x, y=y, label=f"crosshair_{element['crosshair_number']}")
    
    print(f"Clicked element at crosshair #{element['crosshair_number']} ({x}, {y})")
    return True