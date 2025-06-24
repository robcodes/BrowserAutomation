# Official FuzzyCode Step Implementation

## ⭐ THIS IS THE REFERENCE IMPLEMENTATION

This directory contains the **official** step-by-step automation pattern that should be used as a template for ALL browser automation tasks.

## Official Files Only

### Core Files:
- **`common.py`** - Shared utilities, credentials, and helper functions
- **`run_steps.py`** - Main runner that executes all steps in sequence
- **`session_info.json`** - Session persistence between steps (auto-generated)

### Step Files (in order):
1. **`step01_navigate.py`** - Navigate to website and verify page loaded
2. **`step02_open_login.py`** - Click profile icon to open login modal
3. **`step03_fill_login.py`** - Fill username and password fields
4. **`step04_submit_login.py`** - Submit login form and wait for completion
5. **`step05_close_modal.py`** - Close the welcome modal after login
6. **`step06_generate_code.py`** - Enter prompt and generate code

## Important Notes

### What Was Cleaned Up
- All experimental variations (e.g., `*_direct.py`, `*_visual.py`, `*_gemini.py`)
- Debug scripts and investigations
- Alternative implementations
- These have been moved to `/deprecated/fuzzycode_experiments/`

### Why These Are Official
- They follow the step-by-step pattern consistently
- They use CrosshairBrowserClient for visual debugging
- They implement proper session persistence
- They take screenshots for visual verification
- They've been tested and proven to work

### How to Use as Template
1. Copy this directory structure for new sites
2. Replace site-specific values (URLs, selectors, text)
3. Keep the same patterns (session handling, screenshots, verification)
4. One action per step file
5. Always verify visually with screenshots

### Key Patterns to Follow
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

## DO NOT
- Add experimental scripts to this directory
- Create variations without moving old versions to deprecated
- Skip visual verification
- Trust programmatic checks over screenshots
- Create monolithic scripts that do everything

This is the pattern. Follow it.