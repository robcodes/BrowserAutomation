# Playwright Navigation Best Practices

## Core Limitations
1. **Cannot see screenshots during execution** - must write blind, review after
2. **Cannot maintain browser session between executions** - each script run is a new session

## Navigation Strategy

### 1. Checkpoint Method (Recommended)
```python
# Step 1: Initial reconnaissance
nav.start_session(url)
nav.take_screenshot("initial")
nav.save_checkpoint()
# STOP - Review screenshots

# Step 2: Informed navigation based on analysis
nav.continue_from_checkpoint()
```

### 2. Multi-Selector Approach
```python
# Try multiple selectors for same element
selectors = [
    'button:has-text("Submit")',
    'button[type="submit"]',
    '.submit-btn',
    'button.primary'
]
for selector in selectors:
    if element_exists(selector):
        click(selector)
        break
```

### 3. Screenshot Everything
```python
# Take screenshots at EVERY action
nav.fill_input(selector, text)
nav.take_screenshot(f"after_fill_{timestamp}")
nav.click_element(selector)
nav.take_screenshot(f"after_click_{timestamp}")
```

## Element Detection

### Text-based Selection (Most Reliable)
```python
# Prefer text content over classes/IDs
'button:has-text("Exact Text")'
'a:has-text("Link Text")'
```

### Wait Strategies
```python
# Always wait after actions
page.wait_for_load_state('networkidle')
page.wait_for_timeout(2000)  # Additional buffer
```

### State Analysis
```python
def analyze_current_state():
    return {
        "url": page.url,
        "title": page.title(),
        "buttons": len(page.locator('button').all()),
        "links": len(page.locator('a').all()),
        "inputs": len(page.locator('input, textarea').all()),
        "visible_text": page.locator('body').inner_text()[:500]
    }
```

## Error Handling

### Defensive Clicking
```python
try:
    element.click()
except:
    element.click(force=True)  # Force if covered
except:
    element.dispatch_event('click')  # JavaScript fallback
```

### Visibility Checks
```python
if element.is_visible() and element.is_enabled():
    element.click()
```

## Dynamic Content

### API/AJAX Waiting
```python
# For sites with API calls
page.wait_for_response(lambda r: 'api' in r.url)
page.wait_for_timeout(3000)  # Extra time for rendering
```

### Progressive Enhancement
```python
# Start simple, add complexity
basic_selectors = ['button', 'a', 'input']
specific_selectors = ['button.primary', 'a.nav-link']
complex_selectors = ['button:has-text("Submit"):visible']
```

## Navigation Patterns

### Single Page Apps (SPAs)
```python
# Check URL changes
initial_url = page.url
click_element()
if page.url == initial_url:
    # SPA - check for DOM changes instead
    check_dom_mutations()
```

### Form Interaction
```python
# Fill → Screenshot → Submit → Wait → Screenshot
fill_form_fields()
take_screenshot("form_filled")
submit_form()
wait_for_response()
take_screenshot("form_submitted")
```

## Debugging Tools

### Console Log Capture (Enhanced Server v2.0)
```python
# Automatic console capture with enhanced browser server
from browser_client_enhanced import EnhancedBrowserClient

client = EnhancedBrowserClient()

# After failed action, check console
errors = await client.get_errors()
if errors["errors"]:
    for error in errors["errors"]:
        print(f"[{error['type']}] {error['text']}")

# Get logs from specific time range
recent_logs = await client.get_console_logs(
    since=datetime.now() - timedelta(seconds=5),
    types=["error", "warning"]
)

# Search for specific patterns
api_logs = await client.get_console_logs(text_contains="api")
```

### Comprehensive Logging
```python
{
    "step": step_number,
    "action": "click",
    "selector": selector_used,
    "success": True/False,
    "screenshot": filename,
    "console_errors": len(errors["errors"]),
    "network_failures": len(network_failures),
    "state_after": analyze_current_state()
}
```

### Debugging Failed Actions
```python
async def debug_action_failure(client, action_name):
    """Helper to understand why an action failed"""
    # Check JavaScript errors
    await client.print_recent_errors()
    
    # Check network failures
    network = await client.get_network_logs(limit=20)
    failures = [log for log in network["logs"] if log.get("failure")]
    
    # Check recent console activity
    logs = await client.get_console_logs(limit=10)
    
    return {
        "action": action_name,
        "js_errors": errors["count"],
        "network_failures": len(failures),
        "recent_logs": logs["logs"][-5:]
    }
```

### Selector Testing
```python
# Test all selectors before use
def find_working_selector(selectors):
    for sel in selectors:
        if page.locator(sel).count() > 0:
            return sel
    return None
```

## Session Persistence

### Save State
```python
state = {
    "url": page.url,
    "cookies": page.context.cookies(),
    "localStorage": page.evaluate("() => Object.entries(localStorage)"),
    "form_data": page.evaluate("""() => 
        Array.from(document.querySelectorAll('input, textarea')).map(el => ({
            selector: '#' + el.id || '[name="' + el.name + '"]',
            value: el.value
        }))
    """)
}
```

### Restore State
```python
# Navigate to URL
page.goto(state["url"])

# Restore cookies
page.context.add_cookies(state["cookies"])

# Restore localStorage
for key, value in state["localStorage"]:
    page.evaluate(f"localStorage.setItem('{key}', '{value}')")

# Restore form data
for field in state["form_data"]:
    page.fill(field["selector"], field["value"])
```

## Quick Reference

```python
# Essential imports
from playwright.sync_api import sync_playwright
import time, json, os

# Basic navigation template
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Navigate
    page.goto(url)
    page.wait_for_load_state('networkidle')
    
    # Interact
    page.fill('selector', 'text')
    page.click('selector')
    
    # Capture
    page.screenshot(path='screenshot.png')
    
    browser.close()
```

## Future Improvements
- [ ] Implement visual regression testing
- [ ] Add OCR for screenshot text extraction
- [ ] Build selector reliability database
- [ ] Create site-specific navigation profiles