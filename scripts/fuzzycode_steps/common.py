#!/usr/bin/env python3
"""
Common utilities and imports for all FuzzyCode step scripts
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from clients.browser_client_crosshair import CrosshairBrowserClient

# Use CrosshairBrowserClient as the default
BrowserClient = CrosshairBrowserClient

# Test credentials
TEST_USERNAME = "robert.norbeau+test2@gmail.com"
TEST_PASSWORD = "robert.norbeau+test2"

# Common wait times
WAIT_SHORT = 1000
WAIT_MEDIUM = 2000
WAIT_LONG = 3000
WAIT_EXTRA_LONG = 5000

async def take_screenshot_and_check(client, filename, description):
    """Take a screenshot and prompt for verification"""
    await client.screenshot(filename)
    print(f"   ✓ Screenshot: {filename}")
    print(f"   📸 {description}")
    print(f"   ⚠️  CHECK: Verify the screenshot shows the expected state")
    return filename

async def check_element_exists(client, selector, description):
    """Check if an element exists and log the result"""
    result = await client.evaluate(f"""
        (() => {{
            const element = document.querySelector('{selector}');
            return {{
                exists: element !== null,
                visible: element ? element.offsetParent !== null : false,
                text: element ? element.textContent.trim().slice(0, 50) : null
            }};
        }})()
    """)
    
    print(f"   🔍 Checking {description}:")
    print(f"      Exists: {result['exists']}")
    print(f"      Visible: {result['visible']}")
    if result['text']:
        print(f"      Text: {result['text']}...")
    
    return result

async def wait_and_check(client, wait_time, message):
    """Wait with a message"""
    print(f"   ⏳ {message} ({wait_time}ms)...")
    await client.wait(wait_time)

def print_step_header(step_num, step_name):
    """Print a formatted step header"""
    print("\n" + "="*60)
    print(f"STEP {step_num}: {step_name}")
    print("="*60)

def print_step_result(success, message=""):
    """Print step result"""
    if success:
        print(f"\n✅ Step completed successfully! {message}")
    else:
        print(f"\n❌ Step failed! {message}")

async def save_session_info(session_id, page_id, step_num):
    """Save session info for next step"""
    session_file = Path(__file__).parent / "session_info.json"
    import json
    
    data = {
        "session_id": session_id,
        "page_id": page_id,
        "last_step": step_num
    }
    
    with open(session_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"   💾 Session saved to session_info.json")

async def load_session_info():
    """Load session info from previous step"""
    session_file = Path(__file__).parent / "session_info.json"
    import json
    
    if not session_file.exists():
        return None
    
    with open(session_file, "r") as f:
        return json.load(f)

# Export all
__all__ = [
    'EnhancedBrowserClient',
    'CrosshairBrowserClient',
    'BrowserClient',
    'TEST_USERNAME',
    'TEST_PASSWORD',
    'WAIT_SHORT',
    'WAIT_MEDIUM', 
    'WAIT_LONG',
    'WAIT_EXTRA_LONG',
    'take_screenshot_and_check',
    'check_element_exists',
    'wait_and_check',
    'print_step_header',
    'print_step_result',
    'save_session_info',
    'load_session_info',
    'asyncio'
]