# Main Goal 
- Claude Code can perform navigation on any web page to do anything

## 🚀 Quick Start for Browser Automation
```python
# ALWAYS use CrosshairBrowserClient for visual debugging
from clients.browser_client_crosshair import CrosshairBrowserClient
client = CrosshairBrowserClient()

# Create step-by-step scripts (see /scripts/fuzzycode_steps/)
# Take screenshots and CHECK THEM YOURSELF
# Trust screenshots, not programmatic checks
```

## 📚 MUST-READ Documentation
**Read these BEFORE writing any automation code:**
1. **[Visual Verification Guide](/browser_automation/docs/VISUAL_VERIFICATION_GUIDE.md)** - Why screenshots are the ONLY truth
2. **[Step-by-Step Guide](/browser_automation/docs/STEP_BY_STEP_GUIDE.md)** - The required modular approach
3. **[TECHNIQUES.md](/browser_automation/TECHNIQUES.md)** - Proven patterns and solutions

## 🚨 CRITICAL: How We Build Automation Scripts

### THE PREFERRED APPROACH: Step-by-Step Modular Scripts
**ALWAYS create modular step scripts** like:
- `step01_navigate.py` - Navigate to website
- `step02_open_login.py` - Open login modal
- `step03_fill_form.py` - Fill form fields
- `step04_submit.py` - Submit and verify
- etc.

**Key principles:**
1. **One script per step** - Each step does ONE thing only
2. **Take screenshots** - ALWAYS take screenshots and CHECK them VISUALLY YOURSELF
3. **Verify success** - Each step must verify it worked before proceeding
4. **Reusable** - Once a step works, it should continue to work
5. **Session persistence** - Steps share session via session_info.json

**See `/browser_automation/scripts/fuzzycode_steps/` for the reference implementation**

### DO NOT create monolithic scripts that try to do everything
- ❌ Avoid: `fuzzycode_complete_automation.py` 
- ✅ Prefer: `step01_navigate.py`, `step02_login.py`, etc.

## How we achieve our goal
- Break complex automation into simple, verifiable steps
- Take screenshots at each step to verify state
- Extract patterns that work generically across websites
- Document lessons learned in TECHNIQUES.md

## Current state
- First page to explore (fuzzycode.dev), because it has some interesting challenges (partially explored but there are many other parts to explore) -> turn this into a generic process
- For detailed progress, see: FUZZY_CODE_EXPLORATION_PROGRESS.md

## Common Patterns Discovered
1. Authentication flows (modal, page, iframe)
2. Form validation (HTML5, JavaScript-based)
3. Dynamic content loading (AJAX, lazy loading)
4. Modal/overlay interactions
5. Shadow DOM and web components
6. Cross-origin restrictions

## 🚨 CRITICAL LESSON: Visual Verification is MANDATORY

**Programmatic checks LIE!** Example from actual testing:
- Step reported "Code generation failed" 
- element.exists() checks passed
- No JavaScript errors detected
- BUT: Screenshots clearly showed the code WAS generated successfully!

**ALWAYS trust screenshots over programmatic checks**. This is why we have crosshairs - to see EXACTLY what happened.

### The Golden Rule of Browser Automation:
> **"If you haven't looked at the screenshot yourself, you don't know if it worked."**

This means YOU must personally view each screenshot. Do not trust programmatic verification alone.

## 🎯 Crosshair Click Visualization

All browser automation clicks now include crosshair visualization by default:

### Features:
- **Visual debugging**: Red crosshair with yellow center dot shows exact click position
- **Automatic screenshots**: Captures moment before click with crosshair overlay
- **Coordinate labels**: Shows exact x,y coordinates in screenshot
- **Non-intrusive**: Crosshair is removed after screenshot, doesn't interfere with click

### Usage:
```python
from clients.browser_client_crosshair import CrosshairBrowserClient

# All clicks automatically show crosshairs
client = CrosshairBrowserClient()

# Click by selector - shows crosshair at element center
await client.click_with_crosshair(selector='.button', label='my_button')

# Click by coordinates - shows crosshair at exact position  
await client.click_at(x=100, y=200, label='specific_position')

# Disable crosshairs if needed
client.disable_crosshairs()
```

### Benefits:
- **Debug failed clicks**: See exactly where clicks are happening
- **Verify element positions**: Confirm selectors are finding correct elements
- **Document automation**: Screenshots serve as visual documentation
- **Troubleshoot coordinates**: Essential when using Gemini Vision or manual positions

Screenshots are saved to `/browser_automation/screenshots/` with descriptive names like `crosshair_profile_icon_62_377_timestamp.png`.

## 🔍 Visual Element Detection with Gemini Vision API

When traditional selectors fail, use Gemini's vision capabilities to find and click elements:

### ⚠️ CRITICAL: Use the "Find All" Strategy
**DO NOT** ask Gemini to find a specific element - it often selects the wrong one!
**ALWAYS** ask Gemini to find ALL elements, then programmatically select the right one.

See: `/browser_automation/docs/GEMINI_FIND_ALL_STRATEGY.md` for detailed explanation.

### How it works:
1. Take a screenshot with Playwright
2. Send to Gemini Vision API asking for ALL clickable elements
3. Gemini returns bounding boxes as [ymin, xmin, ymax, xmax] arrays
4. Filter results by position/context to find your target
5. Convert coordinates to click positions
6. Click at the exact coordinates

### Key Files:
- `/browser_automation/clients/gemini_detector.py` - Core Gemini Vision integration
- `/browser_automation/scripts/gemini_click_helper.py` - Helper for browser automation
- `/browser_automation/scripts/enhanced_gemini_click_helper.py` - Enhanced with retry logic
- `/browser_automation/examples/gemini_vision/` - Complete working examples
- `/browser_automation/docs/GEMINI_FIND_ALL_STRATEGY.md` - Why "find all" works better

### Example usage (RECOMMENDED APPROACH):
```python
from scripts.enhanced_gemini_click_helper import EnhancedGeminiClickHelper

# API Configuration
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"  # Replace with your key

# Initialize helper
helper = EnhancedGeminiClickHelper(client, GEMINI_API_KEY)

# CORRECT: Find ALL elements with comprehensive prompt
result = await detector.detect_elements(
    screenshot_path,
    "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all icons, svgs, clickable elements, buttons, etc"
)

# Then identify the X button by position
for i, coords in enumerate(result['coordinates']):
    ymin, xmin, ymax, xmax = coords
    if xmin > 940 and ymin < 70:  # Top-right area
        # This is likely the X button
        await helper.click_at_coordinates(session_id, page_id, coords)
```

### Solves These Problems:
- **No good selectors**: Elements with dynamic or missing IDs/classes
- **Visual elements**: Icons, images, or custom-styled buttons
- **Complex DOM**: Deeply nested or shadow DOM elements
- **Natural language**: Describe what you see, not how it's coded
- **Similar elements**: Distinguishes between expand/fullscreen vs close buttons

### Visual Debugging:
Gemini creates annotated images showing:
- Bounding boxes around ALL detected elements
- Clear visual feedback showing what Gemini sees
- Helps identify when wrong element is selected

### Configuration:
- **Model**: `gemini-2.5-flash` (required - best performance)
- **API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Background
- We built a server for playwright that maintains browser sessions across Claude executions
- The server allows taking screenshots, checking console logs, and debugging failures
- **IMPORTANT**: Use the step-by-step approach in `/browser_automation/scripts/fuzzycode_steps/` as the template for ALL new automation

## Interim Files
- Files needed to maintain our progress exploring in md files, because you can run out of context and forget
- Files needed to track step by step what we did, because those will be needed later to write the general docs, based on our specific steps
- Files needed to maintain exploration coverage - needed to keep track of what we've covered so far so we don't miss it

File naming patterns:
- {SITE}_STEPS.md - Sequential actions taken
- {SITE}_EXPLORATION_PROGRESS.md - Feature coverage checklist  
- {SITE}_SUMMARY.md - High-level findings
- {SITE}_INSIGHTS.md - Technical learnings and edge cases

## Requirement Final State Deliverables
- We should have one final server that best incorporates everything we need
- We can have multiple client scripts for different purposes, but they should be organized in one folder, and we should clearly remember which one was the best for each purpose and keep it clean, not leaving old versions that don't work
- A CLAUDE_PLAYWRIGHT_GUIDE.MD doc that shows best practices on how to use it for all normal cases, edge cases, etc

Folder structure:
/browser_automation/
  /server/
    - browser_server_enhanced.py (current best version)
  /clients/
    - browser_client_crosshair.py ⭐ (ALWAYS USE THIS - shows click positions)
    - browser_client_enhanced.py (legacy - has debugging but no crosshairs)
  /scripts/
    /fuzzycode_steps/  ⭐ **REFERENCE IMPLEMENTATION - USE THIS PATTERN**
      - README_OFFICIAL.md (EXPLAINS WHICH FILES ARE OFFICIAL)
      - common.py (shared utilities, credentials)
      - step01_navigate.py
      - step02_open_login.py
      - step03_fill_login.py
      - step04_submit_login.py
      - step05_close_modal.py
      - step06_generate_code.py
      - run_steps.py (runner for all steps)
    - Other automation scripts
  /experimental/
    - Scripts being tested (should be converted to step format)
  /interim/
    - Progress tracking and exploration files
  /deprecated/
    - Old monolithic scripts (DO NOT USE AS EXAMPLES)
    /fuzzycode_experiments/ (65 old experimental files - IGNORE THESE)
  /docs/
    - TECHNIQUES.md (automation patterns)
    - ARCHITECTURE.md (system design)

## ⚠️ Common Pitfalls to AVOID
1. **Trusting programmatic checks** - They lie! Check screenshots yourself
2. **Creating monolithic scripts** - Use step-by-step pattern instead
3. **Skipping visual verification** - This is how you miss failures
4. **Not using crosshairs** - You need to see where clicks happen
5. **Assuming "no errors" = success** - Visual state is what matters

## Success Criteria
- Complete the obvious automation tasks
- Ask the user for validation when unsure
- Solutions should work generically across similar sites
- ALWAYS verify success visually through screenshots


# Environment Context

## System Architecture
- **Host OS**: Ubuntu Desktop
- **Container Platform**: Docker
- **Container Management**: Portainer
- **Container OS**: Ubuntu Desktop (running inside Docker)
- **Access Method**: noVNC2 (browser-based VNC client)

## Environment Details
- **Working Directory**: `/home/ubuntu`
- **Platform**: Linux
- **Kernel Version**: 6.11.0-26-generic
- **Date**: 2025-06-23
- **Git Repository**: No (current directory is not a git repo)

## Access Flow
1. Ubuntu Desktop (Host) → Portainer → Docker Container (Ubuntu Desktop)
2. Container exposes VNC server
3. User accesses via noVNC2 in web browser
4. Full desktop environment available through browser

## Implications
- This is a containerized desktop environment
- GUI applications can be run and accessed through the browser
- File system is isolated within the Docker container
- Network access may be subject to Docker networking configuration
- Performance may be affected by VNC overhead

## Installed Development Environment

### Operating System
- **Distribution**: Ubuntu 20.04.2 LTS (Focal Fossa)
- **Kernel**: 6.11.0-26-generic (from host)
- **Architecture**: x86_64

### Programming Languages & Runtimes
**Installed:**
- Python 3.8.5 (with Python 3 symlink)
- Node.js v20.11.0
- npm 10.2.4
- GCC 9.4.0 (C compiler)
- G++ 9.4.0 (C++ compiler)
- Perl 5.30.0

**NOT Installed:**
- Java/JDK
- Go
- Rust
- Ruby
- PHP (except basic perl)

### Build Tools & Package Managers
**Installed:**
- GNU Make 4.2.1
- build-essential package (includes gcc, g++, make, etc.)

**NOT Installed:**
- CMake
- pip/pip3 (Python package manager)
- yarn
- cargo (Rust)
- Maven
- Gradle

### Version Control
**NOT Installed:**
- Git (critical missing tool)
- SVN
- Mercurial
- GitHub CLI

### Text Editors & IDEs
**NOT Installed:**
- vim
- emacs
- nano
- VS Code
- Sublime Text
- Atom
- gedit

### Container & Virtualization Tools
**NOT Installed:**
- Docker
- Docker Compose
- Podman
- kubectl
- Vagrant
- VirtualBox

### Network & Utility Tools
**Installed:**
- curl 7.68.0
- wget 1.20.3
- OpenSSL 1.1.1f
- netstat (net-tools 2.10-alpha)

**NOT Installed:**
- SSH client
- ripgrep (rg)

## Development Environment Assessment

### Critical Missing Tools
1. **Git** - Essential for version control
2. **Text editor** (vim/nano/emacs) - No console editors available
3. **pip/pip3** - Can't install Python packages
4. **SSH** - Can't connect to remote repositories

### What's Working
- Basic compilation toolchain (gcc/g++/make)
- Node.js ecosystem (node/npm)
- Python runtime
- Network tools (curl/wget)

### Recommendations for Development
To make this a functional development environment, at minimum you need:
```bash
sudo apt update
sudo apt install -y git vim nano python3-pip openssh-client
```

For a more complete setup:
```bash
# Version control & editors
sudo apt install -y git vim nano emacs

# Python development
sudo apt install -y python3-pip python3-venv python3-dev

# Additional tools
sudo apt install -y openssh-client ripgrep cmake

# For GUI development (if needed)
sudo apt install -y code  # VS Code
```