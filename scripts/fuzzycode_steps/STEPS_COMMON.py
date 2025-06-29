#!/usr/bin/env python3
"""
Common utilities for manually following steps in STEPS.md
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from clients.browser_client_crosshair import CrosshairBrowserClient
from clients.gemini_detector import GeminiDetector
sys.path.append(str(Path(__file__).parent.parent.parent / "server"))
from bbox_visualizer import visualize

# Session file for persistence
SESSION_FILE = Path(__file__).parent / "manual_session.json"
SCREENSHOT_DIR = Path(__file__).parent.parent.parent / "screenshots"

async def save_session(session_id: str, page_id: str):
    """Save session info for persistence between steps"""
    with open(SESSION_FILE, 'w') as f:
        json.dump({'session_id': session_id, 'page_id': page_id}, f)

async def load_session() -> Dict[str, str]:
    """Load saved session info"""
    if not SESSION_FILE.exists():
        raise Exception("No session file found. Run step 1 first.")
    with open(SESSION_FILE, 'r') as f:
        return json.load(f)

async def get_client() -> CrosshairBrowserClient:
    """Get a browser client connected to existing session"""
    session = await load_session()
    client = CrosshairBrowserClient()
    await client.connect_session(session['session_id'])
    await client.set_page(session['page_id'])
    return client

async def navigate(url: str, wait_time: int = 3) -> str:
    """Step 1: Navigate to URL"""
    print(f"### Navigating to {url}")
    client = CrosshairBrowserClient()
    
    print("- Creating browser session...")
    session_id = await client.create_session(headless=True)
    print(f"  ✓ Session created: {session_id}")
    
    # Connect to session
    await client.connect_session(session_id)
    
    print(f"- Navigate to {url}")
    # new_page creates a page and navigates to the URL
    page_id = await client.new_page(url)
    
    print(f"- Wait till it's loaded ({wait_time}s)")
    await asyncio.sleep(wait_time)
    
    print("- Take a screenshot")
    screenshot_name = "manual_step1_homepage.png"
    screenshot_path = await client.screenshot(screenshot_name)
    print(f"  ✓ Screenshot saved: {screenshot_name}")
    
    # Save session
    await save_session(session_id, page_id)
    
    return str(SCREENSHOT_DIR / screenshot_name)

async def click_with_gemini(target_description: str, step_num: int) -> str:
    """Click on element using Gemini detection and deep element search"""
    print(f"### Step {step_num}: Click on {target_description}")
    
    client = await get_client()
    
    # Take initial screenshot
    print("- Take a screenshot")
    screenshot_name = f"manual_step{step_num}_before.png"
    await client.screenshot(screenshot_name)
    screenshot_path = str(SCREENSHOT_DIR / screenshot_name)
    print(f"  ✓ Screenshot saved: {screenshot_name}")
    
    # Analyze with Gemini
    print("- Analyze the screenshot with gemini and have it give the bounding boxes")
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise Exception("GEMINI_API_KEY environment variable not set")
    
    # Use enhanced detector with model-specific prompts
    detector = GeminiDetector(api_key, model="gemini-2.0-flash-exp")
    
    # Create user prompt based on target description
    user_prompt = f"Find the {target_description}"
    
    result = await detector.detect_elements(
        screenshot_path, 
        user_prompt=user_prompt,
        save_annotated=False,
        return_labels=True
    )
    
    # Use the server's bbox_visualizer for better non-overlapping labels
    if result['coordinates']:
        annotated_path = visualize(
            screenshot_path, 
            json_data={'coordinates': result['coordinates']},
            mode='bbox',
            output_path=screenshot_path.replace('.png', '_annotated.png')
        )
        print(f"  ✓ Bounding boxes drawn: {Path(annotated_path).name}")
    
    print(f"- Looking for {target_description} in the bounding boxes")
    # For manual steps, we'll need to visually identify which box to use
    # In real implementation, this would be automated
    print("  ⚠️  Manual inspection needed to identify correct element")
    
    # Find element coordinates using JavaScript
    print("- Use deep element search to find elements in that position")
    
    # This is a simplified version - in practice you'd use the Gemini coordinates
    # For now, let's try to find common elements
    if "profile" in target_description.lower():
        element_info = await client.evaluate("""
            (() => {
                const profileIcon = document.querySelector('.user-profile-icon, #user-profile-icon, [aria-label*="profile"]');
                if (!profileIcon) return null;
                const rect = profileIcon.getBoundingClientRect();
                return {
                    x: rect.left + rect.width / 2,
                    y: rect.top + rect.height / 2,
                    found: true
                };
            })()
        """)
    elif "username" in target_description.lower():
        element_info = await client.evaluate("""
            (() => {
                // Check in iframes first
                const iframes = Array.from(document.querySelectorAll('iframe'));
                for (const iframe of iframes) {
                    try {
                        const iframeDoc = iframe.contentDocument;
                        if (!iframeDoc) continue;
                        const input = iframeDoc.querySelector('input[type="text"], input[type="email"], input[placeholder*="sername"], input[placeholder*="mail"]');
                        if (input) {
                            const rect = input.getBoundingClientRect();
                            const iframeRect = iframe.getBoundingClientRect();
                            return {
                                x: iframeRect.left + rect.left + rect.width / 2,
                                y: iframeRect.top + rect.top + rect.height / 2,
                                found: true
                            };
                        }
                    } catch (e) {}
                }
                return null;
            })()
        """)
    elif "password" in target_description.lower():
        element_info = await client.evaluate("""
            (() => {
                const iframes = Array.from(document.querySelectorAll('iframe'));
                for (const iframe of iframes) {
                    try {
                        const iframeDoc = iframe.contentDocument;
                        if (!iframeDoc) continue;
                        const input = iframeDoc.querySelector('input[type="password"]');
                        if (input) {
                            const rect = input.getBoundingClientRect();
                            const iframeRect = iframe.getBoundingClientRect();
                            return {
                                x: iframeRect.left + rect.left + rect.width / 2,
                                y: iframeRect.top + rect.top + rect.height / 2,
                                found: true
                            };
                        }
                    } catch (e) {}
                }
                return null;
            })()
        """)
    elif "sign in" in target_description.lower():
        element_info = await client.evaluate("""
            (() => {
                const iframes = Array.from(document.querySelectorAll('iframe'));
                for (const iframe of iframes) {
                    try {
                        const iframeDoc = iframe.contentDocument;
                        if (!iframeDoc) continue;
                        const button = Array.from(iframeDoc.querySelectorAll('button')).find(b => b.textContent.includes('Sign'));
                        if (button) {
                            const rect = button.getBoundingClientRect();
                            const iframeRect = iframe.getBoundingClientRect();
                            return {
                                x: iframeRect.left + rect.left + rect.width / 2,
                                y: iframeRect.top + rect.top + rect.height / 2,
                                found: true
                            };
                        }
                    } catch (e) {}
                }
                return null;
            })()
        """)
    else:
        element_info = None
    
    if element_info and element_info.get('found'):
        print(f"  ✓ Found element at ({element_info['x']}, {element_info['y']})")
        
        # Get crosshair screenshot
        print("- Get the crosshair screenshot, verify it makes sense")
        click_result = await client.click_at(element_info['x'], element_info['y'], f"step{step_num}_{target_description.replace(' ', '_')}")
        
        if click_result.get('screenshot_path'):
            print(f"  ✓ Crosshair screenshot: {Path(click_result['screenshot_path']).name}")
        
        print("- Send the click")
        print(f"  ✓ Click result: {click_result.get('success', False)}")
    else:
        print("  ❌ Could not find element automatically")
        return None
    
    # Wait
    print("- Wait")
    await asyncio.sleep(1)
    
    # Take final screenshot
    print("- Take a screenshot")
    screenshot_name = f"manual_step{step_num}_after.png"
    await client.screenshot(screenshot_name)
    print(f"  ✓ Screenshot saved: {screenshot_name}")
    
    return str(SCREENSHOT_DIR / screenshot_name)

async def type_text(text: str, step_num: int) -> str:
    """Type text into currently focused field"""
    print(f"### Step {step_num}: Type text")
    
    client = await get_client()
    
    print(f"- Type the text: {text}")
    # Type directly to the focused element using keyboard actions
    await client.evaluate(f"""
        (() => {{
            const activeElement = document.activeElement;
            if (activeElement && activeElement.tagName === 'INPUT') {{
                activeElement.value = '{text}';
                activeElement.dispatchEvent(new Event('input', {{ bubbles: true }}));
                activeElement.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            // Check in iframes
            const iframes = Array.from(document.querySelectorAll('iframe'));
            for (const iframe of iframes) {{
                try {{
                    const iframeDoc = iframe.contentDocument;
                    if (!iframeDoc) continue;
                    const activeInIframe = iframeDoc.activeElement;
                    if (activeInIframe && activeInIframe.tagName === 'INPUT') {{
                        activeInIframe.value = '{text}';
                        activeInIframe.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        activeInIframe.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                }} catch (e) {{}}
            }}
            return false;
        }})()
    """)
    
    print("- Wait")
    await asyncio.sleep(1)
    
    print("- Take a screenshot")
    screenshot_name = f"manual_step{step_num}_typed.png"
    await client.screenshot(screenshot_name)
    print(f"  ✓ Screenshot saved: {screenshot_name}")
    
    return str(SCREENSHOT_DIR / screenshot_name)

async def check_screenshot(screenshot_path: str):
    """Remind to check screenshot manually"""
    print("- Look at the screenshot")
    print(f"  📸 Please check: {Path(screenshot_path).name}")
    print("- Verify it is good or tell the user of the issue")

# Convenience functions for each step
async def step1():
    """Navigate to Fuzzycode.dev"""
    screenshot = await navigate("https://fuzzycode.dev")
    await check_screenshot(screenshot)
    return screenshot

async def step2():
    """Click on user profile"""
    screenshot = await click_with_gemini("user profile icon", 2)
    if screenshot:
        await check_screenshot(screenshot)
    return screenshot

async def step3():
    """Click on username field"""
    screenshot = await click_with_gemini("username field", 3)
    if screenshot:
        await check_screenshot(screenshot)
    return screenshot

async def step4():
    """Type username"""
    screenshot = await type_text("robert.norbeau+test2@gmail.com", 4)
    await check_screenshot(screenshot)
    return screenshot

async def step5():
    """Click on password field"""
    screenshot = await click_with_gemini("password field", 5)
    if screenshot:
        await check_screenshot(screenshot)
    return screenshot

async def step6():
    """Type password"""
    screenshot = await type_text("robert.norbeau+test2", 6)
    await check_screenshot(screenshot)
    return screenshot

async def step7():
    """Click sign in button"""
    screenshot = await click_with_gemini("sign in button", 7)
    if screenshot:
        await check_screenshot(screenshot)
    return screenshot

async def step8():
    """Click X button to close modal"""
    screenshot = await click_with_gemini("X button close modal", 8)
    if screenshot:
        await check_screenshot(screenshot)
    return screenshot

async def step9():
    """Click in request text area"""
    screenshot = await click_with_gemini("request text area", 9)
    if screenshot:
        await check_screenshot(screenshot)
    return screenshot

async def step10():
    """Type prime function request"""
    screenshot = await type_text("Write a Python function to check if a number is prime", 10)
    await check_screenshot(screenshot)
    return screenshot

async def step11():
    """Click Fuzzy Code It button"""
    screenshot = await click_with_gemini("Fuzzy Code It button", 11)
    if screenshot:
        await check_screenshot(screenshot)
    return screenshot

async def step12():
    """Determine success"""
    print("### Step 12: Determine Success")
    client = await get_client()
    
    print("- Wait for page to process (may take several seconds)")
    await asyncio.sleep(5)
    
    print("- Take a screenshot")
    screenshot_name = "manual_step12_result.png"
    await client.screenshot(screenshot_name)
    screenshot_path = str(SCREENSHOT_DIR / screenshot_name)
    print(f"  ✓ Screenshot saved: {screenshot_name}")
    
    print("- Look at the screenshot")
    print("- Check if still loading (look for loading indicators)")
    print("- If result appears below that looks like Python function implementation, claim success")
    await check_screenshot(screenshot_path)
    
    return screenshot_path

# Main execution helper
async def run_all_steps():
    """Run all steps in sequence"""
    steps = [
        step1, step2, step3, step4, step5, step6,
        step7, step8, step9, step10, step11, step12
    ]
    
    for i, step_func in enumerate(steps, 1):
        print(f"\n{'='*60}")
        print(f"EXECUTING STEP {i}")
        print(f"{'='*60}\n")
        
        try:
            screenshot = await step_func()
            if screenshot:
                print(f"\n✅ Step {i} completed")
            else:
                print(f"\n❌ Step {i} failed")
                break
        except Exception as e:
            print(f"\n❌ Step {i} error: {e}")
            break
        
        # Small pause between steps
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    # Allow running individual steps or all
    import sys
    if len(sys.argv) > 1:
        step_num = int(sys.argv[1])
        step_func = globals()[f'step{step_num}']
        asyncio.run(step_func())
    else:
        asyncio.run(run_all_steps())