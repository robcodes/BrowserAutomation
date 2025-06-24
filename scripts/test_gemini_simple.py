#!/usr/bin/env python3
"""Simple test of Gemini consistency - just find X button 5 times"""
import asyncio
import sys
from pathlib import Path
import time
sys.path.append(str(Path(__file__).parent.parent))

from clients.gemini_detector import GeminiDetector

GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"

async def main():
    detector = GeminiDetector(GEMINI_API_KEY)
    screenshot_path = "/home/ubuntu/browser_automation/screenshots/find_all_test.png"
    
    print("Testing Gemini X button detection (5 attempts)")
    print("="*50)
    
    results = []
    
    for i in range(5):
        print(f"\nAttempt {i + 1}:")
        
        try:
            # Use a specific prompt for X button
            result = await detector.find_element(
                screenshot_path,
                "the X close button (not the expand button) in the modal header"
            )
            
            if result['coordinates']:
                coords = result['coordinates'][0]
                print(f"  Found at: {coords}")
                
                # Check if it's in the right area
                ymin, xmin, ymax, xmax = coords
                if xmin > 900:  # Right side
                    if 940 < xmin < 980:  # More specific range
                        print(f"  ✓ Correct position for X button")
                        results.append("correct")
                    else:
                        print(f"  ? Right side but might be wrong button")
                        results.append("maybe")
                else:
                    print(f"  ✗ Wrong position")
                    results.append("wrong")
            else:
                print(f"  ✗ No coordinates found")
                results.append("none")
                
        except Exception as e:
            if "overloaded" in str(e):
                print(f"  - API overloaded")
                results.append("overloaded")
            else:
                print(f"  - Error: {e}")
                results.append("error")
        
        # Wait 20 seconds between attempts
        if i < 4:
            print("  Waiting 20 seconds...")
            await asyncio.sleep(20)
    
    # Summary
    print("\n" + "="*50)
    print("RESULTS SUMMARY:")
    print(f"  Correct: {results.count('correct')}/5")
    print(f"  Maybe: {results.count('maybe')}/5")
    print(f"  Wrong: {results.count('wrong')}/5") 
    print(f"  None: {results.count('none')}/5")
    print(f"  Overloaded: {results.count('overloaded')}/5")
    print(f"  Other errors: {results.count('error')}/5")

if __name__ == "__main__":
    asyncio.run(main())