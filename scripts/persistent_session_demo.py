#!/usr/bin/env python3
"""
Demonstrate session persistence attempts
"""
from playwright.sync_api import sync_playwright
import json
import pickle
import os

def save_browser_state(page, filename="browser_state.json"):
    """Save current browser state"""
    state = {
        "url": page.url,
        "cookies": page.context.cookies(),
        "local_storage": {},
        "session_storage": {}
    }
    
    # Try to save localStorage
    try:
        state["local_storage"] = page.evaluate("() => Object.entries(localStorage)")
    except:
        pass
    
    # Try to save sessionStorage
    try:
        state["session_storage"] = page.evaluate("() => Object.entries(sessionStorage)")
    except:
        pass
    
    # Save form data
    try:
        state["form_data"] = page.evaluate("""() => {
            const inputs = document.querySelectorAll('input, textarea, select');
            return Array.from(inputs).map(el => ({
                selector: el.tagName + (el.id ? '#' + el.id : '') + (el.name ? '[name="' + el.name + '"]' : ''),
                value: el.value,
                type: el.type
            }));
        }""")
    except:
        pass
    
    with open(filename, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"State saved to {filename}")
    return state

def restore_browser_state(page, filename="browser_state.json"):
    """Restore browser state from file"""
    if not os.path.exists(filename):
        print("No saved state found")
        return False
    
    with open(filename, 'r') as f:
        state = json.load(f)
    
    # Navigate to saved URL
    page.goto(state["url"])
    page.wait_for_load_state('networkidle')
    
    # Restore cookies
    if state.get("cookies"):
        page.context.add_cookies(state["cookies"])
    
    # Restore localStorage
    if state.get("local_storage"):
        for key, value in state["local_storage"]:
            page.evaluate(f"localStorage.setItem('{key}', '{value}')")
    
    # Restore sessionStorage
    if state.get("session_storage"):
        for key, value in state["session_storage"]:
            page.evaluate(f"sessionStorage.setItem('{key}', '{value}')")
    
    # Restore form data
    if state.get("form_data"):
        for field in state["form_data"]:
            try:
                if field["value"]:
                    page.fill(field["selector"], field["value"])
            except:
                pass
    
    print("State restored")
    return True

# Demo 1: First session - save state
def session_part1():
    print("=== SESSION PART 1: Initial Navigation ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Navigate and interact
        page.goto("https://fuzzycode.dev")
        page.wait_for_load_state('networkidle')
        
        # Fill form
        page.fill('textarea', 'Create a hello world program')
        
        # Take screenshot
        page.screenshot(path='/home/ubuntu/screenshots/session1_before_save.png')
        
        # Save state
        state = save_browser_state(page, "fuzzycode_state.json")
        
        print("Session 1 complete - state saved")
        browser.close()

# Demo 2: Second session - restore state
def session_part2():
    print("\n=== SESSION PART 2: Restore and Continue ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Restore state
        restore_browser_state(page, "fuzzycode_state.json")
        
        # Take screenshot to verify
        page.screenshot(path='/home/ubuntu/screenshots/session2_after_restore.png')
        
        # Continue interaction
        page.click('button:has-text("Fuzzy Code It!")')
        page.wait_for_timeout(3000)
        
        page.screenshot(path='/home/ubuntu/screenshots/session2_after_action.png')
        
        print("Session 2 complete")
        browser.close()

# Alternative: Use browser context persistence
def persistent_context_demo():
    print("\n=== PERSISTENT CONTEXT DEMO ===")
    
    # First session
    with sync_playwright() as p:
        # Create persistent context
        context = p.chromium.launch_persistent_context(
            "/home/ubuntu/browser_data",
            headless=True
        )
        page = context.new_page()
        
        page.goto("https://example.com")
        page.fill('input[type="text"]', 'test data') if page.locator('input[type="text"]').count() > 0 else None
        
        page.screenshot(path='/home/ubuntu/screenshots/persistent1.png')
        context.close()
    
    print("First session closed, data persisted")
    
    # Second session - same profile
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            "/home/ubuntu/browser_data",
            headless=True
        )
        page = context.new_page()
        
        # Browser remembers cookies, localStorage, etc.
        page.goto("https://example.com")
        page.screenshot(path='/home/ubuntu/screenshots/persistent2.png')
        
        context.close()

if __name__ == "__main__":
    import sys
    
    os.makedirs('/home/ubuntu/screenshots', exist_ok=True)
    os.environ['DISPLAY'] = ':99'
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "1":
            session_part1()
        elif sys.argv[1] == "2":
            session_part2()
        elif sys.argv[1] == "persistent":
            persistent_context_demo()
    else:
        # Run all demos
        session_part1()
        session_part2()
        persistent_context_demo()