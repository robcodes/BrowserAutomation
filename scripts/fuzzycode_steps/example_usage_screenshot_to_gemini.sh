#!/bin/bash
# Example usage of screenshot_to_gemini_bb_json.py from command line

# Set the API key (you should replace this with your own)
API_KEY="AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

# Path to screenshot
SCREENSHOT="./screenshots/element_search.png"

echo "=== Example 1: Basic usage with human-readable output ==="
./screenshot_to_gemini_bb_json.py "$SCREENSHOT" --api-key "$API_KEY"

echo -e "\n=== Example 2: Save JSON output ==="
./screenshot_to_gemini_bb_json.py "$SCREENSHOT" --api-key "$API_KEY" --save-json

echo -e "\n=== Example 3: Output only coordinates as JSON ==="
./screenshot_to_gemini_bb_json.py "$SCREENSHOT" --api-key "$API_KEY" --format coords

echo -e "\n=== Example 4: Full JSON output ==="
./screenshot_to_gemini_bb_json.py "$SCREENSHOT" --api-key "$API_KEY" --format json

echo -e "\n=== Example 5: Custom prompt ==="
./screenshot_to_gemini_bb_json.py "$SCREENSHOT" --api-key "$API_KEY" \
    --prompt "Find all buttons and clickable elements, return as [ymin, xmin, ymax, xmax]"