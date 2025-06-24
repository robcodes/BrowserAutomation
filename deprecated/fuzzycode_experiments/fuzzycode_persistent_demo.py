#!/usr/bin/env python3
"""
Demo: Using persistent browser server with fuzzycode.dev
Shows how to navigate complex sites with screenshot analysis
"""
import asyncio
import json
from browser_client_poc import PersistentBrowserClient

async def explore_fuzzycode_step1():
    """Step 1: Initial exploration and screenshot"""
    print("=== STEP 1: Initial Exploration of FuzzyCode ===\n")
    
    client = PersistentBrowserClient()
    
    # Create a new session
    session_id = await client.create_session()
    print(f"Created session: {session_id}")
    
    # Navigate to fuzzycode.dev
    page_id = await client.new_page("https://fuzzycode.dev")
    print(f"Created page: {page_id}")
    
    # Wait for page to load
    await client.wait(3000)
    
    # Take initial screenshot
    screenshot_path = await client.screenshot("fuzzycode_1_initial.png")
    print(f"\nScreenshot saved: {screenshot_path}")
    
    # Get page info
    info = await client.get_info()
    print(f"\nPage info:")
    print(f"  Title: {info['title']}")
    print(f"  URL: {info['url']}")
    
    # Try to close any welcome modal if present
    try:
        # Try clicking outside modal or close button
        await client.click('.modal-close, .close, button[aria-label="Close"]')
        print("\n✓ Closed modal/popup")
        await client.wait(1000)
        await client.screenshot("fuzzycode_2_modal_closed.png")
    except:
        print("\n✓ No modal to close")
    
    # Save session info
    session_data = {
        "session_id": session_id,
        "page_id": page_id,
        "site": "fuzzycode.dev",
        "step": 1
    }
    
    with open("fuzzycode_session.json", "w") as f:
        json.dump(session_data, f, indent=2)
    
    print(f"\n💾 Session saved! Use this to continue:")
    print(f"   Session: {session_id}")
    print(f"   Page: {page_id}")
    
    return session_id, page_id

async def continue_fuzzycode_step2():
    """Step 2: Fill prompt and generate code"""
    print("\n=== STEP 2: Fill Prompt and Generate Code ===\n")
    
    # Load session
    with open("fuzzycode_session.json", "r") as f:
        session_data = json.load(f)
    
    client = PersistentBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Fill the main textarea with a prompt
    prompt_text = "Create a Python function that generates the Fibonacci sequence up to n terms"
    print(f"\n→ Filling prompt: {prompt_text}")
    
    try:
        # Try to fill the main textarea
        await client.fill('textarea', prompt_text)
        print("✓ Filled textarea")
    except Exception as e:
        print(f"⚠ Error filling textarea: {e}")
        # Try alternative selector
        await client.fill('input[type="text"]', prompt_text)
        print("✓ Filled input field")
    
    # Take screenshot after filling
    await client.screenshot("fuzzycode_3_prompt_filled.png")
    
    # Click the generate button
    print("\n→ Clicking 'Fuzzy Code It!' button")
    try:
        await client.click('button:has-text("Fuzzy Code It!")')
        print("✓ Clicked generate button")
    except Exception as e:
        print(f"⚠ Error clicking button: {e}")
        # Try alternative approaches
        await client.click('button.primary, button[type="submit"]')
    
    # Wait for generation
    print("\n⏳ Waiting for code generation...")
    await client.wait(5000)
    
    # Take screenshot of results
    screenshot_path = await client.screenshot("fuzzycode_4_after_generation.png")
    print(f"\n✓ Results screenshot: {screenshot_path}")
    
    # Update session data
    session_data["step"] = 2
    with open("fuzzycode_session.json", "w") as f:
        json.dump(session_data, f, indent=2)
    
    print("\n💡 Check the screenshots to see if code was generated!")

async def explore_fuzzycode_features():
    """Step 3: Explore other features"""
    print("\n=== STEP 3: Explore FuzzyCode Features ===\n")
    
    # Load session
    with open("fuzzycode_session.json", "r") as f:
        session_data = json.load(f)
    
    client = PersistentBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Check the dropdown menu
    print("\n→ Checking dropdown menu options")
    try:
        # Get dropdown options
        options_script = """
        Array.from(document.querySelectorAll('select option')).map(opt => ({
            value: opt.value,
            text: opt.textContent
        }))
        """
        options = await client.evaluate(options_script)
        print(f"✓ Found {len(options)} dropdown options")
        for opt in options[:5]:  # Show first 5
            print(f"   - {opt['text']}")
    except Exception as e:
        print(f"⚠ Could not get dropdown options: {e}")
    
    # Try Sample Prompts
    print("\n→ Trying Sample Prompts button")
    try:
        await client.click('button:has-text("Sample Prompts")')
        await client.wait(1000)
        await client.screenshot("fuzzycode_5_sample_prompts.png")
        print("✓ Clicked Sample Prompts")
    except:
        print("⚠ Sample Prompts button not clickable")
    
    # Check for the Play Now link
    print("\n→ Checking 'Play Now' link")
    try:
        play_href = await client.evaluate('document.querySelector("a:has-text(\'Play Now\')").href')
        print(f"✓ Play Now link found: {play_href}")
    except:
        print("⚠ Play Now link not found")
    
    # Final screenshot
    await client.screenshot("fuzzycode_6_final_state.png")
    
    print("\n✅ Exploration complete!")
    print("   Check the screenshots to see the progression")

async def cleanup_session():
    """Clean up the browser session"""
    print("\n=== Cleanup ===")
    
    try:
        with open("fuzzycode_session.json", "r") as f:
            session_data = json.load(f)
        
        client = PersistentBrowserClient()
        await client.connect_session(session_data["session_id"])
        await client.close_session()
        print("✓ Session closed")
    except:
        print("⚠ No session to clean up")

if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            if sys.argv[1] == "1":
                await explore_fuzzycode_step1()
            elif sys.argv[1] == "2":
                await continue_fuzzycode_step2()
            elif sys.argv[1] == "3":
                await explore_fuzzycode_features()
            elif sys.argv[1] == "cleanup":
                await cleanup_session()
            else:
                print("Unknown step")
        else:
            print("Usage:")
            print("  python fuzzycode_persistent_demo.py 1        # Initial exploration")
            print("  python fuzzycode_persistent_demo.py 2        # Fill prompt & generate")
            print("  python fuzzycode_persistent_demo.py 3        # Explore features")
            print("  python fuzzycode_persistent_demo.py cleanup  # Close session")
    
    asyncio.run(main())