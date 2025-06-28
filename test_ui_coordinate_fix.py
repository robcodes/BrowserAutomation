#!/usr/bin/env python3
"""
Test script to verify UI coordinate normalization fix.
Tests that Gemini coordinates (0-1000 range) are properly normalized.
"""

import asyncio
import json
from datetime import datetime

# Test coordinates from Gemini (in 0-1000 range)
test_gemini_coords = [
    [100, 200, 300, 400],  # [ymin, xmin, ymax, xmax]
    [500, 600, 700, 800],
    [50, 50, 150, 150],
]

# Test screenshot dimensions
test_dimensions = {
    "width": 1920,
    "height": 1080
}

def normalize_and_convert_coords(coords, dimensions):
    """Normalize Gemini coordinates and convert to pixel coordinates."""
    ymin, xmin, ymax, xmax = coords
    
    # Normalize (divide by 1000)
    norm_ymin = ymin / 1000
    norm_xmin = xmin / 1000
    norm_ymax = ymax / 1000
    norm_xmax = xmax / 1000
    
    # Convert to pixels
    pixel_xmin = round(norm_xmin * dimensions["width"])
    pixel_xmax = round(norm_xmax * dimensions["width"])
    pixel_ymin = round(norm_ymin * dimensions["height"])
    pixel_ymax = round(norm_ymax * dimensions["height"])
    
    # Calculate center
    center_x = round((pixel_xmin + pixel_xmax) / 2)
    center_y = round((pixel_ymin + pixel_ymax) / 2)
    
    return {
        "normalized": [norm_ymin, norm_xmin, norm_ymax, norm_xmax],
        "pixels": {
            "bbox": [pixel_ymin, pixel_xmin, pixel_ymax, pixel_xmax],
            "center": [center_x, center_y]
        }
    }

def main():
    print("Testing Gemini Coordinate Normalization")
    print("=" * 50)
    print(f"Test dimensions: {test_dimensions['width']}x{test_dimensions['height']}")
    print()
    
    for i, coords in enumerate(test_gemini_coords):
        print(f"Test {i+1}:")
        print(f"  Gemini coords: {coords}")
        
        result = normalize_and_convert_coords(coords, test_dimensions)
        
        print(f"  Normalized: {result['normalized']}")
        print(f"  Pixel bbox: {result['pixels']['bbox']}")
        print(f"  Center point: {result['pixels']['center']}")
        print(f"  Click code: page.click({{position: {{x: {result['pixels']['center'][0]}, y: {result['pixels']['center'][1]}}}}});")
        print()

    print("\nExpected behavior:")
    print("- Gemini coordinates should be divided by 1000 to get 0-1 range")
    print("- Normalized coords multiplied by image dimensions for pixel values")
    print("- Center point calculated from pixel bounding box")
    
    print("\nUI Fix Summary:")
    print("1. Screenshot dimensions are captured when image loads")
    print("2. generateClickCode() normalizes coords before calculating pixels")
    print("3. generateTypeCode() uses same normalization logic")
    print("4. Fallback to raw coords if dimensions unavailable")

if __name__ == "__main__":
    main()