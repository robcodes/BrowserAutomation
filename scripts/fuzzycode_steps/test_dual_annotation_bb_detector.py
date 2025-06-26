#!/usr/bin/env python3
"""
Test script to verify bounding box detection consistency using the EXACT prompt
and logic from bb_detector.html, but with dual annotation (numbers + crosshairs).

This script runs the EXACT SAME detection 3 times to analyze consistency.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict, Counter

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from clients.gemini_detector import GeminiDetector

# EXACT prompt from bb_detector.html
EXACT_PROMPT = "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax]"

# Your API key (replace with your actual key)
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

def smart_label_placement(draw, box_num, xmin, ymin, xmax, ymax, font_size=24, padding=5):
    """
    Smart label placement algorithm that avoids going off-screen.
    Returns the best position and alignment for the label.
    """
    # Get image dimensions
    img_width, img_height = draw.im.size
    
    # Try to load a font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    label_text = str(box_num)
    
    # Get text bounding box using textbbox
    bbox = draw.textbbox((0, 0), label_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Add padding
    label_width = text_width + 2 * padding
    label_height = text_height + 2 * padding
    
    # Define possible positions in priority order
    positions = []
    
    # 1. Top-left (outside if possible)
    if ymin >= label_height:  # Can place above
        positions.append(('above-left', xmin, ymin - label_height))
    elif xmin >= label_width:  # Can place to the left
        positions.append(('left-top', xmin - label_width, ymin))
    else:  # Place inside top-left
        positions.append(('inside-top-left', xmin + padding, ymin + padding))
    
    # 2. Top-right (outside if possible)
    if ymin >= label_height and xmax + label_width <= img_width:  # Can place above
        positions.append(('above-right', xmax - label_width, ymin - label_height))
    elif xmax + label_width <= img_width:  # Can place to the right
        positions.append(('right-top', xmax, ymin))
    else:  # Place inside top-right
        positions.append(('inside-top-right', xmax - label_width - padding, ymin + padding))
    
    # 3. Bottom-left (outside if possible)
    if ymax + label_height <= img_height:  # Can place below
        positions.append(('below-left', xmin, ymax))
    elif xmin >= label_width:  # Can place to the left
        positions.append(('left-bottom', xmin - label_width, ymax - label_height))
    else:  # Place inside bottom-left
        positions.append(('inside-bottom-left', xmin + padding, ymax - label_height - padding))
    
    # 4. Bottom-right (outside if possible)
    if ymax + label_height <= img_height and xmax - label_width >= 0:  # Can place below
        positions.append(('below-right', xmax - label_width, ymax))
    elif xmax + label_width <= img_width:  # Can place to the right
        positions.append(('right-bottom', xmax, ymax - label_height))
    else:  # Place inside bottom-right
        positions.append(('inside-bottom-right', xmax - label_width - padding, ymax - label_height - padding))
    
    # 5. Center (last resort)
    center_x = (xmin + xmax) // 2 - label_width // 2
    center_y = (ymin + ymax) // 2 - label_height // 2
    positions.append(('center', center_x, center_y))
    
    # Choose the first position that fits entirely within the image
    for position_type, x, y in positions:
        if 0 <= x and x + label_width <= img_width and 0 <= y and y + label_height <= img_height:
            return x, y, label_width, label_height, font
    
    # If nothing fits perfectly, use the first position and clip
    _, x, y = positions[0]
    x = max(0, min(x, img_width - label_width))
    y = max(0, min(y, img_height - label_height))
    return x, y, label_width, label_height, font


def draw_bounding_boxes_with_labels(image_path, boxes, output_path):
    """Draw bounding boxes with smart numbered labels."""
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # Colors for boxes
    colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', 
              '#FFA500', '#800080', '#008080', '#FF1493', '#32CD32', '#FFD700']
    
    for idx, (ymin, xmin, ymax, xmax) in enumerate(boxes):
        color = colors[idx % len(colors)]
        # Draw bounding box
        draw.rectangle([xmin, ymin, xmax, ymax], outline=color, width=3)
        
        # Smart label placement
        label_x, label_y, label_w, label_h, font = smart_label_placement(
            draw, idx + 1, xmin, ymin, xmax, ymax
        )
        
        # Draw label background
        draw.rectangle([label_x, label_y, label_x + label_w, label_y + label_h], 
                      fill=color, outline=color)
        
        # Draw label text
        draw.text((label_x + 5, label_y + 5), str(idx + 1), fill='white', font=font)
    
    img.save(output_path)
    print(f"Saved bounding boxes image: {output_path}")


def draw_crosshairs(image_path, boxes, output_path):
    """Draw crosshairs at the center of each bounding box with smart numbered labels."""
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # Colors for crosshairs
    colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF',
              '#FFA500', '#800080', '#008080', '#FF1493', '#32CD32', '#FFD700']
    
    for idx, (ymin, xmin, ymax, xmax) in enumerate(boxes):
        color = colors[idx % len(colors)]
        
        # Calculate center
        center_x = (xmin + xmax) // 2
        center_y = (ymin + ymax) // 2
        
        # Draw crosshair
        crosshair_size = 20
        draw.line([center_x - crosshair_size, center_y, center_x + crosshair_size, center_y], 
                 fill=color, width=3)
        draw.line([center_x, center_y - crosshair_size, center_x, center_y + crosshair_size], 
                 fill=color, width=3)
        
        # Draw center dot
        dot_size = 4
        draw.ellipse([center_x - dot_size, center_y - dot_size, 
                     center_x + dot_size, center_y + dot_size], 
                    fill='yellow', outline=color, width=2)
        
        # Smart label placement for crosshair
        label_x, label_y, label_w, label_h, font = smart_label_placement(
            draw, idx + 1, xmin, ymin, xmax, ymax
        )
        
        # Draw label background
        draw.rectangle([label_x, label_y, label_x + label_w, label_y + label_h], 
                      fill=color, outline=color)
        
        # Draw label text
        draw.text((label_x + 5, label_y + 5), str(idx + 1), fill='white', font=font)
    
    img.save(output_path)
    print(f"Saved crosshairs image: {output_path}")


def analyze_consistency(all_results):
    """Analyze consistency across multiple runs."""
    print("\n" + "="*60)
    print("CONSISTENCY ANALYSIS")
    print("="*60)
    
    # Count detections per run
    for i, (coords, raw_response) in enumerate(all_results):
        print(f"\nRun {i+1}: {len(coords)} elements detected")
    
    # Find common elements (based on position similarity)
    def boxes_similar(box1, box2, threshold=50):
        """Check if two boxes are similar (within threshold pixels)."""
        return all(abs(box1[i] - box2[i]) < threshold for i in range(4))
    
    # Group similar boxes across runs
    all_boxes = []
    for run_idx, (coords, _) in enumerate(all_results):
        for box in coords:
            all_boxes.append((run_idx, box))
    
    # Find boxes that appear in multiple runs
    consistent_boxes = []
    used = set()
    
    for i, (run1, box1) in enumerate(all_boxes):
        if i in used:
            continue
        
        similar_boxes = [(run1, box1)]
        used.add(i)
        
        for j, (run2, box2) in enumerate(all_boxes):
            if j in used or run1 == run2:
                continue
            
            if boxes_similar(box1, box2):
                similar_boxes.append((run2, box2))
                used.add(j)
        
        if len(set(run for run, _ in similar_boxes)) > 1:
            consistent_boxes.append(similar_boxes)
    
    # Report consistency
    print(f"\n{len(consistent_boxes)} elements found in multiple runs:")
    
    for idx, similar_group in enumerate(consistent_boxes):
        runs = set(run + 1 for run, _ in similar_group)
        
        # Calculate average box manually
        boxes = [box for _, box in similar_group]
        avg_box = []
        for i in range(4):
            avg_val = sum(box[i] for box in boxes) / len(boxes)
            avg_box.append(int(avg_val))
        
        print(f"\nElement {idx + 1} (found in runs: {sorted(runs)}):")
        print(f"  Average position: {avg_box}")
        
        # Show variance
        if len(similar_group) > 1:
            # Calculate variance manually
            variance = []
            for i in range(4):
                vals = [box[i] for box in boxes]
                mean = sum(vals) / len(vals)
                var = sum((v - mean) ** 2 for v in vals) / len(vals)
                variance.append(int(var ** 0.5))  # Standard deviation
            print(f"  Position variance (std dev): {variance}")
    
    # Elements unique to specific runs
    print("\n\nElements unique to specific runs:")
    for run_idx in range(len(all_results)):
        unique_count = sum(1 for r, _ in all_boxes if r == run_idx and 
                          all((r, b) not in any_group for any_group in consistent_boxes 
                              for r, b in any_group))
        if unique_count > 0:
            print(f"  Run {run_idx + 1}: {unique_count} unique elements")


async def main():
    # Initialize detector
    detector = GeminiDetector(api_key=GEMINI_API_KEY)
    
    # Use a test screenshot
    screenshot_path = "/home/ubuntu/browser_automation/screenshots/modal_to_close.png"
    
    if not os.path.exists(screenshot_path):
        print(f"Screenshot not found: {screenshot_path}")
        print("Please ensure the screenshot exists or update the path.")
        return
    
    print(f"Using screenshot: {screenshot_path}")
    print(f"Using EXACT prompt from bb_detector.html: '{EXACT_PROMPT}'")
    print("\nRunning 3 identical detection attempts...\n")
    
    # Store all results
    all_results = []
    
    # Run detection 3 times with the EXACT same prompt
    for run_num in range(1, 4):
        print(f"\n{'='*60}")
        print(f"RUN {run_num}")
        print('='*60)
        
        try:
            # Use the EXACT prompt from bb_detector.html
            result = await detector.detect_elements(screenshot_path, EXACT_PROMPT)
            
            if result and 'coordinates' in result:
                coords = result['coordinates']
                print(f"Run {run_num}: Detected {len(coords)} bounding boxes")
                
                # Store results
                all_results.append((coords, result.get('raw_response', '')))
                
                # Generate timestamp for unique filenames
                timestamp = int(time.time())
                
                # Save outputs with dual annotation
                bbox_output = f"/home/ubuntu/browser_automation/screenshots/run{run_num}_smart_bboxes_{timestamp}.png"
                crosshair_output = f"/home/ubuntu/browser_automation/screenshots/run{run_num}_smart_crosshairs_{timestamp}.png"
                
                draw_bounding_boxes_with_labels(screenshot_path, coords, bbox_output)
                draw_crosshairs(screenshot_path, coords, crosshair_output)
                
                # Save raw response for analysis
                raw_output = f"/home/ubuntu/browser_automation/screenshots/run{run_num}_raw_response.json"
                with open(raw_output, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"Saved raw response: {raw_output}")
                
            else:
                print(f"Run {run_num}: No bounding boxes detected")
                all_results.append(([], ''))
                
        except Exception as e:
            print(f"Run {run_num} error: {str(e)}")
            all_results.append(([], ''))
        
        # Small delay between runs
        if run_num < 3:
            await asyncio.sleep(2)
    
    # Analyze consistency
    analyze_consistency(all_results)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nCheck the screenshots directory for:")
    print("- run1_smart_bboxes_*.png, run2_smart_bboxes_*.png, run3_smart_bboxes_*.png")
    print("- run1_smart_crosshairs_*.png, run2_smart_crosshairs_*.png, run3_smart_crosshairs_*.png")
    print("- run1_raw_response.json, run2_raw_response.json, run3_raw_response.json")
    print("\nCompare these images to see the variance in detection across runs.")


if __name__ == "__main__":
    asyncio.run(main())