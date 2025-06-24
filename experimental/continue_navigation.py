#!/usr/bin/env python3
"""
Continue navigation based on checkpoint analysis
"""
from interactive_navigation import InteractiveNavigator
import json

def continue_from_checkpoint():
    """Continue navigation based on what we learned from the checkpoint"""
    nav = InteractiveNavigator()
    
    print("\n=== Continuing Navigation from Checkpoint ===")
    print("Based on screenshot analysis:")
    print("- Main textarea is visible at the top")
    print("- 'Fuzzy Code It!' button is in the left panel")
    print("- Code output area is below")
    print("- Found 8 inputs (more than initially detected)")
    
    # Re-establish session
    state = nav.start_session("https://fuzzycode.dev")
    
    # Step 1: Fill the main textarea
    print("\n=== Step 1: Fill the prompt ===")
    # The main textarea is likely the first one
    success, state = nav.fill_input(
        'textarea',
        'Create a Python function that calculates the factorial of a number',
        'main_prompt'
    )
    
    if success:
        print("✓ Successfully filled the prompt")
        print(f"Current URL: {state['url']}")
    
    # Step 2: Click the Fuzzy Code It! button
    print("\n=== Step 2: Generate Code ===")
    success, state = nav.click_element(
        'button:has-text("Fuzzy Code It!")',
        'generate_code'
    )
    
    if success:
        print("✓ Clicked the generate button")
        
        # Step 3: Wait longer for code generation
        print("\n=== Step 3: Wait for Generation ===")
        state = nav.wait_and_screenshot(8, 'code_generation')
        
        # Step 4: Check the code output area
        print("\n=== Step 4: Check Results ===")
        # Try to find code in various possible containers
        code_selectors = [
            'pre', 'code', '.code-output', '#output', 
            'textarea:not(:first-of-type)', '.output-area'
        ]
        
        code_found = False
        for selector in code_selectors:
            try:
                elements = nav.agent.page.locator(selector).all()
                for element in elements:
                    text = element.inner_text().strip()
                    if len(text) > 50 and ('def' in text or 'function' in text or 'class' in text):
                        print(f"✓ Found generated code in {selector}")
                        print(f"Code preview: {text[:200]}...")
                        code_found = True
                        break
                if code_found:
                    break
            except:
                pass
        
        if not code_found:
            print("⚠ Code might be loading or in a different element")
    
    # Step 5: Explore other features
    print("\n=== Step 5: Explore Features ===")
    
    # Try the dropdown menu
    dropdown = nav.agent.page.locator('select, .dropdown').first
    if dropdown:
        try:
            # Get options
            options = nav.agent.page.locator('option').all()
            print(f"Found dropdown with {len(options)} options")
            nav.take_screenshot('dropdown_found')
        except:
            pass
    
    # Check the tabs/buttons in the toolbar
    toolbar_buttons = ['Sample Prompts', 'Example Apps', 'Create', 'Update']
    for button_text in toolbar_buttons:
        try:
            button = nav.agent.page.locator(f'button:has-text("{button_text}")').first
            if button and button.is_visible():
                print(f"✓ Found {button_text} button")
        except:
            pass
    
    # Final summary
    print("\n=== Navigation Summary ===")
    print(f"Total screenshots taken: {nav.step_count}")
    print("Key findings:")
    print("- Successfully interacted with the main prompt area")
    print("- Triggered code generation")
    print("- Site appears to be an AI-powered code generation tool")
    print("- Multiple features available through toolbar buttons")
    
    nav.close()

if __name__ == "__main__":
    continue_from_checkpoint()