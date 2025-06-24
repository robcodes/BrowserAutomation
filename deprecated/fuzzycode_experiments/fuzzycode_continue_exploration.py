#!/usr/bin/env python3
"""
Continue exploring FuzzyCode after successful login
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def continue_exploration():
    """Continue exploring after login"""
    print("=== Continuing FuzzyCode Exploration ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Step 19: Close the welcome modal
    print("\n→ Step 19: Closing welcome modal...")
    
    close_result = await client.evaluate("""
        () => {
            // Try to click the X button on the modal
            const closeButtons = Array.from(document.querySelectorAll('button')).filter(btn => 
                btn.textContent === '×' || btn.textContent === 'X' || 
                btn.getAttribute('aria-label')?.includes('close')
            );
            
            if (closeButtons.length > 0) {
                closeButtons[0].click();
                return { success: true, method: 'x-button' };
            }
            
            // Try clicking outside the modal
            const backdrop = document.querySelector('.modal-backdrop, [class*="backdrop"]');
            if (backdrop) {
                backdrop.click();
                return { success: true, method: 'backdrop' };
            }
            
            // Try clicking on the main content behind the modal
            const mainContent = document.querySelector('#root, .main, body');
            if (mainContent) {
                mainContent.click();
                return { success: true, method: 'main-content' };
            }
            
            return { success: false };
        }
    """)
    
    print(f"  Close result: {close_result}")
    
    await client.wait(1000)
    await client.screenshot("fuzzy_explore_23_modal_closed.png")
    print("  ✓ Screenshot: fuzzy_explore_23_modal_closed.png")
    
    # Step 20: Test authenticated code generation
    print("\n→ Step 20: Testing authenticated code generation...")
    
    # Fill textarea with a test prompt
    fill_result = await client.evaluate("""
        () => {
            const textarea = document.querySelector('textarea');
            if (textarea) {
                textarea.focus();
                textarea.value = 'Write a Python function that checks if a number is prime';
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                textarea.dispatchEvent(new Event('change', { bubbles: true }));
                return { success: true };
            }
            return { success: false };
        }
    """)
    
    if fill_result['success']:
        await client.screenshot("fuzzy_explore_24_auth_prompt.png")
        print("  ✓ Filled authenticated prompt")
        
        # Click generate
        generate_result = await client.evaluate("""
            () => {
                const btn = document.querySelector('#processTextButton') || 
                           Array.from(document.querySelectorAll('button')).find(btn => 
                               btn.textContent.includes('Fuzzy Code It'));
                if (btn && !btn.disabled) {
                    btn.click();
                    return { success: true };
                }
                return { success: false, disabled: btn?.disabled };
            }
        """)
        
        if generate_result['success']:
            print("  ✓ Clicked generate button")
            await client.wait(5000)
            await client.screenshot("fuzzy_explore_25_auth_generated.png")
            print("  ✓ Screenshot: fuzzy_explore_25_auth_generated.png")
            
            # Check for generated code
            code_check = await client.evaluate("""
                () => {
                    const codeElements = Array.from(document.querySelectorAll('pre, code, [class*="code"]'));
                    const hasCode = codeElements.some(el => 
                        el.textContent.includes('def') || 
                        el.textContent.includes('function') ||
                        el.textContent.includes('prime')
                    );
                    
                    return {
                        hasCode: hasCode,
                        codeBlockCount: codeElements.length,
                        sampleCode: codeElements[0]?.textContent.substring(0, 100)
                    };
                }
            """)
            
            print(f"\n  Code generation result:")
            print(f"    Has code: {code_check['hasCode']}")
            print(f"    Code blocks: {code_check['codeBlockCount']}")
            if code_check['sampleCode']:
                print(f"    Sample: {code_check['sampleCode']}...")
    
    # Step 21: Explore UI elements
    print("\n\n→ Step 21: Exploring UI elements...")
    
    ui_analysis = await client.evaluate("""
        () => {
            // Find all interactive elements
            const buttons = Array.from(document.querySelectorAll('button'));
            const selects = Array.from(document.querySelectorAll('select'));
            const links = Array.from(document.querySelectorAll('a'));
            
            // Look for specific features
            const versionDropdown = selects.find(s => s.textContent.includes('Version'));
            const themeButtons = buttons.filter(b => 
                b.textContent.includes('theme') || 
                b.className.includes('theme')
            );
            
            // Check bottom toolbar
            const bottomElements = Array.from(document.querySelectorAll('*')).filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.bottom > window.innerHeight - 100 && el.offsetParent !== null;
            });
            
            return {
                buttonCount: buttons.length,
                buttonTexts: buttons.map(b => b.textContent.trim()).filter(t => t && t.length < 20),
                selectCount: selects.length,
                linkCount: links.length,
                hasVersionDropdown: versionDropdown !== undefined,
                themeButtonCount: themeButtons.length,
                bottomToolbarElements: bottomElements.length
            };
        }
    """)
    
    print(f"  UI Analysis:")
    print(f"    Buttons: {ui_analysis['buttonCount']} ({', '.join(ui_analysis['buttonTexts'][:10])})")
    print(f"    Dropdowns: {ui_analysis['selectCount']}")
    print(f"    Links: {ui_analysis['linkCount']}")
    print(f"    Version dropdown: {ui_analysis['hasVersionDropdown']}")
    print(f"    Theme buttons: {ui_analysis['themeButtonCount']}")
    print(f"    Bottom toolbar elements: {ui_analysis['bottomToolbarElements']}")
    
    # Update final tracking
    with open("FUZZY_CODE_STEPS.md", "a") as f:
        f.write("\n## Post-Login Exploration\n")
        f.write("19. Closed welcome modal after successful login\n")
        f.write("20. Tested authenticated code generation with prime number function\n")
        f.write("21. Analyzed UI elements - found buttons, dropdowns, and toolbar\n")
    
    print("\n✅ Exploration phase complete!")

if __name__ == "__main__":
    asyncio.run(continue_exploration())