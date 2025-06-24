#!/usr/bin/env python3
"""Test the improved prompt for finding all elements"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from clients.gemini_detector import GeminiDetector

GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def main():
    detector = GeminiDetector(GEMINI_API_KEY)
    screenshot_path = "/home/ubuntu/browser_automation/screenshots/find_all_test.png"
    
    print("Testing improved prompt for element detection")
    print("=" * 60)
    
    # Test 1: Original generic prompt
    print("\n1. ORIGINAL PROMPT:")
    print("   'Find ALL clickable elements'")
    try:
        result = await detector.detect_elements(
            screenshot_path,
            "Find ALL clickable elements"
        )
        print(f"   Found {len(result['coordinates'])} elements")
    except Exception as e:
        print(f"   Error: {e}")
    
    await asyncio.sleep(15)
    
    # Test 2: Improved specific prompt
    print("\n2. IMPROVED PROMPT:")
    print("   'Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc'")
    try:
        result = await detector.detect_elements(
            screenshot_path,
            "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc",
            save_annotated=True
        )
        print(f"   Found {len(result['coordinates'])} elements")
        
        # Check for X button
        print("\n   Top-right elements (likely modal controls):")
        for i, coords in enumerate(result['coordinates']):
            ymin, xmin, ymax, xmax = coords
            if xmin > 900 and ymin < 100:
                center_x = int((xmin+xmax)/2)
                center_y = int((ymin+ymax)/2)
                print(f"   Element {i+1}: {coords} (center: x={center_x}, y={center_y})")
        
        if result['annotated_image_path']:
            import shutil
            shutil.copy(result['annotated_image_path'],
                       "/home/ubuntu/browser_automation/screenshots/improved_prompt_annotated.png")
            print("\n   Saved annotated image as: improved_prompt_annotated.png")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("CONCLUSION: The improved prompt should detect more elements,")
    print("especially icons and SVG elements that might be missed otherwise.")

if __name__ == "__main__":
    asyncio.run(main())