# Gemini Coordinate Normalization Fix

## Issue
Gemini Vision API returns bounding box coordinates in a normalized format (0-1000 scale) that need to be converted to actual pixel coordinates before using them for clicking. Without this normalization, clicks happen at incorrect positions.

## Root Cause
Gemini returns coordinates as `[ymin, xmin, ymax, xmax]` where each value is in the range 0-1000, representing a percentage of the image dimensions. To get actual pixel positions, these values must be:
1. Divided by 1000 to get a fraction (0-1)
2. Multiplied by the actual image dimension (width or height)

## Formula
```python
pixel_x = gemini_x / 1000 * image_width
pixel_y = gemini_y / 1000 * image_height
```

## Files Fixed

### 1. `/home/ubuntu/browser_automation/scripts/fuzzycode_steps/gemini_element_matcher.py`
- **Issue**: Lines 68-69 were calculating center coordinates without normalization
- **Fix**: Added image dimension retrieval and proper normalization formula

### 2. `/home/ubuntu/browser_automation/scripts/close_modal_with_gemini.py`
- **Issue**: Lines 40-41 and 48-49 were using raw coordinates
- **Fix**: Added PIL Image import, retrieved dimensions, and applied normalization throughout

## Files Already Correct
- `/home/ubuntu/browser_automation/scripts/fuzzycode_steps/bbox_visualizer.py` - Line 428 correctly normalizes
- `/home/ubuntu/browser_automation/scripts/fuzzycode_steps/gemini_crosshair_matcher.py` - Lines 76-77 and 170-171 correctly normalize
- `/home/ubuntu/browser_automation/clients/gemini_detector.py` - Has correct `convert_to_playwright_coords` method

## Testing
Created `/home/ubuntu/browser_automation/test_coordinate_normalization.py` which:
1. Creates a test page with a button
2. Uses Gemini to detect the button
3. Compares raw vs normalized coordinates
4. Visualizes both to show the difference
5. Clicks using normalized coordinates with crosshair verification

## Results
- Raw coordinates: `[ymin=147, xmin=76, ymax=208, xmax=234]`
- Normalized pixel coordinates: `[x1=97, y1=105, x2=299, y2=149]`
- Center click position: `(198, 127)` - correctly positioned at button center

## Best Practices
1. **Always normalize Gemini coordinates** before using them for clicking or positioning
2. **Use the GeminiDetector.convert_to_playwright_coords()** method when available
3. **Get image dimensions** using PIL Image when manually calculating positions
4. **Test with crosshair visualization** to verify click positions are correct

## Example Code
```python
from PIL import Image

# Get image dimensions
img = Image.open(screenshot_path)
width, height = img.size

# Normalize Gemini coordinates
ymin, xmin, ymax, xmax = gemini_coords
center_x = int((xmin + xmax) / 2 / 1000 * width)
center_y = int((ymin + ymax) / 2 / 1000 * height)

# Click at normalized position
await client.click_at(x=center_x, y=center_y)
```