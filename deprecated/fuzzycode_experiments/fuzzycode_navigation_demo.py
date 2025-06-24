#!/usr/bin/env python3
"""
Demonstration of navigating fuzzycode.dev by combining visual and code analysis
"""
from playwright_agent_advanced import create_browser_session
import os
import time

def navigate_fuzzycode_demo():
    """
    Navigate through fuzzycode.dev demonstrating various interactions
    """
    os.environ['DISPLAY'] = ':99'
    
    print("=== FuzzyCode Navigation Demo ===\n")
    
    # Create browser session
    agent = create_browser_session(headless=True)
    
    try:
        # 1. Navigate to main page
        print("1. Navigating to fuzzycode.dev...")
        agent.page.goto('https://fuzzycode.dev')
        agent.page.wait_for_load_state('networkidle')
        agent.page.wait_for_timeout(2000)
        
        # Take initial screenshot
        agent.page.screenshot(path='/home/ubuntu/screenshots/fuzzy_step1_initial.png')
        print("   ✓ Screenshot saved: fuzzy_step1_initial.png")
        
        # 2. Find and interact with the main prompt input
        print("\n2. Finding the main prompt input area...")
        
        # Look for the textarea/input field
        prompt_input = agent.page.locator('textarea, input[type="text"]').first
        if prompt_input:
            print("   ✓ Found prompt input field")
            
            # Enter a sample prompt
            sample_prompt = "Create a simple calculator with add, subtract, multiply, and divide functions"
            prompt_input.fill(sample_prompt)
            print(f'   ✓ Entered prompt: "{sample_prompt}"')
            
            agent.page.screenshot(path='/home/ubuntu/screenshots/fuzzy_step2_prompt_entered.png')
            print("   ✓ Screenshot saved: fuzzy_step2_prompt_entered.png")
        
        # 3. Click the "Fuzzy Code It!" button
        print("\n3. Looking for the code generation button...")
        
        # Find the button by text
        fuzzy_button = agent.page.locator('button:has-text("Fuzzy Code It!")').first
        if fuzzy_button:
            print("   ✓ Found 'Fuzzy Code It!' button")
            fuzzy_button.click()
            print("   ✓ Clicked the button")
            
            # Wait for code generation
            print("   ⏳ Waiting for code generation...")
            agent.page.wait_for_timeout(5000)
            
            agent.page.screenshot(path='/home/ubuntu/screenshots/fuzzy_step3_code_generated.png')
            print("   ✓ Screenshot saved: fuzzy_step3_code_generated.png")
        
        # 4. Check for generated code
        print("\n4. Checking for generated code...")
        
        # Look for code display area (usually in pre, code, or textarea elements)
        code_areas = agent.page.locator('pre, code, .code-output, .output, textarea').all()
        code_found = False
        
        for area in code_areas:
            text = area.inner_text().strip()
            if len(text) > 50:  # Assume generated code is longer than 50 chars
                code_found = True
                print("   ✓ Found generated code!")
                print(f"   Code preview: {text[:100]}...")
                break
        
        if not code_found:
            print("   ⚠ No generated code found (might need more wait time)")
        
        # 5. Explore other buttons
        print("\n5. Exploring other functionality...")
        
        # Try Sample Prompts button
        sample_prompts_btn = agent.page.locator('button:has-text("Sample Prompts")').first
        if sample_prompts_btn:
            print("   ✓ Found 'Sample Prompts' button")
            sample_prompts_btn.click()
            agent.page.wait_for_timeout(2000)
            
            agent.page.screenshot(path='/home/ubuntu/screenshots/fuzzy_step4_sample_prompts.png')
            print("   ✓ Screenshot saved: fuzzy_step4_sample_prompts.png")
            
            # Check if any modal or dropdown appeared
            modals = agent.page.locator('.modal, .dropdown, .popup, [role="dialog"]').all()
            if modals:
                print("   ✓ Sample prompts interface appeared")
        
        # 6. Try the "Play Now" link
        print("\n6. Checking the 'Play Now' link...")
        
        play_link = agent.page.locator('a:has-text("Play Now")').first
        if play_link:
            href = play_link.get_attribute('href')
            print(f"   ✓ Found 'Play Now' link pointing to: {href}")
            
            # Click it in a new tab to preserve our current state
            with agent.context.expect_page() as new_page_info:
                play_link.click(modifiers=['Control'])  # Ctrl+click for new tab
            
            try:
                new_page = new_page_info.value
                new_page.wait_for_load_state('networkidle')
                new_page.wait_for_timeout(2000)
                
                new_title = new_page.title()
                new_url = new_page.url
                print(f"   ✓ New page opened: {new_title}")
                print(f"   URL: {new_url}")
                
                new_page.screenshot(path='/home/ubuntu/screenshots/fuzzy_step5_play_page.png')
                print("   ✓ Screenshot saved: fuzzy_step5_play_page.png")
                
                new_page.close()
            except:
                print("   ⚠ Could not open in new tab, might be same-page navigation")
        
        # 7. Summary of navigation capabilities
        print("\n7. NAVIGATION SUMMARY:")
        print("   - Main interface is a code generation tool")
        print("   - Primary interaction: Enter prompt → Click 'Fuzzy Code It!' → View generated code")
        print("   - Additional features: Sample prompts, Example apps, Save/Load functionality")
        print("   - 'Play Now' link leads to additional content/games")
        print("   - The site uses a modern single-page application design")
        
        # 8. Create a navigation map
        navigation_map = {
            "main_page": "https://fuzzycode.dev",
            "primary_action": "Enter prompt and generate code",
            "key_elements": {
                "prompt_input": "Main textarea for entering coding requests",
                "generate_button": "Fuzzy Code It! - triggers code generation",
                "sample_prompts": "Pre-made prompt examples",
                "example_apps": "Example applications",
                "save_load": "Save/Load/Share functionality",
                "clear": "Clear the workspace",
                "suggest_fixes": "Get fix suggestions",
                "suggest_improvements": "Get improvement suggestions"
            },
            "external_links": {
                "play_now": "https://pages.fuzzycode.dev/ - Additional games/content"
            }
        }
        
        print("\n8. NAVIGATION MAP:")
        import json
        print(json.dumps(navigation_map, indent=2))
        
        return navigation_map
        
    except Exception as e:
        print(f"\nError during navigation: {e}")
        return None
    finally:
        agent.stop()
        print("\n✓ Navigation demo complete!")

if __name__ == "__main__":
    navigate_fuzzycode_demo()