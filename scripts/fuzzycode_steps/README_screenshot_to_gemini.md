# screenshot_to_gemini_bb_json.py

A standalone module for sending screenshots to Gemini Vision API and extracting bounding boxes. This module was extracted from `test_match_bb_detector.py` to create a clean, modular pipeline.

## Features

- Sends screenshots to Gemini Vision API with the exact same prompt used in bb_detector.html
- Extracts bounding box coordinates using regex pattern matching
- Returns both raw response and parsed coordinates
- Optionally saves the complete response as JSON
- Can be used as a Python module or command-line tool

## Usage

### As a Python Module

```python
from screenshot_to_gemini_bb_json import sync_detect_bounding_boxes

# Basic usage
result = sync_detect_bounding_boxes(
    "path/to/screenshot.png",
    "your-api-key"
)

# With JSON saving
result = sync_detect_bounding_boxes(
    "path/to/screenshot.png",
    "your-api-key",
    save_json=True,
    output_dir="/path/to/output/"
)

# Access results
print(f"Found {len(result['coordinates'])} bounding boxes")
for coord in result['coordinates']:
    print(coord)  # [ymin, xmin, ymax, xmax]
```

### As a Command-Line Tool

```bash
# Basic usage
./screenshot_to_gemini_bb_json.py screenshot.png --api-key YOUR_KEY

# Save JSON output
./screenshot_to_gemini_bb_json.py screenshot.png --api-key YOUR_KEY --save-json

# Output only coordinates
./screenshot_to_gemini_bb_json.py screenshot.png --api-key YOUR_KEY --format coords

# Custom prompt
./screenshot_to_gemini_bb_json.py screenshot.png --api-key YOUR_KEY \
    --prompt "Find all buttons, return as [ymin, xmin, ymax, xmax]"
```

## Pipeline Integration

This module is designed to work in a pipeline with `bbox_visualizer.py`:

1. **screenshot_to_gemini_bb_json.py** → Produces JSON with bounding boxes
2. **bbox_visualizer.py** → Takes JSON and creates visualizations

Example pipeline:
```bash
# Step 1: Get bounding boxes from Gemini
./screenshot_to_gemini_bb_json.py screenshot.png --api-key KEY --save-json

# Step 2: Visualize the bounding boxes
./bbox_visualizer.py screenshot_gemini_bb_20240101_120000.json
```

## Output Format

The module returns/saves JSON in this format:
```json
{
  "screenshot_path": "/path/to/screenshot.png",
  "prompt": "Return bounding boxes as JSON arrays...",
  "raw_response": "Here are the bounding boxes: [100, 200, 300, 400]...",
  "coordinates": [
    [100, 200, 300, 400],
    [150, 250, 350, 450]
  ],
  "timestamp": "20240101_120000"
}
```

## Key Implementation Details

- Uses the EXACT same prompt as bb_detector.html: "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc"
- Uses the same regex pattern for coordinate extraction: `r'\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]'`
- Preserves the exact API call format from the original implementation
- Coordinates are in the format [ymin, xmin, ymax, xmax] where values are typically 0-1000

## Dependencies

- aiohttp
- PIL (Pillow)
- Standard library: asyncio, json, re, base64, pathlib

## Error Handling

The module includes error handling for:
- Missing screenshot files
- API errors (non-200 responses)
- Unexpected API response structure
- JSON parsing errors