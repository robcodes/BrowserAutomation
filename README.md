# Browser Automation Project

## 🚨 IMPORTANT: Use Step-by-Step Scripts

**The preferred approach for ALL browser automation is the modular step-by-step pattern.**

See `/scripts/fuzzycode_steps/` for the reference implementation:
- Each step is a separate script (step01_navigate.py, step02_login.py, etc.)
- Each step takes screenshots that MUST be checked VISUALLY by you
- Each step verifies success before proceeding
- Steps share session via session_info.json

**DO NOT** create monolithic scripts that try to do everything at once.

## 🚨 Critical: Visual Verification

**READ THIS FIRST**: [Visual Verification Guide](docs/VISUAL_VERIFICATION_GUIDE.md)

Programmatic checks can lie. Screenshots don't. ALWAYS verify visually!

## Quick Start

1. **Start the server**:
   ```bash
   python server/browser_server_enhanced.py
   ```

2. **Use the client with crosshair visualization** (RECOMMENDED):
   ```python
   from browser_automation.clients.browser_client_crosshair import CrosshairBrowserClient
   
   # Crosshairs show EXACTLY where clicks happen
   client = CrosshairBrowserClient()
   
   # Headless mode (default)
   session_id = await client.create_session()
   
   # Visible browser mode (watch it run!)
   session_id = await client.create_session(headless=False)
   
   page_id = await client.new_page("https://example.com")
   
   # All clicks show crosshairs automatically
   await client.click_with_crosshair(selector='.button', label='my_button')
   ```

3. **Debug issues**:
   - Check `logs/` folder for server logs
   - Use `client.print_recent_errors()` for console errors
   - Screenshots saved in `screenshots/`

## Project Structure

```
browser_automation/
├── server/                 # Browser server implementation
│   ├── browser_server_enhanced.py    # Main server with logging
│   └── browser_server_poc.py         # Original proof of concept
├── clients/                # Client libraries
│   ├── browser_client_crosshair.py   # ⭐ Client with click visualization
│   ├── browser_client_enhanced.py    # Client with debugging features
│   ├── browser_client_poc.py         # Original client
│   └── gemini_detector.py            # Gemini Vision API integration
├── scripts/                # Working automation scripts
│   ├── fuzzycode_steps/   # Modular step-by-step scripts ⭐ REFERENCE
│   │   ├── common.py      # Shared utilities and credentials
│   │   ├── step01_navigate.py    # Navigate to FuzzyCode
│   │   ├── step02_open_login.py  # Open login modal
│   │   ├── step03_fill_login.py  # Fill login form
│   │   ├── step04_submit_login.py # Submit and verify login
│   │   ├── step05_close_modal.py  # Close welcome modal
│   │   ├── step06_generate_code.py # Generate code
│   │   └── run_steps.py   # Runner for all steps
│   └── gemini_click_helper.py # Helper for visual element detection
├── experimental/           # FuzzyCode exploration scripts
├── examples/              # Problem-solving examples
│   ├── fuzzycode/         # Specific solutions that worked
│   └── gemini_vision/     # Gemini Vision API examples ⭐ NEW
│       ├── simple_click_example.py   # Basic usage
│       ├── modal_close_example.py    # Modal handling
│       └── README.md      # Gemini setup guide
├── tests/                 # Test files
├── docs/                  # Documentation
├── interim/               # Progress tracking files
└── screenshots/           # Screenshot storage

## Key Files

- **`server/browser_server_enhanced.py`** - Enhanced server with console/network logging
- **`clients/browser_client_enhanced.py`** - Client with debugging capabilities
- **`ARCHITECTURE.md`** - System design and rationale
- **`TECHNIQUES.md`** - Automation patterns and solutions
- **`docs/BROWSER_AUTOMATION_BEST_PRACTICES.md`** - Comprehensive guide

## Important Discoveries

1. **Console Logging**: Reveals hidden errors (401 auth failures)
2. **Direct Array Access**: `inputs[0]`, `inputs[1]` for forms
3. **Session Persistence**: External server maintains browser state
4. **Modal Handling**: Page reload often the simplest solution
5. **Visual Element Detection**: Gemini Vision API for hard-to-target elements

## Common Tasks

### Debug Failed Automation
```python
# Check console errors
await client.print_recent_errors()

# Get detailed logs
logs = await client.get_console_logs(limit=50, types=["error"])

# Check network failures  
await client.debug_failed_action()
```

### Handle Login Forms
```python
# Use direct array access when selectors fail
await client.evaluate("""
  const inputs = document.querySelectorAll('input');
  inputs[0].value = 'username';
  inputs[1].value = 'password';
""")
```

### Take Screenshots
```python
await client.screenshot("step1_before_action.png")
# Perform action
await client.screenshot("step2_after_action.png")
```

### Use Visual Detection (Gemini Vision API)
```python
from scripts.gemini_click_helper import GeminiClickHelper

# When CSS selectors fail, use visual detection
helper = GeminiClickHelper(client, GEMINI_API_KEY)
success = await helper.click_element_by_description(
    session_id, page_id,
    "close button in the modal header"
)
```

## Troubleshooting

- **Server already running**: Check `ps aux | grep browser_server`
- **Import errors**: Ensure you're importing from `browser_automation.`
- **Session not found**: Server may have restarted, create new session

## Further Reading

- See `ARCHITECTURE.md` for system design
- See `TECHNIQUES.md` for automation patterns
- See `docs/GEMINI_VISION_GUIDE.md` for visual element detection
- See `examples/fuzzycode/README.md` for specific solutions
- See `examples/gemini_vision/` for Gemini Vision examples
- See `interim/FUZZYCODE_TEST_CREDENTIALS.md` for test login credentials
- See `docs/` for comprehensive guides