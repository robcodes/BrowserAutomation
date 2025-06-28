#!/usr/bin/env python3
"""
Test script to verify that Gemini coordinate normalization is working correctly.
This script:
1. Takes a screenshot
2. Uses Gemini to detect elements
3. Shows the normalized vs raw coordinates
4. Visualizes both to confirm correctness
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from clients.browser_client_crosshair import CrosshairBrowserClient
from clients.gemini_detector import GeminiDetector
from PIL import Image, ImageDraw
import json

GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def test_normalization():
    """Test coordinate normalization"""
    
    # Initialize browser client
    client = CrosshairBrowserClient()
    
    # Create a simple test page
    session_id = await client.create_session(headless=True)
    page_id = await client.new_page("data:text/html,<html><body><button style='position:absolute;left:100px;top:100px;width:200px;height:50px'>Test Button</button></body></html>")
    await asyncio.sleep(1)
    
    # Take screenshot
    screenshot_path = "/home/ubuntu/browser_automation/screenshots/normalization_test.png"
    await client.screenshot("normalization_test.png")
    print(f"Screenshot saved to: {screenshot_path}")
    
    # Get image dimensions
    img = Image.open(screenshot_path)
    width, height = img.size
    print(f"Image dimensions: {width}x{height}")
    
    # Use Gemini to detect elements
    detector = GeminiDetector(GEMINI_API_KEY)
    result = await detector.detect_elements(
        screenshot_path,
        "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all buttons and clickable elements"
    )
    
    print(f"\nFound {len(result['coordinates'])} elements")
    
    # Compare raw vs normalized coordinates
    for i, coords in enumerate(result['coordinates']):
        ymin, xmin, ymax, xmax = coords
        
        # Raw coordinates (as returned by Gemini)
        print(f"\nElement {i+1}:")
        print(f"  Raw coordinates: [ymin={ymin}, xmin={xmin}, ymax={ymax}, xmax={xmax}]")
        
        # Normalized pixel coordinates
        pixel_xmin = int(xmin / 1000 * width)
        pixel_ymin = int(ymin / 1000 * height)
        pixel_xmax = int(xmax / 1000 * width)
        pixel_ymax = int(ymax / 1000 * height)
        
        print(f"  Pixel coordinates: [x1={pixel_xmin}, y1={pixel_ymin}, x2={pixel_xmax}, y2={pixel_ymax}]")
        
        # Center coordinates
        center_x = int((xmin + xmax) / 2 / 1000 * width)
        center_y = int((ymin + ymax) / 2 / 1000 * height)
        print(f"  Center: ({center_x}, {center_y})")
        
        # Using the detector's conversion method
        click_pos = detector.convert_to_playwright_coords(coords, width, height)
        print(f"  Detector method center: ({click_pos['x']}, {click_pos['y']})")
        
        # Verify they match
        if click_pos['x'] == center_x and click_pos['y'] == center_y:
            print("  ✓ Normalization methods match!")
        else:
            print("  ✗ WARNING: Normalization methods don't match!")
    
    # Create visualization showing both raw and normalized
    draw = ImageDraw.Draw(img)
    
    for i, coords in enumerate(result['coordinates']):
        ymin, xmin, ymax, xmax = coords
        
        # Draw using normalized coordinates (correct)
        pixel_coords = [
            int(xmin / 1000 * width),
            int(ymin / 1000 * height),
            int(xmax / 1000 * width),
            int(ymax / 1000 * height)
        ]
        draw.rectangle(pixel_coords, outline='green', width=3)
        draw.text((pixel_coords[0], pixel_coords[1]-20), "Normalized", fill='green')
        
        # Draw using raw coordinates (incorrect - for comparison)
        if xmax < width and ymax < height:  # Only if within bounds
            raw_coords = [int(xmin), int(ymin), int(xmax), int(ymax)]
            draw.rectangle(raw_coords, outline='red', width=1)
            draw.text((raw_coords[0], raw_coords[1]-10), "Raw", fill='red')
    
    # Save comparison image
    comparison_path = "/home/ubuntu/browser_automation/screenshots/normalization_comparison.png"
    img.save(comparison_path)
    print(f"\nComparison image saved to: {comparison_path}")
    print("Green boxes = normalized (correct), Red boxes = raw (incorrect)")
    
    # Test clicking with normalized coordinates
    if result['coordinates']:
        coords = result['coordinates'][0]
        click_pos = detector.convert_to_playwright_coords(coords, width, height)
        
        print(f"\nTesting click at normalized position: ({click_pos['x']}, {click_pos['y']})")
        await client.click_at(x=click_pos['x'], y=click_pos['y'], label="normalized_click_test")
        
        # The crosshair screenshot will show exactly where the click happened
        print("Check the crosshair screenshot to verify click position!")
    
    await client.close_session()
    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(test_normalization())