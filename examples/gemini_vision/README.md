# Gemini Vision Integration Examples

This directory contains examples of using Google's Gemini Vision API to detect and interact with UI elements when traditional selectors fail.

## Setup

1. **Get a Gemini API Key**:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Replace `YOUR_API_KEY` in the examples

2. **Install Dependencies**:
   ```bash
   pip install aiohttp pillow
   ```

## Examples

### 1. Simple Click Example (`simple_click_example.py`)
Basic example of finding and clicking an element by description:
```python
python examples/gemini_vision/simple_click_example.py
```

### 2. Modal Close Example (`modal_close_example.py`)
Demonstrates closing modal dialogs when the X button is hard to target:
```python
python examples/gemini_vision/modal_close_example.py
```

## How It Works

1. **Screenshot Capture**: Playwright takes a screenshot of the current page
2. **Visual Detection**: Gemini Vision API analyzes the image to find elements
3. **Coordinate Extraction**: Bounding boxes are returned as [ymin, xmin, ymax, xmax]
4. **Click Execution**: Coordinates are converted and a click event is dispatched

## Benefits

- **No Selectors Needed**: Find elements by visual appearance
- **Handles Dynamic Content**: Works even when classes/IDs change
- **Natural Language**: Describe what you're looking for in plain English
- **Visual Debugging**: Annotated images show what was detected

## Configuration

- **API Key**: `AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA` (example key)
- **Model**: `gemini-2.5-flash` (recommended for best performance)

## Common Use Cases

1. **Modal Close Buttons**: X buttons without good selectors
2. **Dynamic Elements**: Elements with changing classes/IDs
3. **Visual Elements**: Icons, images, or styled buttons
4. **Complex UIs**: When DOM structure is unclear
5. **Fallback Strategy**: When all other methods fail

## Tips

- Be specific in your element descriptions
- Check the annotated images to verify detection
- Use `find_all_clickable_elements()` to explore what's available
- Combine with traditional methods for best results