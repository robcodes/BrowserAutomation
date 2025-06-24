#!/usr/bin/env python3
"""
Gemini Vision API integration for detecting UI elements and their bounding boxes
in screenshots. This helps locate clickable elements when selectors fail.
"""
import base64
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import io

class GeminiDetector:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = model  # Default to 2.5-flash which works best
        
    async def detect_elements(self, 
                            image_path: str, 
                            prompt: str = "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all clickable elements",
                            save_annotated: bool = True) -> Dict:
        """
        Detect elements in a screenshot using Gemini Vision API
        
        Args:
            image_path: Path to the screenshot
            prompt: What to look for in the image
            save_annotated: Whether to save annotated image with bounding boxes
            
        Returns:
            Dict containing:
                - coordinates: List of [ymin, xmin, ymax, xmax] arrays
                - annotated_image_path: Path to annotated image (if saved)
                - raw_response: Full API response text
        """
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # Prepare API request
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
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
        
        # Make API request with error handling
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
        
        # Check for API errors
        if 'error' in result:
            error_msg = result['error'].get('message', 'Unknown error')
            error_code = result['error'].get('code', 'Unknown')
            
            if error_code == 503 or 'overloaded' in error_msg:
                raise Exception(f"Gemini API overloaded. Please try again in a moment.")
            else:
                raise Exception(f"Gemini API error ({error_code}): {error_msg}")
        
        # Extract response text
        try:
            response_text = result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            raise Exception(f"Unexpected API response structure: {result}")
        
        # Extract coordinates
        coordinates = self._extract_coordinates(response_text)
        
        # Create annotated image if requested
        annotated_path = None
        if save_annotated and coordinates:
            annotated_path = self._create_annotated_image(
                image_path, 
                coordinates, 
                response_text
            )
        
        return {
            'coordinates': coordinates,
            'annotated_image_path': annotated_path,
            'raw_response': response_text
        }
    
    async def find_element(self, 
                          image_path: str, 
                          element_description: str,
                          save_annotated: bool = True) -> Dict:
        """
        Find a specific element in the screenshot
        
        Args:
            image_path: Path to the screenshot
            element_description: What element to find (e.g., "the close button", "the login form")
            save_annotated: Whether to save annotated image
            
        Returns:
            Dict with element coordinates and annotated image
        """
        prompt = f"""Find the {element_description} in this image and return its bounding box as a JSON array [ymin, xmin, ymax, xmax].
Also describe what you found and why you think it's the correct element."""
        
        return await self.detect_elements(image_path, prompt, save_annotated)
    
    def _extract_coordinates(self, text: str) -> List[List[int]]:
        """Extract coordinate arrays from response text"""
        # Pattern to match [ymin, xmin, ymax, xmax] arrays
        pattern = r'\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]'
        matches = re.findall(pattern, text)
        
        coordinates = []
        for match in matches:
            try:
                coords = json.loads(match)
                coordinates.append(coords)
            except json.JSONDecodeError:
                continue
                
        return coordinates
    
    def _create_annotated_image(self, 
                               image_path: str, 
                               coordinates: List[List[int]], 
                               response_text: str) -> str:
        """Create an annotated version of the image with bounding boxes"""
        # Open image
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        # Colors for different boxes
        colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan']
        
        # Draw bounding boxes
        for idx, coords in enumerate(coordinates):
            ymin, xmin, ymax, xmax = coords
            
            # Convert from 1000-scale to actual pixels
            actual_coords = [
                xmin * img.width / 1000,
                ymin * img.height / 1000,
                xmax * img.width / 1000,
                ymax * img.height / 1000
            ]
            
            color = colors[idx % len(colors)]
            
            # Draw rectangle
            draw.rectangle(actual_coords, outline=color, width=3)
            
            # Draw label
            label = f"Box {idx + 1}"
            draw.text((actual_coords[0], actual_coords[1] - 20), label, fill=color)
        
        # Save annotated image
        base_path = Path(image_path)
        annotated_path = base_path.parent / f"{base_path.stem}_annotated{base_path.suffix}"
        img.save(annotated_path)
        
        # Also save individual bounding box images
        for idx, coords in enumerate(coordinates):
            ymin, xmin, ymax, xmax = coords
            
            # Convert coordinates
            x1 = int(xmin * img.width / 1000)
            y1 = int(ymin * img.height / 1000)
            x2 = int(xmax * img.width / 1000)
            y2 = int(ymax * img.height / 1000)
            
            # Crop and save
            cropped = img.crop((x1, y1, x2, y2))
            crop_path = base_path.parent / f"{base_path.stem}_box{idx + 1}.png"
            cropped.save(crop_path)
        
        return str(annotated_path)
    
    def convert_to_playwright_coords(self, 
                                   coords: List[int], 
                                   image_width: int, 
                                   image_height: int) -> Dict[str, int]:
        """
        Convert Gemini coordinates to Playwright click coordinates
        
        Args:
            coords: [ymin, xmin, ymax, xmax] from Gemini
            image_width: Original image width
            image_height: Original image height
            
        Returns:
            Dict with x, y coordinates for center of bounding box
        """
        ymin, xmin, ymax, xmax = coords
        
        # Convert from 1000-scale to actual pixels
        x_center = ((xmin + xmax) / 2) * image_width / 1000
        y_center = ((ymin + ymax) / 2) * image_height / 1000
        
        return {
            'x': int(x_center),
            'y': int(y_center)
        }


# Example usage
async def example_usage():
    # API key that works: AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA
    # Model to use: gemini-2.5-flash
    detector = GeminiDetector(api_key="YOUR_API_KEY")
    
    # Detect all clickable elements
    result = await detector.detect_elements(
        "screenshot.png",
        "Find all buttons, links, and clickable elements. Return their bounding boxes as JSON arrays [ymin, xmin, ymax, xmax]"
    )
    
    print(f"Found {len(result['coordinates'])} elements")
    print(f"Annotated image saved to: {result['annotated_image_path']}")
    
    # Find specific element
    close_button = await detector.find_element(
        "screenshot.png",
        "close button (X button) in the modal header"
    )
    
    if close_button['coordinates']:
        coords = close_button['coordinates'][0]
        click_pos = detector.convert_to_playwright_coords(coords, 1920, 1080)
        print(f"Click at: {click_pos}")


if __name__ == "__main__":
    # This would need an actual API key to run
    # asyncio.run(example_usage())
    print("Gemini Detector module loaded. Use with your API key.")