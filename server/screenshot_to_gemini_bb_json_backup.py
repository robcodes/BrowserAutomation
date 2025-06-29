#!/usr/bin/env python3
"""
Standalone module for sending screenshots to Gemini Vision API and extracting bounding boxes.
Extracted from test_match_bb_detector.py to create a modular pipeline.
"""

import asyncio
import json
import re
import base64
import aiohttp
from pathlib import Path
from datetime import datetime
import argparse
import sys

# Default configuration
DEFAULT_PROMPT = "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc"
DEFAULT_MODEL = "gemini-2.5-flash"

def extract_coordinates(text):
    """Extract coordinates from text using the same regex as bb_detector.html"""
    regex = r'\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]'
    matches = re.findall(regex, text)
    return [json.loads(match) for match in matches]

async def detect_bounding_boxes(screenshot_path, api_key, save_json=False, output_dir=None, prompt=None):
    """
    Send screenshot to Gemini Vision API and extract bounding boxes.
    
    Args:
        screenshot_path: Path to the screenshot image
        api_key: Gemini API key
        save_json: Whether to save the raw response to a JSON file
        output_dir: Directory to save JSON output (defaults to same as screenshot)
        prompt: Custom prompt (defaults to the standard bounding box prompt)
    
    Returns:
        dict: {
            'raw_response': Full text response from Gemini,
            'coordinates': List of [ymin, xmin, ymax, xmax] arrays,
            'json_path': Path to saved JSON file (if save_json=True)
        }
    """
    # Use default prompt if not provided
    if prompt is None:
        prompt = DEFAULT_PROMPT
    
    # Prepare API URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_MODEL}:generateContent?key={api_key}"
    
    # Load and encode the image
    screenshot_path = Path(screenshot_path)
    if not screenshot_path.exists():
        raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")
    
    with open(screenshot_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    # Create payload matching bb_detector.html structure
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
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
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Gemini API error: {response.status} - {error_text}")
            result = await response.json()
    
    # Extract the text response
    try:
        text = result['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        raise Exception(f"Unexpected API response structure: {result}")
    
    # Extract coordinates using the same method as bb_detector.html
    coordinates = extract_coordinates(text)
    
    # Prepare result
    result_dict = {
        'raw_response': text,
        'coordinates': coordinates,
        'json_path': None
    }
    
    # Save JSON if requested
    if save_json:
        if output_dir is None:
            output_dir = screenshot_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename based on screenshot name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"{screenshot_path.stem}_gemini_bb_{timestamp}.json"
        json_path = output_dir / json_filename
        
        # Save the complete response data
        json_data = {
            'screenshot_path': str(screenshot_path),
            'prompt': prompt,
            'raw_response': text,
            'coordinates': coordinates,
            'timestamp': timestamp
        }
        
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        result_dict['json_path'] = str(json_path)
    
    return result_dict

def sync_detect_bounding_boxes(screenshot_path, api_key, save_json=False, output_dir=None, prompt=None):
    """Synchronous wrapper for detect_bounding_boxes"""
    return asyncio.run(detect_bounding_boxes(screenshot_path, api_key, save_json, output_dir, prompt))

def main():
    """Command line interface for testing"""
    parser = argparse.ArgumentParser(description='Send screenshot to Gemini Vision API for bounding box detection')
    parser.add_argument('screenshot', help='Path to screenshot image')
    parser.add_argument('--api-key', required=True, help='Gemini API key')
    parser.add_argument('--save-json', action='store_true', help='Save raw response to JSON file')
    parser.add_argument('--output-dir', help='Directory to save JSON output')
    parser.add_argument('--prompt', help='Custom prompt (defaults to standard bounding box prompt)')
    parser.add_argument('--format', choices=['json', 'coords', 'full'], default='full',
                        help='Output format: json (full JSON), coords (just coordinates), full (human-readable)')
    
    args = parser.parse_args()
    
    try:
        # Run detection
        result = sync_detect_bounding_boxes(
            args.screenshot,
            args.api_key,
            save_json=args.save_json,
            output_dir=args.output_dir,
            prompt=args.prompt
        )
        
        # Output based on format
        if args.format == 'json':
            print(json.dumps(result, indent=2))
        elif args.format == 'coords':
            print(json.dumps(result['coordinates'], indent=2))
        else:  # full
            print(f"Screenshot: {args.screenshot}")
            print(f"Found {len(result['coordinates'])} bounding boxes")
            print("\nCoordinates:")
            for i, coord in enumerate(result['coordinates']):
                print(f"  Box {i+1}: {coord}")
            print(f"\nRaw response preview: {result['raw_response'][:200]}...")
            if result['json_path']:
                print(f"\nJSON saved to: {result['json_path']}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()