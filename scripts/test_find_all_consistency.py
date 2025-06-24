#!/usr/bin/env python3
"""Test consistency of the 'find all' approach"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from clients.gemini_detector import GeminiDetector

GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def main():
    detector = GeminiDetector(GEMINI_API_KEY)
    screenshot_path = "/home/ubuntu/browser_automation/screenshots/find_all_test.png"
    
    print("Testing 'Find All' approach consistency (5 attempts)")
    print("="*50)
    
    attempts = []
    
    for i in range(5):
        print(f"\nAttempt {i + 1}:")
        
        try:
            result = await detector.detect_elements(
                screenshot_path,
                "Find ALL clickable elements. Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax]"
            )
            
            print(f"  Found {len(result['coordinates'])} elements")
            
            # Look for X button in the results
            x_button_positions = []
            for j, coords in enumerate(result['coordinates']):
                ymin, xmin, ymax, xmax = coords
                # X button criteria: right side (xmin > 940) and top area (ymin < 100)
                if 940 < xmin < 980 and 40 < ymin < 70:
                    x_button_positions.append(j + 1)
                    print(f"  ✓ X button found at position {j + 1}: {coords}")
            
            if not x_button_positions:
                print(f"  ✗ X button not found in expected position")
                # Show what's in the top-right area
                for j, coords in enumerate(result['coordinates']):
                    ymin, xmin, ymax, xmax = coords
                    if xmin > 900 and ymin < 100:
                        print(f"    Element {j + 1} in top-right: {coords}")
            
            attempts.append({
                'success': True,
                'count': len(result['coordinates']),
                'x_positions': x_button_positions
            })
            
        except Exception as e:
            print(f"  Error: {str(e)[:50]}...")
            attempts.append({
                'success': False,
                'error': 'overloaded' if 'overloaded' in str(e) else 'other'
            })
        
        if i < 4:
            print("  Waiting 15 seconds...")
            await asyncio.sleep(15)
    
    # Analysis
    print("\n" + "="*50)
    print("ANALYSIS:")
    
    successful = [a for a in attempts if a['success']]
    print(f"\nSuccessful attempts: {len(successful)}/5")
    
    if successful:
        # Element count consistency
        counts = [a['count'] for a in successful]
        print(f"\nElement counts: {counts}")
        if len(set(counts)) == 1:
            print("  ✓ Consistent element count")
        else:
            print(f"  ✗ Inconsistent: min={min(counts)}, max={max(counts)}")
        
        # X button detection
        x_found = [len(a['x_positions']) > 0 for a in successful]
        print(f"\nX button found: {sum(x_found)}/{len(successful)} times")
        
        # Position consistency
        all_positions = []
        for a in successful:
            if a['x_positions']:
                all_positions.extend(a['x_positions'])
        
        if all_positions:
            print(f"X button positions: {all_positions}")
            if len(set(all_positions)) == 1:
                print("  ✓ Always at same position")
            else:
                print("  ✗ Found at different positions")

if __name__ == "__main__":
    asyncio.run(main())