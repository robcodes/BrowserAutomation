#!/usr/bin/env python3
"""
Test the screenshot_to_gemini_bb_json module
"""

from screenshot_to_gemini_bb_json import sync_detect_bounding_boxes
import json

# Configuration
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"
SCREENSHOT_PATH = "/home/ubuntu/browser_automation/screenshots/element_search.png"

def test_module():
    """Test the modular function"""
    print("Testing screenshot_to_gemini_bb_json module...")
    print(f"Screenshot: {SCREENSHOT_PATH}")
    
    # Call the module function
    result = sync_detect_bounding_boxes(
        SCREENSHOT_PATH,
        GEMINI_API_KEY,
        save_json=True,  # Save the JSON output
        output_dir="/home/ubuntu/browser_automation/screenshots/"
    )
    
    # Display results
    print(f"\nFound {len(result['coordinates'])} bounding boxes")
    print("\nFirst 5 coordinates:")
    for i, coord in enumerate(result['coordinates'][:5]):
        print(f"  Box {i+1}: {coord}")
    
    print(f"\nRaw response preview: {result['raw_response'][:200]}...")
    
    if result['json_path']:
        print(f"\nJSON saved to: {result['json_path']}")
        
        # Read and display the saved JSON structure
        with open(result['json_path'], 'r') as f:
            saved_data = json.load(f)
        print(f"\nSaved JSON contains:")
        print(f"  - screenshot_path: {saved_data['screenshot_path']}")
        print(f"  - prompt: {saved_data['prompt'][:50]}...")
        print(f"  - coordinates: {len(saved_data['coordinates'])} items")
        print(f"  - timestamp: {saved_data['timestamp']}")

if __name__ == "__main__":
    test_module()