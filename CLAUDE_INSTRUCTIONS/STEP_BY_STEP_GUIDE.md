# Step-by-Step Browser Automation Guide

## 🚨 THIS IS THE REQUIRED APPROACH

All browser automation MUST follow the step-by-step modular pattern demonstrated in `/scripts/fuzzycode_steps/`.

## Why Step-by-Step?

1. **Debuggable** - When step 4 fails, you know exactly where the problem is
2. **Verifiable** - Screenshots at each step prove what happened
3. **Reusable** - Step scripts work across different flows
4. **Maintainable** - Fix one step without touching others
5. **Reliable** - Each step verifies success before proceeding

## The Pattern

### 1. Create a `common.py` file
```python
# common.py - Shared utilities
TEST_USERNAME = "user@example.com"
TEST_PASSWORD = "password123"

async def take_screenshot_and_check(client, filename, description):
    await client.screenshot(filename)
    print(f"   ✓ Screenshot: {filename}")
    print(f"   📸 {description}")
    print(f"   ⚠️  CHECK: Verify the screenshot shows the expected state")
    # CRITICAL: This means YOU must look at the screenshot! Do NOT rely on programmatic checks alone!
```

### 2. Create numbered step files
```python
# step01_navigate.py
from common import *

async def step01_navigate(headless=True):
    print_step_header(1, "Navigate to Website")
    
    client = EnhancedBrowserClient()
    session_id = await client.create_session(headless=headless)
    
    # Navigate
    page_id = await client.new_page("https://example.com")
    await wait_and_check(client, WAIT_LONG, "Waiting for page load")
    
    # Screenshot
    await take_screenshot_and_check(
        client, 
        "step01_homepage.png",
        "Should show homepage with expected elements"
    )
    
    # Verify
    success = await check_element_exists(client, "#main-content", "Main content")
    
    # Save session
    await save_session_info(session_id, page_id, 1)
    
    return success
```

### 3. Create a runner
```python
# run_steps.py
from step01_navigate import step01_navigate
from step02_login import step02_login
# ... import all steps

STEPS = [
    ("Navigate", step01_navigate),
    ("Login", step02_login),
    # ... all steps
]

async def run_all_steps():
    for i, (name, func) in enumerate(STEPS):
        result = await func()
        if not result:
            print(f"Step {i+1} failed!")
            break
```

## Rules

### ✅ DO:
- One action per step
- Take screenshots before AND after actions
- **MANUALLY CHECK SCREENSHOTS** - Look at them yourself! This is NOT optional!
- Verify success programmatically (but this is secondary to visual checks)
- Save session between steps
- Use descriptive step names
- Keep steps under 100 lines
- Use CrosshairBrowserClient to see exactly where clicks happen

### ❌ DON'T:
- Multiple actions in one step
- Skip screenshot verification
- **Assume programmatic success means visual success** (IT DOESN'T!)
- Rely only on element.exists() or similar checks
- Trust that "no errors" means "it worked"
- Hard-code waits without reason
- Create "do everything" scripts
- Nest complex logic in steps

## Example Step Structure

```
scripts/
└── website_name_steps/
    ├── common.py              # Shared utilities
    ├── step01_navigate.py     # Go to site
    ├── step02_accept_cookies.py # Handle cookie banner
    ├── step03_open_login.py   # Click login button
    ├── step04_fill_login.py   # Enter credentials
    ├── step05_submit_login.py # Submit and verify
    ├── step06_navigate_to_feature.py # Go to specific page
    ├── run_steps.py          # Runner script
    └── README.md             # Documentation
```

## Converting Old Scripts

If you have a monolithic script:

1. Identify each action (navigate, click, fill, submit)
2. Create one step file per action
3. Add screenshot verification to each step
4. Test each step individually
5. Create runner to execute all steps

## Common Steps Library

Consider creating reusable step templates:

- `step_navigate_to_url.py`
- `step_accept_cookies.py`
- `step_fill_text_input.py`
- `step_click_button.py`
- `step_handle_modal.py`
- `step_wait_for_element.py`

## ⚠️ Critical: Visual Verification vs Programmatic Checks

**LESSON LEARNED**: Programmatic checks can pass while the automation completely fails!

Example of what NOT to trust:
- `element.exists()` returns True → Element might be hidden or covered
- Form validation passes → Form might not have submitted
- No JavaScript errors → Page might show user-facing error messages
- Click returns success → Click might have hit the wrong element

**What TO trust**:
- Your eyes looking at screenshots
- Crosshair screenshots showing exact click positions
- Visual confirmation of expected state changes
- Actually seeing the result you want on screen

## Debugging

When a step fails:

1. **CHECK THE SCREENSHOT FIRST** - what's actually on screen?
2. Look for crosshair screenshots to see where clicks happened
3. Run just that step: `python step04_submit.py`
4. Add more logging to the step
5. Check console errors with `client.print_recent_errors()`
6. Try with `--visible` to watch it happen

## Remember

**Every browser automation task should be broken into steps.**
**Every step should take screenshots.**
**Every screenshot should be checked.**

This is not optional - it's the required approach for reliable automation.