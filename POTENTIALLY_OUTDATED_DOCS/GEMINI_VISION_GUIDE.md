# Gemini Vision Integration Guide

## Overview

The Gemini Vision integration allows you to find and interact with UI elements using natural language descriptions and visual detection, solving problems where traditional CSS selectors fail.

## When to Use Gemini Vision

Use Gemini Vision when:
- Elements have no reliable CSS selectors
- Classes/IDs change dynamically
- You can see the element but can't target it programmatically
- Shadow DOM or iframes block access
- You want to describe elements naturally ("the blue submit button")

## Setup

### 1. Get an API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your key

### 2. Install Dependencies

```bash
pip install aiohttp pillow
```

## Basic Usage

### Simple Click Example

```python
from scripts.gemini_click_helper import GeminiClickHelper

# Initialize with your API key
helper = GeminiClickHelper(client, "YOUR_API_KEY")

# Click element by description
success = await helper.click_element_by_description(
    session_id, 
    page_id,
    "the blue submit button in the form"
)
```

### Find All Clickable Elements

```python
# Discover what's clickable on the page
result = await helper.find_all_clickable_elements(
    session_id,
    page_id,
    "all_elements.png"
)

print(f"Found {len(result['coordinates'])} clickable elements")
# Check the annotated image to see what was detected
```

## Advanced Usage

### Direct Detector Usage

For more control, use the detector directly:

```python
from clients.gemini_detector import GeminiDetector
from PIL import Image

# Initialize detector
detector = GeminiDetector(api_key="YOUR_KEY", model="gemini-2.5-flash")

# Find specific element
result = await detector.find_element(
    "screenshot.png",
    "the shopping cart icon in the header"
)

# Get coordinates
if result['coordinates']:
    coords = result['coordinates'][0]  # [ymin, xmin, ymax, xmax]
    
    # Convert to click position
    img = Image.open("screenshot.png")
    click_pos = detector.convert_to_playwright_coords(
        coords, img.width, img.height
    )
    
    print(f"Click at: x={click_pos['x']}, y={click_pos['y']}")
```

### Custom Detection Prompts

```python
# Detect specific types of elements
result = await detector.detect_elements(
    "screenshot.png",
    prompt="""Find all form input fields including:
    - Text inputs
    - Password fields
    - Email fields
    - Dropdown menus
    Return bounding boxes as [ymin, xmin, ymax, xmax]"""
)
```

## Integration Patterns

### Pattern 1: Fallback Strategy

```python
async def click_element(selector_or_description):
    # Try CSS selector first
    try:
        await client.click(selector_or_description)
        return True
    except:
        # Fall back to Gemini
        print(f"Selector failed, trying Gemini...")
        return await helper.click_element_by_description(
            session_id, page_id, selector_or_description
        )
```

### Pattern 2: Modal Closer

```python
async def close_any_modal():
    # Common descriptions that work
    descriptions = [
        "X button or close button in the modal",
        "close icon in the top right corner",
        "dismiss or cancel button"
    ]
    
    for desc in descriptions:
        if await helper.click_element_by_description(
            session_id, page_id, desc
        ):
            return True
    return False
```

### Pattern 3: Form Filler

```python
async def fill_form_field(field_description, value):
    # Find the field
    result = await detector.find_element(
        "form_screenshot.png",
        f"input field for {field_description}"
    )
    
    if result['coordinates']:
        coords = result['coordinates'][0]
        click_pos = detector.convert_to_playwright_coords(...)
        
        # Click to focus
        await client.evaluate(f"""
            document.elementFromPoint({click_pos['x']}, {click_pos['y']}).click();
        """)
        
        # Type the value
        await client.type(value)
```

## Best Practices

### 1. Be Specific in Descriptions

```python
# ❌ Too vague
"button"

# ✅ Specific
"blue submit button at the bottom of the login form"
```

### 2. Use Visual Context

```python
# ❌ No context
"X button"

# ✅ With context  
"X close button in the top-right corner of the modal dialog"
```

### 3. Check Annotated Images

Always review the annotated images to verify detection:

```python
result = await detector.find_element(screenshot_path, description)
if result['annotated_image_path']:
    print(f"Review detection at: {result['annotated_image_path']}")
```

### 4. Handle Multiple Matches

```python
# When multiple elements match
all_results = await detector.detect_elements(...)
if len(all_results['coordinates']) > 1:
    print(f"Found {len(all_results['coordinates'])} matches")
    # Use the first one or iterate through them
```

## Debugging

### Enable Visual Feedback

```python
# Always save annotated images when debugging
result = await detector.find_element(
    screenshot_path,
    element_description,
    save_annotated=True  # Creates annotated image
)
```

### Check Raw Response

```python
# See exactly what Gemini detected
print("Gemini says:", result['raw_response'])
```

### Verify Coordinates

```python
# Log coordinate conversions
coords = result['coordinates'][0]
print(f"Bounding box: {coords}")
print(f"Image size: {img.width}x{img.height}")
print(f"Click position: {click_pos}")
```

## Common Issues

### Issue: "No element found"
- Make element description more specific
- Check if element is visible in screenshot
- Try alternative descriptions

### Issue: "Wrong element clicked"
- Review annotated image
- Add more context to description
- Specify position ("top-right", "bottom of form")

### Issue: "API overloaded"
- Gemini has rate limits
- Add retry logic with delays
- Cache results when possible

## Performance Tips

1. **Batch Detection**: Find all elements at once rather than multiple API calls
2. **Cache Screenshots**: Reuse screenshots when checking multiple elements
3. **Selective Usage**: Use CSS selectors when possible, Gemini as fallback
4. **Parallel Processing**: Process multiple screenshots concurrently

## Example: Complete Modal Handler

```python
async def handle_modal_with_gemini(client, session_id, page_id):
    """Complete example of modal handling"""
    
    # 1. Detect if modal exists
    await client.screenshot("check_modal.png")
    
    # 2. Find close button
    helper = GeminiClickHelper(client, API_KEY)
    
    # 3. Try multiple descriptions
    descriptions = [
        "X or × button in the modal header",
        "close button in top-right of dialog",
        "dismiss or close icon"
    ]
    
    for desc in descriptions:
        print(f"Trying: {desc}")
        success = await helper.click_element_by_description(
            session_id, page_id, desc, 
            f"modal_attempt_{descriptions.index(desc)}.png"
        )
        
        if success:
            print("✅ Modal closed!")
            break
    else:
        print("❌ Could not find close button")
        
        # Last resort: find all clickable elements
        all_elements = await helper.find_all_clickable_elements(
            session_id, page_id
        )
        print(f"Found {len(all_elements['coordinates'])} clickable elements")
        print("Check annotated image for manual selection")
```

## API Configuration

- **Recommended Model**: `gemini-2.5-flash`
- **Alternative Models**: `gemini-2.0-flash-exp`, `gemini-1.5-flash`
- **Rate Limits**: Check Google AI Studio for your limits
- **Best Performance**: Use specific, descriptive prompts

## Further Resources

- [Google AI Studio](https://makersuite.google.com/)
- [Gemini API Documentation](https://ai.google.dev/)
- Example implementations: `/browser_automation/examples/gemini_vision/`
- Core implementation: `/browser_automation/clients/gemini_detector.py`