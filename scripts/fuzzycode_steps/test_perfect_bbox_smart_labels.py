#!/usr/bin/env python3
"""
Uses the modular bbox_visualizer to test perfect bounding box positioning
with smart label placement and thin crosshairs. Saves JSON responses.
"""

import asyncio
import json
import base64
import aiohttp
from datetime import datetime
from pathlib import Path
from bbox_visualizer import visualize_bboxes, visualize_crosshairs

# Configuration
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"
SCREENSHOT_PATH = "/home/ubuntu/browser_automation/screenshots/element_search.png"
OUTPUT_DIR = "/home/ubuntu/browser_automation/screenshots/"

# Exact prompt from bb_detector.html
PROMPT = "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc"


async def test_gemini_detection(run_number):
    """Test Gemini detection with smart label placement"""
    print(f"\n=== Run {run_number} ===")
    
    # Use direct API call
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # Load and prepare the image
    with open(SCREENSHOT_PATH, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    # Create payload
    payload = {
        "contents": [{
            "parts": [
                {"text": PROMPT},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_data
                    }
                }
            ]
        }]
    }
    
    # Send to Gemini
    print(f"Sending to Gemini with prompt: {PROMPT}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
    
    # Save the JSON response
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = Path(OUTPUT_DIR) / f"gemini_response_run{run_number}_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Saved JSON response: {json_path}")
    
    # Extract the text response
    try:
        text = result['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        print(f"Unexpected API response: {result}")
        return
        
    print(f"Gemini response preview: {text[:200]}...")
    
    # Extract coordinates using regex
    import re
    regex = r'\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]'
    matches = re.findall(regex, text)
    coordinates = [json.loads(match) for match in matches]
    print(f"Found {len(coordinates)} bounding boxes")
    
    if coordinates:
        # Create output paths with timestamps
        bbox_output = Path(OUTPUT_DIR) / f"run{run_number}_smart_bboxes_{int(datetime.now().timestamp())}.png"
        crosshair_output = Path(OUTPUT_DIR) / f"run{run_number}_smart_crosshairs_{int(datetime.now().timestamp())}.png"
        
        # Draw bounding boxes with smart labels using the visualizer
        bbox_path = visualize_bboxes(
            SCREENSHOT_PATH, 
            json_data=result,  # Pass the full API response
            output_path=str(bbox_output)
        )
        print(f"Saved bounding boxes: {bbox_path}")
        
        # Draw crosshairs with smart labels using the visualizer
        crosshair_path = visualize_crosshairs(
            SCREENSHOT_PATH,
            json_data=result,  # Pass the full API response
            output_path=str(crosshair_output)
        )
        print(f"Saved crosshairs: {crosshair_path}")
        
        # Print the coordinates for debugging
        print(f"\n{len(coordinates)} elements detected:")
        for i, coord in enumerate(coordinates[:8]):  # Show first 8
            print(f"  Element {i+1}: {coord}")
        if len(coordinates) > 8:
            print(f"  ... and {len(coordinates) - 8} more")
    else:
        print("No coordinates found in response")


async def main():
    """Run the test 3 times"""
    print("Testing perfect bbox positioning with smart label placement")
    print(f"Using screenshot: {SCREENSHOT_PATH}")
    print(f"JSON responses will be saved to: {OUTPUT_DIR}")
    
    for run in range(1, 4):
        await test_gemini_detection(run)
        # Small delay between runs
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())