# FuzzyCode Step-by-Step Automation

## ⭐ THIS IS THE REFERENCE IMPLEMENTATION

This directory demonstrates the **REQUIRED** pattern for ALL browser automation. Every automation task MUST be broken into modular step scripts like these.

## Core Philosophy

1. **One script per step** - Each step does ONE thing only
2. **Visual verification** - Screenshots are the ONLY truth
3. **Session persistence** - Browser stays open between steps
4. **Reusability** - Steps work independently and reliably
5. **Clear reporting** - Each step clearly shows success/failure

## ⚠️ CRITICAL: No Programmatic Verification

**We removed ALL programmatic checks from these scripts!** Why?
- They give false confidence
- They often lie (e.g., can't detect modals in iframes)
- They confuse future LLMs into writing more broken checks
- Screenshots tell the truth - always check them yourself!

## Files Overview

### Core Files:
- **`common.py`** - Shared utilities, credentials, helper functions
- **`run_steps.py`** - Main runner that executes all steps in sequence
- **`session_info.json`** - Session persistence (auto-generated)

### Step Files (in order):
1. **`step01_navigate.py`** - Navigate to website and verify page loaded
2. **`step02_open_login.py`** - Click profile icon to open login modal
3. **`step03_fill_login.py`** - Fill username and password fields
4. **`step04_submit_login.py`** - Submit login form and wait for completion
5. **`step05_close_modal.py`** - Close the welcome modal after login
6. **`step06_generate_code.py`** - Enter prompt and generate code

## Usage

### Run all steps:
```bash
# Headless mode (default)
python run_steps.py all

# Visible browser mode
python run_steps.py all --visible
```

### Run individual step:
```bash
# Run step 1 in headless mode
python step01_navigate.py

# Run step 1 with visible browser
python step01_navigate.py --visible

# Or use the runner
python run_steps.py 1
python run_steps.py 3 --visible
```

## Key Patterns to Follow

```python
# 1. Load session from previous step
session_info = await load_session_info()
if not session_info or session_info['last_step'] < 2:
    print("❌ Previous steps not completed!")
    return False

# 2. Connect to existing session
client = BrowserClient()  # Uses CrosshairBrowserClient
await client.connect_session(session_info['session_id'])

# 3. Take screenshots and verify
await take_screenshot_and_check(
    client,
    "descriptive_name.png",
    "What you expect to see"
)

# 4. Save session for next step
await save_session_info(session_id, page_id, step_number)
```

## Screenshots Generated

Each step creates screenshots in `../../screenshots/`:
- `step01_fuzzycode_homepage.png` - Initial page load
- `step02_login_modal_open.png` - Login modal visible
- `step03_login_form_filled.png` - Credentials entered
- `step04_post_submit.png` - After login attempt
- `step05_modal_closed.png` - Main interface ready
- `step06_code_generated.png` - Generated code output

## Creating New Automation

### 1. Copy this directory structure:
```bash
cp -r scripts/fuzzycode_steps scripts/newsite_steps
```

### 2. Update site-specific values:
- URLs in navigation steps
- Selectors for elements
- Expected text/content
- Credentials in `common.py`

### 3. Keep the same patterns:
- Session handling
- Screenshot verification
- Error checking
- Step numbering

### 4. Test each step individually first

## Common Functions (from common.py)

- `take_screenshot_and_check()` - Capture and describe state
- `check_element_exists()` - Verify element presence
- `wait_and_check()` - Wait with status message
- `save_session_info()` - Persist session data
- `load_session_info()` - Restore session data
- `print_step_header()` - Consistent formatting

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Step fails | Check the screenshot to see actual state |
| Login fails | Verify credentials in `common.py` |
| Element not found | Add more wait time for modals/iframes |
| Session lost | Server restarted - run from step 1 |
| Click missed | Check crosshair position in screenshot |

## Important Rules

### ✅ DO:
- Check screenshots yourself - don't trust programmatic checks
- Run steps in order - each depends on previous
- Keep server running - `browser_server_enhanced.py`
- Use CrosshairBrowserClient - shows click positions
- One action per step - keep it simple

### ❌ DO NOT:
- Add experimental scripts here - use `experimental/` instead
- Skip visual verification - it's mandatory
- Trust element.exists() - screenshots are truth
- Create monolithic scripts - break them down
- Mix patterns - follow this template exactly

## Why These Are Official

1. **Proven to work** - Tested extensively on fuzzycode.dev
2. **Visual debugging** - CrosshairBrowserClient shows clicks
3. **Proper patterns** - Session persistence, error handling
4. **Clean separation** - One action per file
5. **Documentation** - Clear what each step does

## Test Credentials

Stored in `common.py`:
- Username: `robert.norbeau+test2@gmail.com`
- Password: `robert.norbeau+test2`

---

**Remember**: This is THE pattern. Follow it exactly for all browser automation.