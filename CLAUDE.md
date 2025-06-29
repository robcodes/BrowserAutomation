# Browser Automation with Claude Code

## 🎯 Main Goal
Enable Claude Code to explore any website autonomously - navigating, interacting, and documenting like a human user would.

## 🚀 Quick Start
```python
from clients.browser_client_crosshair import CrosshairBrowserClient
client = CrosshairBrowserClient()  # ALWAYS use this - shows click positions
```

## 📋 The Process

### When You Ask Me to Explore a Website:
1. I create numbered step scripts (`step01_navigate.py`, `step02_login.py`, etc.)
2. I take screenshots at each step and **CHECK THEM MYSELF**
3. I document what I see in exploration tracking files
4. I use crosshairs to show exactly where I'm clicking

### The Golden Rule:
> **"Screenshots are the ONLY truth. If I haven't looked at the screenshot myself, I don't know if it worked."**

## 🏗️ Architecture

### Two Components:
1. **Server** (`browser_server_enhanced.py`)
   - Maintains persistent browser sessions
   - Provides web UI for manual testing
   - Handles screenshots, logging, and debugging
   - Goal: Make it the gold standard with reusable abilities

2. **Client** (`browser_client_crosshair.py`) 
   - Used by Claude Code for automation
   - Shows crosshairs on all clicks for visual debugging
   - Minimal custom code needed - server does the heavy lifting

## 📁 Project Structure
```
/
├── server/
│   ├── browser_server_enhanced.py      # Main server
│   └── static/index_enhanced.html      # Web UI for testing
├── clients/
│   ├── browser_client_crosshair.py ⭐   # ALWAYS use this
│   └── gemini_detector.py              # Vision API integration
├── scripts/
│   └── fuzzycode_steps/ ⭐              # REFERENCE IMPLEMENTATION
│       ├── step01_navigate.py          # One action per file
│       ├── step02_open_login.py        # Session persists between steps
│       └── common.py                   # Shared utilities
└── CLAUDE_INSTRUCTIONS/                # Key documentation
    ├── VISUAL_VERIFICATION_GUIDE.md
    └── STEP_BY_STEP_GUIDE.md
```

## 🔑 Key Principles

### 1. Step-by-Step Modular Approach
- **One script per action** (navigate, login, click button, etc.)
- **Session persistence** via `session_info.json`
- **Visual verification** at each step
- **No monolithic scripts** - break everything down

### 2. Visual Verification is MANDATORY
- Programmatic checks lie (element.exists() can be wrong)
- Screenshots show the actual state
- I must personally view each screenshot
- Crosshairs show exactly where clicks happen

### 3. Generalizable Patterns
- Currently using fuzzycode.dev as test site
- Everything should work on any website
- Document patterns for reuse

## 📝 Tracking Exploration

For each site I explore, I create:
- `{SITE}_STEPS.md` - Sequential actions taken
- `{SITE}_EXPLORATION_PROGRESS.md` - What's been covered
- `{SITE}_NOTES.md` - Technical findings and issues

## 🗂️ File Management

### Temporary Files
All temporary scripts and documentation go in `CLAUDE_TMP/`:
- Test scripts while developing
- Draft documentation
- Exploration notes
- Debug outputs

### When to Move Files:
- **To `scripts/`** - When a script is tested and working
- **To `scripts/{site}_steps/`** - When creating site automation
- **To `docs/`** - When documentation is finalized
- **Delete** - When no longer needed

### Example:
```bash
# Working on new automation
CLAUDE_TMP/test_login_flow.py      # Initial development
CLAUDE_TMP/login_notes.md          # My observations

# Once working, move to proper location
scripts/newsite_steps/step01_login.py
```

**Rule**: Keep the main directories clean. Use CLAUDE_TMP for work in progress.

## 🛠️ When Selectors Fail: Gemini Vision

For elements without good selectors:
1. Take screenshot
2. Send to Gemini Vision API
3. Get bounding boxes for ALL elements
4. Filter to find the right one
5. Click at exact coordinates

**Important**: Always ask for ALL elements, not a specific one.

## ⚠️ Common Pitfalls
1. **Trusting programmatic checks** - Check screenshots instead
2. **Creating monolithic scripts** - Use step pattern
3. **Skipping visual verification** - This causes missed failures
4. **Not using crosshairs** - Can't debug click positions

## 🌍 Environment Setup
- **Replit**: See `ENV_REPLIT.md`
- **Docker Ubuntu**: See `ENV_DOCKER_UBUNTU.md`

## 📚 Essential Reading
- `CLAUDE_INSTRUCTIONS/VISUAL_VERIFICATION_GUIDE.md`
- `CLAUDE_INSTRUCTIONS/STEP_BY_STEP_GUIDE.md`
- `scripts/fuzzycode_steps/README_OFFICIAL.md`