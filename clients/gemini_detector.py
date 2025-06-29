#!/usr/bin/env python3
"""
Enhanced Gemini Vision API integration for detecting UI elements and their bounding boxes
in screenshots. Supports structured output with labels and model-specific prompts.
"""
import base64
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import io
import sys

# Add server directory to path for bbox_visualizer
sys.path.append(str(Path(__file__).parent.parent / "server"))


class BoundingBox:
    """
    Represents a bounding box with its 2D coordinates and associated label.
    """
    def __init__(self, box_2d: List[int], label: str):
        self.box_2d = box_2d  # [y_min, x_min, y_max, x_max]
        self.label = label
    
    def to_dict(self):
        return {"box_2d": self.box_2d, "label": self.label}


class GeminiDetector:
    # Model-specific system prompts
    SYSTEM_PROMPTS = {
        "gemini-2.0-flash-exp": """Return bounding boxes for icons, svgs, clickable elements, buttons, etc as an array with labels.
Never return masks. Limit to 25 objects.
If an object is present multiple times, give each object a unique label
according to its distinct characteristics (action, colors, size, position, etc..).
Exclude anything that is grayed out.""",
        
        "gemini-2.5-flash": """Return bounding boxes as an array with labels.
Never return masks.
If an object is present multiple times, give each object a unique label
according to its distinct characteristics (action, colors, size, position, etc..).

IGNORE ANYTHING NOT IN FOCUS"""
    }
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = model
        
    def get_system_prompt(self, model: Optional[str] = None) -> str:
        """Get the appropriate system prompt for the model"""
        model_to_use = model or self.model
        # Default to 2.5 prompt if model not in list
        return self.SYSTEM_PROMPTS.get(model_to_use, self.SYSTEM_PROMPTS["gemini-2.5-flash"])
        
    async def detect_elements(self, 
                            image_path: str, 
                            user_prompt: str = "",
                            system_prompt: Optional[str] = None,
                            save_annotated: bool = True,
                            return_labels: bool = True,
                            num_calls: int = 1) -> Dict:
        """
        Detect elements in a screenshot using Gemini Vision API with enhanced features
        
        Args:
            image_path: Path to the screenshot
            user_prompt: Optional user prompt to add context (e.g. "Find the close button")
            system_prompt: Override the default system prompt if provided
            save_annotated: Whether to save annotated image with bounding boxes
            return_labels: Whether to request labels with bounding boxes
            num_calls: Number of API calls to make (for consistency checking)
            
        Returns:
            Dict containing:
                - coordinates: List of [ymin, xmin, ymax, xmax] arrays
                - labels: List of labels (if return_labels=True)
                - bounding_boxes: List of BoundingBox objects
                - annotated_image_path: Path to annotated image (if saved)
                - raw_response: Full API response text (or list if num_calls > 1)
                - results: List of all results if num_calls > 1
        """
        # Use appropriate system prompt
        if system_prompt is None:
            system_prompt = self.get_system_prompt()
        
        # Combine system and user prompts
        full_prompt = system_prompt
        if user_prompt:
            full_prompt += f"\n\nAdditional context: {user_prompt}"
        
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # Make multiple API calls if requested
        all_results = []
        
        for call_num in range(num_calls):
            # Prepare API request
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": full_prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_data
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.5,
                    "candidateCount": 1,
                }
            }
            
            # Make API request
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
            
            # Parse the response
            parsed_result = self._parse_response(response_text, return_labels)
            parsed_result['raw_response'] = response_text
            parsed_result['call_number'] = call_num + 1
            
            all_results.append(parsed_result)
        
        # Consolidate results
        if num_calls == 1:
            final_result = all_results[0]
        else:
            # Use the first successful result, but include all results
            final_result = all_results[0]
            final_result['results'] = all_results
        
        # Create annotated image if requested
        if save_annotated and final_result['coordinates']:
            # Use the enhanced bbox_visualizer
            from bbox_visualizer import visualize
            
            # Prepare data for visualization
            viz_data = {
                'coordinates': final_result['coordinates']
            }
            if 'labels' in final_result:
                viz_data['labels'] = final_result['labels']
            
            annotated_path = visualize(
                image_path,
                json_data=viz_data,
                mode='bbox',
                output_path=str(Path(image_path).parent / f"{Path(image_path).stem}_annotated.png")
            )
            final_result['annotated_image_path'] = annotated_path
        
        return final_result
    
    def _parse_response(self, response_text: str, return_labels: bool) -> Dict[str, Any]:
        """Parse the response text to extract bounding boxes and labels"""
        result = {
            'coordinates': [],
            'bounding_boxes': []
        }
        
        if return_labels:
            result['labels'] = []
        
        # Try to parse as JSON first (structured output)
        try:
            # Clean up markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            # Parse JSON
            parsed_json = json.loads(cleaned_text)
            
            # Handle different response formats
            if isinstance(parsed_json, list):
                # List of bounding boxes
                for item in parsed_json:
                    if isinstance(item, dict):
                        # Structured format with box_2d and label
                        if 'box_2d' in item:
                            coords = item['box_2d']
                            label = item.get('label', f'Object {len(result["coordinates"]) + 1}')
                            
                            result['coordinates'].append(coords)
                            result['bounding_boxes'].append(BoundingBox(coords, label))
                            if return_labels:
                                result['labels'].append(label)
                    elif isinstance(item, list) and len(item) == 4:
                        # Simple coordinate array
                        result['coordinates'].append(item)
                        label = f'Object {len(result["coordinates"])}'
                        result['bounding_boxes'].append(BoundingBox(item, label))
                        if return_labels:
                            result['labels'].append(label)
            
            elif isinstance(parsed_json, dict):
                # Single bounding box
                if 'box_2d' in parsed_json:
                    coords = parsed_json['box_2d']
                    label = parsed_json.get('label', 'Object 1')
                    
                    result['coordinates'].append(coords)
                    result['bounding_boxes'].append(BoundingBox(coords, label))
                    if return_labels:
                        result['labels'].append(label)
                        
        except json.JSONDecodeError:
            # Fall back to regex extraction
            result['coordinates'] = self._extract_coordinates(response_text)
            
            # Create default labels
            for i, coords in enumerate(result['coordinates']):
                label = f'Object {i + 1}'
                result['bounding_boxes'].append(BoundingBox(coords, label))
                if return_labels:
                    result['labels'].append(label)
        
        return result
    
    def _extract_coordinates(self, text: str) -> List[List[int]]:
        """Extract coordinate arrays from response text using regex"""
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
        user_prompt = f"Find the {element_description} in this image. Focus only on this specific element."
        
        return await self.detect_elements(
            image_path, 
            user_prompt=user_prompt,
            save_annotated=save_annotated,
            return_labels=True
        )
    
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


# Convenience function for backward compatibility
async def detect_elements_simple(image_path: str, api_key: str, prompt: str = None) -> Dict:
    """Simple detection function for backward compatibility"""
    detector = GeminiDetector(api_key=api_key)
    
    if prompt is None:
        prompt = "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all clickable elements"
    
    # Use the old simple prompt style
    result = await detector.detect_elements(
        image_path,
        system_prompt=prompt,
        save_annotated=True,
        return_labels=False
    )
    
    return {
        'coordinates': result['coordinates'],
        'annotated_image_path': result.get('annotated_image_path'),
        'raw_response': result['raw_response']
    }


# Example usage
async def example_usage():
    # Initialize with API key and model
    detector = GeminiDetector(
        api_key="YOUR_API_KEY",
        model="gemini-2.0-flash-exp"  # or "gemini-2.5-flash"
    )
    
    # Example 1: Detect all clickable elements with default prompts
    result = await detector.detect_elements(
        "screenshot.png",
        save_annotated=True
    )
    
    print(f"Found {len(result['coordinates'])} elements")
    if 'labels' in result:
        for i, (coords, label) in enumerate(zip(result['coordinates'], result['labels'])):
            print(f"  {i+1}. {label}: {coords}")
    
    # Example 2: Find specific element with user prompt
    close_button = await detector.find_element(
        "screenshot.png",
        "X button to close the modal in the top right"
    )
    
    # Example 3: Custom user prompt for specific elements
    result = await detector.detect_elements(
        "screenshot.png",
        user_prompt="Focus on the login form elements: username field, password field, and sign in button",
        save_annotated=True
    )
    
    # Example 4: Multiple calls for consistency
    result = await detector.detect_elements(
        "screenshot.png",
        num_calls=3,
        save_annotated=True
    )
    if 'results' in result:
        print(f"Made {len(result['results'])} API calls")


if __name__ == "__main__":
    print("Enhanced Gemini Detector module loaded.")
    print("Features:")
    print("- Model-specific system prompts (2.0 and 2.5)")
    print("- Structured output with labels")
    print("- Custom user prompts for context")
    print("- Multiple API calls for consistency")
    print("- Advanced visualization with non-overlapping labels")