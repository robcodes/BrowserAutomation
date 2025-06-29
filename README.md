# Browser Automation Framework

A modular, visual-first browser automation framework built on Playwright with AI-powered element detection.

## ✨ Key Features

- **🎯 Crosshair Click Visualization** - See exactly where every click happens
- **👁️ Visual Verification First** - Screenshots are the source of truth, not DOM checks
- **🤖 AI-Powered Element Detection** - Gemini Vision API integration for hard-to-find elements
- **📦 Modular Step-by-Step Pattern** - Each action in its own reusable script
- **🔄 Session Persistence** - Maintain browser state across script executions
- **🐛 Advanced Debugging** - Console logs, network monitoring, detailed screenshots

## 🚨 IMPORTANT: Use Step-by-Step Scripts

**The preferred approach for ALL browser automation is the modular step-by-step pattern.**

See `/scripts/fuzzycode_steps/` for the reference implementation:
- Each step is a separate script (step01_navigate.py, step02_login.py, etc.)
- Each step takes screenshots that MUST be checked VISUALLY by you
- Each step verifies success before proceeding
- Steps share session via session_info.json

**DO NOT** create monolithic scripts that try to do everything at once.

## 🚨 Critical: Visual Verification

**READ THIS FIRST**: [Visual Verification Guide](CLAUDE_INSTRUCTIONS/VISUAL_VERIFICATION_GUIDE.md)

Programmatic checks can lie. Screenshots don't. ALWAYS verify visually!

## Quick Start

1. **Start the server**:
   ```bash
   python server/browser_server_enhanced.py
   ```

2. **Use the client with crosshair visualization** (RECOMMENDED):
   ```python
   from clients.browser_client_crosshair import CrosshairBrowserClient
   
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
   - Use `client.print_recent_errors()` for console errors
   - Screenshots saved in `screenshots/`

## Project Structure

```
/
├── server/                 # Browser server implementation
│   ├── browser_server_enhanced.py    # Main server with UI
│   └── static/            # Web UI files
├── clients/                # Client libraries
│   ├── browser_client_crosshair.py   # ⭐ Client with click visualization
│   ├── browser_client_enhanced.py    # Client with debugging features
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
├── CLAUDE_INSTRUCTIONS/    # Essential documentation
│   ├── VISUAL_VERIFICATION_GUIDE.md
│   └── STEP_BY_STEP_GUIDE.md
├── CLAUDE_TMP/            # Temporary work files
├── experimental/          # Experimental scripts
└── screenshots/           # Screenshot storage

## Key Files

- **`server/browser_server_enhanced.py`** - Enhanced server with console/network logging and web UI
- **`clients/browser_client_crosshair.py`** - Client with click visualization (ALWAYS USE THIS)
- **`clients/browser_client_enhanced.py`** - Client with debugging capabilities
- **`CLAUDE.md`** - Main instructions for Claude Code

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
- **Import errors**: Use direct imports like `from clients.browser_client_crosshair import ...`
- **Session not found**: Server may have restarted, create new session

## Further Reading

- See `CLAUDE.md` for main instructions and philosophy
- See `CLAUDE_INSTRUCTIONS/VISUAL_VERIFICATION_GUIDE.md` for why screenshots matter
- See `CLAUDE_INSTRUCTIONS/STEP_BY_STEP_GUIDE.md` for the modular approach
- See `scripts/fuzzycode_steps/README.md` for the reference implementation
- See `ENV_REPLIT.md` or `ENV_DOCKER_UBUNTU.md` for environment setup