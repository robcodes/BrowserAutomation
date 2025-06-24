#!/usr/bin/env python3
"""Final comparison: Direct vs Find All with visual confirmation"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from clients.gemini_detector import GeminiDetector
import shutil

GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def main():
    detector = GeminiDetector(GEMINI_API_KEY)
    screenshot_path = "/home/ubuntu/browser_automation/screenshots/find_all_test.png"
    
    print("FINAL COMPARISON TEST")
    print("="*60)
    
    # Test 1: Direct X button search
    print("\n1. DIRECT X BUTTON SEARCH:")
    try:
        result = await detector.find_element(
            screenshot_path,
            "the X close button (not the expand button) in the modal header",
            save_annotated=True
        )
        
        if result['coordinates']:
            coords = result['coordinates'][0]
            ymin, xmin, ymax, xmax = coords
            print(f"   Found at: {coords}")
            print(f"   Center: x={int((xmin+xmax)/2)}, y={int((ymin+ymax)/2)}")
            
            if result['annotated_image_path']:
                shutil.copy(result['annotated_image_path'], 
                           "/home/ubuntu/browser_automation/screenshots/final_direct_search.png")
                print("   Saved as: final_direct_search.png")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Wait
    await asyncio.sleep(15)
    
    # Test 2: Find all elements
    print("\n2. FIND ALL ELEMENTS:")
    try:
        result = await detector.detect_elements(
            screenshot_path,
            """Find ALL clickable elements including buttons, links, and icons.
            Pay special attention to distinguish between expand/fullscreen buttons and X/close buttons.
            Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax]""",
            save_annotated=True
        )
        
        print(f"   Found {len(result['coordinates'])} elements")
        
        # Analyze top-right elements
        print("\n   Top-right elements (xmin > 900, ymin < 100):")
        for i, coords in enumerate(result['coordinates']):
            ymin, xmin, ymax, xmax = coords
            if xmin > 900 and ymin < 100:
                center_x = int((xmin+xmax)/2)
                center_y = int((ymin+ymax)/2)
                print(f"   Element {i+1}: {coords}")
                print(f"             Center: x={center_x}, y={center_y}")
                
                # Check if this matches the direct search position
                if 955 < center_x < 970 and 45 < center_y < 65:
                    print("             ^ This is likely the X button!")
        
        if result['annotated_image_path']:
            shutil.copy(result['annotated_image_path'],
                       "/home/ubuntu/browser_automation/screenshots/final_find_all.png")
            print("\n   Saved as: final_find_all.png")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*60)
    print("Check the annotated images to visually confirm:")
    print("- final_direct_search.png")
    print("- final_find_all.png")

if __name__ == "__main__":
    asyncio.run(main())