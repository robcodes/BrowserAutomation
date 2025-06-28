#!/usr/bin/env python3
"""
Use Gemini to match elements to descriptions
"""
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from clients.gemini_detector import GeminiDetector

async def find_element_by_description(screenshot_path, description, api_key):
    """
    First detect all elements, then ask Gemini which one matches the description
    """
    detector = GeminiDetector(api_key)
    
    # Step 1: Find all elements
    print("Step 1: Finding all elements...")
    all_elements = await detector.detect_elements(
        screenshot_path,
        "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for ALL clickable elements, buttons, inputs, links, icons, text fields, form elements.",
        save_annotated=True
    )
    
    if not all_elements['coordinates']:
        return None
    
    print(f"Found {len(all_elements['coordinates'])} elements")
    
    # Step 2: Ask Gemini which element matches our description
    print(f"\nStep 2: Asking Gemini to identify: '{description}'")
    
    # Create a prompt that includes all the annotated boxes
    matching_prompt = f"""
Look at the annotated image with numbered bounding boxes. 
I need to find: {description}

Examine each numbered box carefully. Return ONLY the box number that best matches this description.
If no box matches, return "NO_MATCH".
If multiple boxes could match, return the most likely one.

Just return the number (e.g., "7") or "NO_MATCH". Nothing else.
"""
    
    # Use the annotated image that was created
    annotated_path = screenshot_path.replace('.png', '_annotated.png')
    
    # Send a second request to Gemini with the annotated image
    match_result = await detector.detect_elements(
        annotated_path,
        matching_prompt,
        save_annotated=False  # Don't re-annotate
    )
    
    # Extract the response text
    response_text = match_result.get('raw_response', '').strip()
    
    if not response_text or response_text == "NO_MATCH":
        print("No matching element found")
        return None
    
    try:
        # Gemini returns box numbers starting from 1, but our array is 0-indexed
        box_number = int(response_text) - 1
        if 0 <= box_number < len(all_elements['coordinates']):
            coords = all_elements['coordinates'][box_number]
            ymin, xmin, ymax, xmax = coords
            
            # Get image dimensions for proper coordinate normalization
            from PIL import Image
            img = Image.open(screenshot_path)
            width, height = img.size
            
            # Normalize coordinates (divide by 1000 and multiply by image dimensions)
            center_x = int(((xmin + xmax) / 2) / 1000 * width)
            center_y = int(((ymin + ymax) / 2) / 1000 * height)
            
            print(f"✓ Gemini identified box {box_number + 1} at ({center_x}, {center_y})")
            return {
                'box_number': box_number,
                'coordinates': coords,
                'center': (center_x, center_y)
            }
    except:
        print(f"Could not parse Gemini's response: {response_text}")
    
    return None

# Example usage function
async def click_element_by_description(client, description, api_key):
    """
    Take screenshot, find element by description, and click it
    """
    # Take screenshot
    screenshot_name = "element_search.png"
    await client.screenshot(screenshot_name)
    screenshot_path = f"/home/ubuntu/browser_automation/screenshots/{screenshot_name}"
    
    # Find the element
    element = await find_element_by_description(screenshot_path, description, api_key)
    
    if not element:
        print(f"Could not find: {description}")
        return False
    
    # Click it
    x, y = element['center']
    await client.click_at(x=x, y=y, label=description.replace(' ', '_'))
    
    return True