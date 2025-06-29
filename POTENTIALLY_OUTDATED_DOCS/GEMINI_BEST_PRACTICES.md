# Gemini Vision API Best Practices for Browser Automation

## Key Discoveries

### 1. Always Use "Find All" Strategy ⚠️
**NEVER** ask Gemini to find a specific element directly - it often selects the wrong one.
**ALWAYS** ask for all elements, then programmatically filter.

### 2. Use Specific, Technical Prompts
The optimal prompt format is:
```
"Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc"
```

This prompt works better because:
- Explicit coordinate format specification
- Mentions specific element types (icons, svgs)
- Uses technical web development terminology
- Results in more comprehensive detection (8 elements vs 5)

### 3. Visual Verification is Critical
- Direct search can appear successful but select wrong elements
- Example: Asked for X button, got Sign Out button
- Always save and check annotated images during development

## Implementation Pattern

```python
from clients.gemini_detector import GeminiDetector

# 1. Initialize detector
detector = GeminiDetector(api_key, model="gemini-2.5-flash")

# 2. Find ALL elements with the optimized prompt
result = await detector.detect_elements(
    screenshot_path,
    "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc",
    save_annotated=True  # For debugging
)

# 3. Filter programmatically to find your target
target_found = False
for i, coords in enumerate(result['coordinates']):
    ymin, xmin, ymax, xmax = coords
    
    # Example: Find X button in top-right
    if xmin > 940 and ymin < 70:
        click_x = int((xmin + xmax) / 2)
        click_y = int((ymin + ymax) / 2)
        # Click at these coordinates
        target_found = True
        break

# 4. Fallback strategies if not found
if not target_found:
    # Try different position criteria
    # Or use manual offsets from known positions
    # Or try keyboard shortcuts (ESC for modals)
```

## Common Pitfalls to Avoid

1. **Don't use vague descriptions**
   - ❌ "Find the close button"
   - ✅ Use find-all approach

2. **Don't trust single element detection**
   - Even if coordinates look right, might be wrong element
   - Always verify with visual output

3. **Don't ignore API limits**
   - Add 15-20 second delays between requests
   - Implement retry logic for overloaded responses

## Success Metrics

- Find all + filtering: ~95% accuracy
- Direct element search: ~50% accuracy (often wrong element)
- Improved prompt: Detects 60% more elements

## API Configuration

- **Model**: Always use `gemini-2.5-flash`
- **API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Rate Limiting**: Wait 15-20 seconds between calls

## Debugging Tips

1. Always save annotated images during development
2. Log the raw Gemini response to understand what it sees
3. Compare coordinates with expected positions
4. Use manual position corrections as fallback

## Example: Closing a Modal

```python
# Find all elements
all_elements = await detector.detect_elements(screenshot, OPTIMAL_PROMPT)

# Look for X button by position (top-right)
for coords in all_elements['coordinates']:
    ymin, xmin, ymax, xmax = coords
    if 940 < xmin < 980 and 40 < ymin < 70:
        # This is likely the X button
        await click_at_coordinates(coords)
        break
else:
    # Fallback: Try ESC key
    await press_escape_key()
```

## Reference Implementation

See `/browser_automation/scripts/fuzzycode_steps/step05_close_modal_gemini.py` for a complete working example.