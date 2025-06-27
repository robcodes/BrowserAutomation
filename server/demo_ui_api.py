#!/usr/bin/env python3
"""
Demo script showing how to use the UI API endpoints programmatically
"""
import requests
import json
import base64
from pathlib import Path
import time

BASE_URL = "http://localhost:8000"

def demo_workflow():
    """Demonstrate the complete workflow using the API"""
    
    print("Browser Automation UI API Demo")
    print("=" * 50)
    
    # Step 1: Create a session
    print("\n1. Creating browser session...")
    session_resp = requests.post(f"{BASE_URL}/sessions", 
                                json={"browser_type": "chromium", "headless": False})
    if session_resp.status_code != 200:
        print(f"Failed to create session: {session_resp.text}")
        return
    
    session_data = session_resp.json()
    session_id = session_data["session_id"]
    print(f"   Session created: {session_id}")
    
    # Step 2: Create a page
    print("\n2. Creating page...")
    page_resp = requests.post(f"{BASE_URL}/sessions/{session_id}/pages")
    if page_resp.status_code != 200:
        print(f"Failed to create page: {page_resp.text}")
        return
        
    page_data = page_resp.json()
    page_id = page_data["page_id"]
    print(f"   Page created: {page_id}")
    
    # Step 3: Navigate to URL
    print("\n3. Navigating to fuzzycode.dev...")
    nav_resp = requests.post(f"{BASE_URL}/navigate_to",
                            json={
                                "session_id": session_id,
                                "page_id": page_id,
                                "url": "https://fuzzycode.dev"
                            })
    if nav_resp.status_code == 200:
        nav_data = nav_resp.json()
        print(f"   Navigated to: {nav_data['title']}")
    else:
        print(f"   Navigation failed: {nav_resp.text}")
    
    # Wait a bit for page to load
    time.sleep(3)
    
    # Step 4: Take screenshot
    print("\n4. Taking screenshot...")
    screenshot_resp = requests.get(f"{BASE_URL}/get_screenshot/{session_id}/{page_id}")
    if screenshot_resp.status_code != 200:
        print(f"Failed to take screenshot: {screenshot_resp.text}")
        return
        
    screenshot_data = screenshot_resp.json()
    screenshot_base64 = screenshot_data["screenshot"]
    print(f"   Screenshot captured at: {screenshot_data['timestamp']}")
    
    # Step 5: Detect bounding boxes
    print("\n5. Detecting elements with Gemini Vision...")
    detect_resp = requests.post(f"{BASE_URL}/screenshot_to_bounding_boxes",
                               json={
                                   "screenshot": screenshot_base64,
                                   "api_key": "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA",  # Replace with your key
                                   "prompt": "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc"
                               })
    
    if detect_resp.status_code != 200:
        print(f"   Detection failed: {detect_resp.text}")
        print("   Note: Replace the API key with your own Gemini API key")
        return
        
    detect_data = detect_resp.json()
    bounding_boxes = detect_data["coordinates"]
    print(f"   Detected {detect_data['count']} elements")
    print(f"   First 3 bounding boxes: {bounding_boxes[:3]}")
    
    # Step 6: Visualize as bounding boxes
    print("\n6. Creating bounding box visualization...")
    viz_resp = requests.post(f"{BASE_URL}/visualize_bounding_boxes",
                            json={
                                "screenshot": screenshot_base64,
                                "bounding_boxes": bounding_boxes,
                                "mode": "bbox"
                            })
    
    if viz_resp.status_code == 200:
        viz_data = viz_resp.json()
        # Save the visualization
        viz_image = viz_data["visualized_image"].split(',')[1]  # Remove data:image/png;base64,
        with open("/tmp/demo_bbox_visualization.png", "wb") as f:
            f.write(base64.b64decode(viz_image))
        print("   Visualization saved to: /tmp/demo_bbox_visualization.png")
    else:
        print(f"   Visualization failed: {viz_resp.text}")
    
    # Step 7: Visualize as crosshairs
    print("\n7. Creating crosshair visualization...")
    viz_resp = requests.post(f"{BASE_URL}/visualize_bounding_boxes",
                            json={
                                "screenshot": screenshot_base64,
                                "bounding_boxes": bounding_boxes,
                                "mode": "crosshair"
                            })
    
    if viz_resp.status_code == 200:
        viz_data = viz_resp.json()
        # Save the visualization
        viz_image = viz_data["visualized_image"].split(',')[1]
        with open("/tmp/demo_crosshair_visualization.png", "wb") as f:
            f.write(base64.b64decode(viz_image))
        print("   Visualization saved to: /tmp/demo_crosshair_visualization.png")
    
    # Step 8: Clean up
    print("\n8. Cleaning up...")
    cleanup_resp = requests.delete(f"{BASE_URL}/sessions/{session_id}")
    if cleanup_resp.status_code == 200:
        print("   Session closed successfully")
    
    print("\n" + "=" * 50)
    print("Demo complete! Check the visualizations in /tmp/")
    print("You can also access the web UI at: http://localhost:8000/ui")

if __name__ == "__main__":
    demo_workflow()