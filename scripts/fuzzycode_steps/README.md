# FuzzyCode Step-by-Step Automation

## 🚨 THIS IS THE REFERENCE IMPLEMENTATION

**This directory demonstrates the REQUIRED pattern for ALL browser automation.**

Every automation task MUST be broken into modular step scripts like these.
Each step is a separate script that takes screenshots and verifies success before proceeding.

## Philosophy

- **One script per step** - Each step is isolated and can be run independently
- **Screenshot verification** - Every step takes screenshots that MUST be checked
- **Reusable** - Once a step works, it should continue to work
- **Clear success criteria** - Each step clearly reports success or failure
- **Session persistence** - Steps share session info via `session_info.json`

## Available Steps

1. **step01_navigate.py** - Navigate to FuzzyCode homepage
2. **step02_open_login.py** - Click profile icon to open login modal
3. **step03_fill_login.py** - Fill username and password fields
4. **step04_submit_login.py** - Submit login form and check result
5. **step05_close_modal.py** - Close welcome modal after login
6. **step06_generate_code.py** - Enter prompt and generate code

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

## Test Credentials

Stored in `common.py`:
- Username: `robert.norbeau+test2@gmail.com`
- Password: `robert.norbeau+test2`

## Screenshots

Each step generates screenshots in the parent `screenshots/` directory:
- `step01_fuzzycode_homepage.png` - Initial page load
- `step02_login_modal_open.png` - Login modal visible
- `step03_login_form_filled.png` - Credentials entered
- `step04_post_submit.png` - After login attempt
- `step05_modal_closed.png` - Main interface ready
- `step06_code_generated.png` - Generated code output

## Common Functions

The `common.py` file provides shared utilities:
- `take_screenshot_and_check()` - Take screenshot with description
- `check_element_exists()` - Check if element exists and is visible
- `wait_and_check()` - Wait with status message
- `save_session_info()` - Save session for next step
- `load_session_info()` - Load session from previous step

## Adding New Steps

1. Create `step07_your_action.py`
2. Import from `common` 
3. Load session info from previous step
4. Perform action with verification
5. Take screenshots at key points
6. Save session info for next step
7. Return True/False for success

## Troubleshooting

- **Step fails**: Check the screenshot to see actual state
- **Login fails**: Verify credentials in `common.py`
- **Element not found**: Modal/iframe may need more wait time
- **Session lost**: Server may have restarted, run from step 1

## Important Notes

1. **ALWAYS CHECK SCREENSHOTS** - Don't assume success
2. **Steps must be run in order** - Each depends on previous
3. **Session persists** - Browser stays open between steps
4. **Server must be running** - Start `browser_server_enhanced.py` first