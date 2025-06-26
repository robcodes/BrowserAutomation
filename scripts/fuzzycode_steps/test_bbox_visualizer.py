#!/usr/bin/env python3
"""
Simple test script to verify bbox_visualizer module works correctly.
Loads a saved JSON file and creates both bbox and crosshair visualizations.
"""

import json
from pathlib import Path
from bbox_visualizer import visualize_bboxes, visualize_crosshairs, visualize

# Configuration
SCREENSHOT_PATH = "/home/ubuntu/browser_automation/screenshots/element_search.png"
OUTPUT_DIR = "/home/ubuntu/browser_automation/screenshots/"


def find_latest_json():
    """Find the most recent gemini_response JSON file"""
    json_files = list(Path(OUTPUT_DIR).glob("gemini_response_*.json"))
    if not json_files:
        return None
    return max(json_files, key=lambda p: p.stat().st_mtime)


def test_with_saved_json():
    """Test visualizer with a saved JSON file"""
    # Find latest JSON file
    json_path = find_latest_json()
    if not json_path:
        print("No saved JSON files found. Run test_perfect_bbox_smart_labels.py first.")
        return
    
    print(f"Using JSON file: {json_path}")
    
    # Test 1: Load JSON and create bbox visualization
    print("\n--- Test 1: Bounding Box Visualization ---")
    bbox_output = Path(OUTPUT_DIR) / "test_visualizer_bboxes.png"
    bbox_path = visualize_bboxes(
        SCREENSHOT_PATH,
        json_path=str(json_path),
        output_path=str(bbox_output)
    )
    print(f"Created bbox visualization: {bbox_path}")
    
    # Test 2: Create crosshair visualization
    print("\n--- Test 2: Crosshair Visualization ---")
    crosshair_output = Path(OUTPUT_DIR) / "test_visualizer_crosshairs.png"
    crosshair_path = visualize_crosshairs(
        SCREENSHOT_PATH,
        json_path=str(json_path),
        output_path=str(crosshair_output)
    )
    print(f"Created crosshair visualization: {crosshair_path}")
    
    # Test 3: Direct coordinates test
    print("\n--- Test 3: Direct Coordinates Test ---")
    test_coords = [
        [100, 200, 300, 400],  # ymin, xmin, ymax, xmax (will be normalized by /1000)
        [500, 600, 700, 800],
        [200, 100, 400, 300]
    ]
    
    direct_output = Path(OUTPUT_DIR) / "test_visualizer_direct.png"
    direct_path = visualize(
        SCREENSHOT_PATH,
        json_data=test_coords,
        mode='bbox',
        output_path=str(direct_output)
    )
    print(f"Created direct visualization: {direct_path}")
    
    # Test 4: Load and examine JSON structure
    print("\n--- Test 4: JSON Structure ---")
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    
    # Print JSON structure
    print("JSON keys:", list(json_data.keys()))
    if 'candidates' in json_data:
        try:
            text = json_data['candidates'][0]['content']['parts'][0]['text']
            print(f"Response text preview: {text[:100]}...")
            
            # Count coordinates in response
            import re
            regex = r'\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]'
            matches = re.findall(regex, text)
            print(f"Number of coordinates found: {len(matches)}")
        except (KeyError, IndexError):
            print("Could not extract text from JSON")


def test_error_handling():
    """Test error handling in the visualizer"""
    print("\n--- Test Error Handling ---")
    
    try:
        # Test with no data
        visualize(SCREENSHOT_PATH)
    except ValueError as e:
        print(f"✓ Correctly caught missing data error: {e}")
    
    try:
        # Test with invalid JSON structure
        visualize(SCREENSHOT_PATH, json_data={"invalid": "structure"})
    except ValueError as e:
        print(f"✓ Correctly caught invalid structure error: {e}")
    
    try:
        # Test with empty coordinates
        visualize(SCREENSHOT_PATH, json_data=[])
    except ValueError as e:
        print(f"✓ Correctly caught empty coordinates error: {e}")


def main():
    """Run all tests"""
    print("Testing bbox_visualizer module")
    print("=" * 50)
    
    # Check if screenshot exists
    if not Path(SCREENSHOT_PATH).exists():
        print(f"Screenshot not found: {SCREENSHOT_PATH}")
        print("Please ensure element_search.png exists in the screenshots folder")
        return
    
    # Run tests
    test_with_saved_json()
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    main()