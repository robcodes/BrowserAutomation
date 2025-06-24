# Browser Automation Techniques

## 🚨 CRITICAL: Script Organization

### ALWAYS Use Step-by-Step Modular Scripts

**The ONLY acceptable pattern for browser automation is modular step scripts:**

```python
# ✅ CORRECT: Modular steps
step01_navigate.py      # Navigate to site
step02_open_modal.py    # Open specific modal
step03_fill_form.py     # Fill form fields
step04_submit.py        # Submit and verify

# ❌ WRONG: Monolithic scripts
complete_automation.py  # Tries to do everything
full_login_flow.py     # Too many steps in one file
```

**Why modular steps?**
1. Easy to debug - run individual steps
2. Reusable - each step works independently
3. Verifiable - screenshots at each step
4. Maintainable - fix one step without breaking others

**Reference implementation:** `/browser_automation/scripts/fuzzycode_steps/`
**Detailed guide:** `/browser_automation/docs/STEP_BY_STEP_GUIDE.md`

## Form Handling

### The Direct Array Access Pattern
```javascript
// Instead of complex selectors that might fail:
// ❌ document.querySelector('input[type="email"][placeholder*="email"]')

// Use direct array access:
// ✅ const inputs = document.querySelectorAll('input');
//    inputs[0].value = 'username';
//    inputs[1].value = 'password';
```

### Form Validation
- Check ALL fields with `form.checkValidity()`
- Hidden required fields WILL block submission
- Look for all inputs, not just visible ones
- Fire both 'input' and 'change' events

## Debugging Techniques

### Console Log Analysis
```python
# Always check console logs when automation fails
logs = await client.get_console_logs(limit=20)
errors = [log for log in logs["logs"] if log["type"] == "error"]
```

### Network Monitoring
- 401 errors indicate authentication required
- 403 errors suggest permission issues
- Empty responses may indicate client-side rendering

### Screenshot Strategy
- Before action: Verify current state
- After action: Confirm it worked
- On failure: Capture for debugging

## Modal/Overlay Handling

### Priority Order
1. Try close button (X, ×, or aria-label="close")
2. Try backdrop/overlay click
3. Try ESC key press
4. Last resort: Reload page (maintains cookies)

### Modal Detection
```javascript
const hasModal = document.querySelector('.modal, [role="dialog"]')?.offsetParent !== null;
const hasOverlay = document.querySelector('[class*="backdrop"], [class*="overlay"]')?.offsetParent !== null;
```

## Element Finding Strategies

### When Standard Selectors Fail
1. **Bounding Box Detection**
   ```javascript
   const rect = element.getBoundingClientRect();
   if (rect.top < 100 && rect.right > window.innerWidth - 100) {
     // Element in top-right corner
   }
   ```

2. **Text Content Search**
   ```javascript
   Array.from(document.querySelectorAll('*'))
     .find(el => el.textContent.includes('Login'))
   ```

3. **Shadow DOM Check**
   ```javascript
   // Look for custom elements that might have shadow roots
   document.querySelectorAll('*').forEach(el => {
     if (el.shadowRoot) console.log('Shadow root found:', el);
   });
   ```

4. **Visual Detection with Gemini Vision API**
   ```python
   # When all else fails, use AI vision to find elements
   from scripts.gemini_click_helper import GeminiClickHelper
   
   # Initialize with your API key
   helper = GeminiClickHelper(client, "YOUR_GEMINI_API_KEY")
   
   # Find and click element by description
   success = await helper.click_element_by_description(
       session_id, page_id,
       "X button or close button in the modal header"
   )
   ```
   
   **Key Benefits:**
   - No CSS selectors needed
   - Works with dynamic elements
   - Natural language descriptions
   - Visual debugging with annotated images
   
   **See:** `/examples/gemini_vision/` for complete examples

## Iframe Handling

### Check Accessibility First
```javascript
try {
  const iframeDoc = iframe.contentDocument;
  // Same-origin - can access
} catch (e) {
  // Cross-origin - blocked
}
```

### Working with Iframe Content
```javascript
const iframe = document.querySelector('iframe');
const iframeDoc = iframe.contentDocument;
const iframeInputs = iframeDoc.querySelectorAll('input');
```

## Common Pitfalls & Solutions

### Pitfall: Button Stays Disabled
**Solution**: Check ALL form fields, including hidden ones

### Pitfall: Click Doesn't Work
**Solution**: Element might be covered, scroll into view first

### Pitfall: Selector Works in Console but Not in Code
**Solution**: Page might not be fully loaded, add wait conditions

### Pitfall: Modal Won't Close
**Solution**: Try page reload - sessions persist through cookies

## Visible vs Headless Mode

### When to Use Visible Mode
```python
# Use headless=False to watch the browser
session_id = await client.create_session(headless=False)
```

Benefits:
- Watch automation in real-time
- Debug visual issues
- Demo to stakeholders
- Verify element interactions

### When to Use Headless Mode (Default)
```python
# Default is headless=True
session_id = await client.create_session()
```

Benefits:
- Faster execution
- Less resource intensive
- Runs on servers without display
- Better for CI/CD pipelines

## Best Practices

1. **Always Take Screenshots AND CHECK THEM YOURSELF**
   - Document each step
   - Essential for debugging
   - Proof of state changes
   - **CRITICAL**: Screenshots are the ONLY reliable verification
   - Programmatic checks (element.exists, form.valid) can LIE
   - Visual verification reveals what really happened
   - Look for error messages, loading states, actual results
   - Trust your eyes, not your code checks

2. **Check Console Logs**
   - Hidden errors revealed
   - API failures exposed
   - JavaScript exceptions caught

3. **Use Simple Selectors First**
   - ID selectors most reliable
   - Array access for forms
   - Text content as fallback

4. **Handle Failures Gracefully**
   - Don't continue if previous step failed
   - Capture state for debugging
   - Report specific error details