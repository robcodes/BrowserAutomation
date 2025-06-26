#!/usr/bin/env python3
"""
Test script that EXACTLY matches bb_detector.html implementation.
Goal: Figure out why bb_detector.html gets perfect bounding boxes.
"""

import asyncio
import json
import re
import base64
from PIL import Image, ImageDraw, ImageFont
import aiohttp
from datetime import datetime
import random

# Configuration
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"
SCREENSHOT_PATH = "/home/ubuntu/browser_automation/screenshots/element_search.png"
OUTPUT_DIR = "/home/ubuntu/browser_automation/screenshots/"

# Exact prompt from bb_detector.html
PROMPT = "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc"

def extract_coordinates(text):
    """Extract coordinates from text using the same regex as bb_detector.html"""
    regex = r'\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]'
    matches = re.findall(regex, text)
    return [json.loads(match) for match in matches]

def draw_bounding_boxes(image_path, coordinates, run_number):
    """Draw bounding boxes exactly like bb_detector.html does"""
    # Load the image
    img = Image.open(image_path)
    width, height = img.size
    
    # Create a new image with padding like bb_detector.html (80px left, 20px top)
    canvas_width = width + 100
    canvas_height = height + 100
    canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
    
    # Paste the original image at the offset position
    canvas.paste(img, (80, 20))
    
    # Draw on the canvas
    draw = ImageDraw.Draw(canvas)
    
    # Draw grid lines (optional - bb_detector.html has these)
    for i in range(0, 1001, 100):
        # Vertical lines
        x = 80 + int(i / 1000 * width)
        draw.line([(x, 20), (x, height + 20)], fill=(255, 0, 0, 128), width=1)
        
        # Horizontal lines
        y = 20 + int((1000 - i) / 1000 * height)
        draw.line([(80, y), (width + 80, y)], fill=(255, 0, 0, 128), width=1)
    
    # Colors for bounding boxes
    colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF']
    
    # Draw bounding boxes
    for idx, box in enumerate(coordinates):
        # bb_detector.html divides coordinates by 1000 to normalize them
        ymin, xmin, ymax, xmax = [coord / 1000 for coord in box]
        
        # Calculate pixel positions
        x1 = int(xmin * width) + 80
        y1 = int(ymin * height) + 20
        x2 = int(xmax * width) + 80
        y2 = int(ymax * height) + 20
        
        # Draw the box
        color = colors[idx % len(colors)]
        draw.rectangle([x1, y1, x2, y2], outline=color, width=5)
        
        # Draw label outside the box (smart positioning)
        label = f"Box {idx+1}"
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font = None
        
        # Get text size
        if font:
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(label) * 8
            text_height = 12
        
        # Smart label positioning - place outside the box
        label_x = x1
        label_y = y1 - text_height - 5 if y1 > 30 else y2 + 5
        
        # Add background for label
        padding = 3
        draw.rectangle(
            [label_x - padding, label_y - padding, 
             label_x + text_width + padding, label_y + text_height + padding],
            fill='white', outline=color, width=2
        )
        draw.text((label_x, label_y), label, fill=color, font=font)
    
    # Draw axes and labels like bb_detector.html
    draw.line([(80, 20), (80, height + 20)], fill='black', width=1)  # Y-axis
    draw.line([(80, height + 20), (width + 80, height + 20)], fill='black', width=1)  # X-axis
    
    # Save the result
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"{OUTPUT_DIR}run{run_number}_bb_detector_match_{timestamp}.png"
    canvas.save(output_path)
    print(f"Saved: {output_path}")
    
    return output_path

async def test_gemini_detection(run_number):
    """Test Gemini detection matching bb_detector.html exactly"""
    print(f"\n=== Run {run_number} ===")
    
    # Use direct API call like gemini_detector.py
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # Load and prepare the image
    with open(SCREENSHOT_PATH, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    # Create payload matching bb_detector.html structure
    payload = {
        "contents": [{
            "parts": [
                {"text": PROMPT},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_data
                    }
                }
            ]
        }]
    }
    
    # Send to Gemini with the exact prompt
    print(f"Sending to Gemini with prompt: {PROMPT}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            result = await response.json()
    
    # Extract the text response
    try:
        text = result['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        print(f"Unexpected API response: {result}")
        return
        
    print(f"Gemini response preview: {text[:200]}...")
    
    # Extract coordinates using the same method as bb_detector.html
    coordinates = extract_coordinates(text)
    print(f"Found {len(coordinates)} bounding boxes")
    
    if coordinates:
        # Draw the bounding boxes
        output_path = draw_bounding_boxes(SCREENSHOT_PATH, coordinates, run_number)
        
        # Print the coordinates for debugging
        print("\nCoordinates found:")
        for i, coord in enumerate(coordinates):
            print(f"  Box {i+1}: {coord}")
    else:
        print("No coordinates found in response")

async def main():
    """Run the test 3 times"""
    for run in range(1, 4):
        await test_gemini_detection(run)
        # Small delay between runs
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())