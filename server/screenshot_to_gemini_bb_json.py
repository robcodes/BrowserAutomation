#!/usr/bin/env python3
"""
Enhanced module for sending screenshots to Gemini Vision API and extracting bounding boxes.
Supports model-specific prompts, labels, and custom user prompts.
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

# Import the enhanced detector
sys.path.append(str(Path(__file__).parent.parent))
from clients.gemini_detector import GeminiDetector

# Default configuration (for backward compatibility)
DEFAULT_PROMPT = "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc"
DEFAULT_MODEL = "gemini-2.5-flash"

def extract_coordinates(text):
    """Extract coordinates from text using regex (backward compatibility)"""
    regex = r'\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]'
    matches = re.findall(regex, text)
    return [json.loads(match) for match in matches]

async def detect_bounding_boxes(screenshot_path, api_key, save_json=False, output_dir=None, 
                              prompt=None, model=None, user_prompt=None, num_calls=1):
    """
    Enhanced function to send screenshot to Gemini Vision API and extract bounding boxes.
    
    Args:
        screenshot_path: Path to the screenshot image
        api_key: Gemini API key
        save_json: Whether to save the raw response to a JSON file
        output_dir: Directory to save JSON output (defaults to same as screenshot)
        prompt: Custom system prompt (defaults to model-specific prompt)
        model: Model to use (defaults to gemini-2.5-flash)
        user_prompt: Additional user context (e.g. "Find the close button")
        num_calls: Number of API calls to make for consistency
    
    Returns:
        dict: {
            'raw_response': Full text response from Gemini,
            'coordinates': List of [ymin, xmin, ymax, xmax] arrays,
            'labels': List of labels for each bounding box,
            'bounding_boxes': List of {box_2d, label} dicts,
            'json_path': Path to saved JSON file (if save_json=True)
        }
    """
    # Use defaults if not provided
    if model is None:
        model = DEFAULT_MODEL
    
    # Initialize detector
    detector = GeminiDetector(api_key=api_key, model=model)
    
    # Detect elements using enhanced detector
    result = await detector.detect_elements(
        screenshot_path,
        user_prompt=user_prompt or "",
        system_prompt=prompt,  # Use custom prompt if provided
        save_annotated=False,  # We'll handle annotation separately if needed
        return_labels=True,
        num_calls=num_calls
    )
    
    # Prepare result in expected format
    result_dict = {
        'raw_response': result['raw_response'],
        'coordinates': result['coordinates'],
        'labels': result.get('labels', []),
        'bounding_boxes': [bb.to_dict() for bb in result.get('bounding_boxes', [])],
        'json_path': None
    }
    
    # Save JSON if requested
    if save_json:
        if output_dir is None:
            output_dir = Path(screenshot_path).parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename based on screenshot name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"{Path(screenshot_path).stem}_gemini_bb_{timestamp}.json"
        json_path = output_dir / json_filename
        
        # Save the complete response data
        json_data = {
            'screenshot_path': str(screenshot_path),
            'model': model,
            'system_prompt': prompt or detector.get_system_prompt(),
            'user_prompt': user_prompt,
            'raw_response': result['raw_response'],
            'coordinates': result['coordinates'],
            'labels': result.get('labels', []),
            'bounding_boxes': result_dict['bounding_boxes'],
            'timestamp': timestamp,
            'num_calls': num_calls
        }
        
        # Include all results if multiple calls were made
        if 'results' in result:
            json_data['all_results'] = result['results']
        
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        result_dict['json_path'] = str(json_path)
    
    return result_dict

def sync_detect_bounding_boxes(screenshot_path, api_key, save_json=False, output_dir=None, 
                             prompt=None, model=None, user_prompt=None, num_calls=1):
    """Synchronous wrapper for detect_bounding_boxes"""
    return asyncio.run(detect_bounding_boxes(
        screenshot_path, api_key, save_json, output_dir, prompt, model, user_prompt, num_calls
    ))

def main():
    """Command line interface for testing"""
    parser = argparse.ArgumentParser(
        description='Send screenshot to Gemini Vision API for bounding box detection with enhanced features'
    )
    parser.add_argument('screenshot', help='Path to screenshot image')
    parser.add_argument('--api-key', required=True, help='Gemini API key')
    parser.add_argument('--save-json', action='store_true', help='Save raw response to JSON file')
    parser.add_argument('--output-dir', help='Directory to save JSON output')
    parser.add_argument('--prompt', help='Custom system prompt (overrides model defaults)')
    parser.add_argument('--user-prompt', help='Additional user context (e.g. "Find the login button")')
    parser.add_argument('--model', choices=['gemini-2.0-flash-exp', 'gemini-2.5-flash'], 
                        default='gemini-2.5-flash', help='Model to use')
    parser.add_argument('--num-calls', type=int, default=1, help='Number of API calls for consistency')
    parser.add_argument('--format', choices=['json', 'coords', 'full', 'labels'], default='full',
                        help='Output format: json (full JSON), coords (just coordinates), labels (with labels), full (human-readable)')
    
    args = parser.parse_args()
    
    try:
        # Run detection
        result = sync_detect_bounding_boxes(
            args.screenshot,
            args.api_key,
            save_json=args.save_json,
            output_dir=args.output_dir,
            prompt=args.prompt,
            model=args.model,
            user_prompt=args.user_prompt,
            num_calls=args.num_calls
        )
        
        # Output based on format
        if args.format == 'json':
            print(json.dumps(result, indent=2))
        elif args.format == 'coords':
            print(json.dumps(result['coordinates'], indent=2))
        elif args.format == 'labels':
            # Show coordinates with labels
            for i, (coord, label) in enumerate(zip(result['coordinates'], result.get('labels', []))):
                print(f"{i+1}. {label}: {coord}")
        else:  # full
            print(f"Screenshot: {args.screenshot}")
            print(f"Model: {args.model}")
            print(f"Found {len(result['coordinates'])} bounding boxes")
            print("\nCoordinates with labels:")
            for i, (coord, label) in enumerate(zip(result['coordinates'], result.get('labels', []))):
                print(f"  {i+1}. {label}: {coord}")
            if args.user_prompt:
                print(f"\nUser prompt: {args.user_prompt}")
            print(f"\nRaw response preview: {result['raw_response'][:200]}...")
            if result['json_path']:
                print(f"\nJSON saved to: {result['json_path']}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()