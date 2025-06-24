#!/usr/bin/env python3
"""Test Gemini's consistency by running multiple annotations on the same screenshot"""
import asyncio
import sys
from pathlib import Path
import time
sys.path.append(str(Path(__file__).parent.parent))

from clients.gemini_detector import GeminiDetector

GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def main():
    detector = GeminiDetector(GEMINI_API_KEY)
    
    # Use the last screenshot
    screenshot_path = "/home/ubuntu/browser_automation/screenshots/find_all_test.png"
    
    print("Testing Gemini consistency on the same screenshot")
    print("="*60)
    
    # Track results
    results = []
    
    for attempt in range(5):
        print(f"\nAttempt {attempt + 1} of 5")
        print("-"*40)
        
        try:
            # Find all clickable elements with the same prompt
            result = await detector.detect_elements(
                screenshot_path,
                """Find ALL clickable elements including:
                - ALL buttons (especially close/X buttons and expand/fullscreen buttons)
                - Links
                - Interactive icons
                - Any element that looks clickable
                Label each element clearly. For buttons with symbols, describe the symbol (X, ×, expand icon, etc).
                Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax]""",
                save_annotated=True  # Save annotated image for each attempt
            )
            
            print(f"Found {len(result['coordinates'])} elements")
            
            # Look for the X button position
            x_button_found = False
            x_button_position = None
            
            for i, coords in enumerate(result['coordinates']):
                ymin, xmin, ymax, xmax = coords
                # Check if this is in the X button area (based on our previous observation)
                if 940 < xmin < 980 and 40 < ymin < 70:
                    x_button_found = True
                    x_button_position = i + 1
                    print(f"✓ X button found as element {i + 1}: {coords}")
                
            if not x_button_found:
                print("✗ X button NOT found in expected position")
                # Check if it's detected elsewhere
                for i, coords in enumerate(result['coordinates']):
                    ymin, xmin, ymax, xmax = coords
                    if xmin > 900 and ymin < 100:
                        print(f"  ? Possible X button at element {i + 1}: {coords}")
            
            # Store results
            results.append({
                'attempt': attempt + 1,
                'total_elements': len(result['coordinates']),
                'x_button_found': x_button_found,
                'x_button_position': x_button_position,
                'all_coordinates': result['coordinates']
            })
            
            # Save annotated image with attempt number
            if result['annotated_image_path']:
                import shutil
                new_path = f"/home/ubuntu/browser_automation/screenshots/consistency_test_attempt_{attempt + 1}.png"
                shutil.copy(result['annotated_image_path'], new_path)
                print(f"Annotated image saved: consistency_test_attempt_{attempt + 1}.png")
            
        except Exception as e:
            print(f"Error in attempt {attempt + 1}: {e}")
            results.append({
                'attempt': attempt + 1,
                'error': str(e)
            })
        
        # Wait between attempts (except after the last one)
        if attempt < 4:
            wait_time = 30  # Increased to 30 seconds to avoid overload
            print(f"\nWaiting {wait_time} seconds before next attempt...")
            await asyncio.sleep(wait_time)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    successful_attempts = [r for r in results if 'error' not in r]
    x_button_detections = [r for r in successful_attempts if r['x_button_found']]
    
    print(f"Successful attempts: {len(successful_attempts)}/5")
    print(f"X button correctly detected: {len(x_button_detections)}/{len(successful_attempts)}")
    
    # Check consistency of total elements
    if successful_attempts:
        element_counts = [r['total_elements'] for r in successful_attempts]
        print(f"Element count consistency: {element_counts}")
        print(f"  Min: {min(element_counts)}, Max: {max(element_counts)}")
    
    # Check X button position consistency
    x_positions = [r['x_button_position'] for r in x_button_detections]
    if x_positions:
        print(f"X button positions: {x_positions}")
        if len(set(x_positions)) == 1:
            print("  ✓ X button consistently detected at same position")
        else:
            print("  ✗ X button detected at different positions")
    
    # Detailed results
    print("\nDetailed Results:")
    for r in results:
        if 'error' in r:
            print(f"  Attempt {r['attempt']}: ERROR - {r['error']}")
        else:
            print(f"  Attempt {r['attempt']}: {r['total_elements']} elements, X button: {'Yes' if r['x_button_found'] else 'No'}")
            if r['x_button_found']:
                x_coords = r['all_coordinates'][r['x_button_position'] - 1]
                print(f"    X button coords: {x_coords}")

if __name__ == "__main__":
    asyncio.run(main())