#!/usr/bin/env python3
"""
Systematic exploration of FuzzyCode following best practices
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def explore_fuzzycode():
    """Explore FuzzyCode systematically"""
    print("=== FuzzyCode Systematic Exploration ===\n")
    
    # Step 1: Create new session
    client = EnhancedBrowserClient()
    session_id = await client.create_session()
    
    # Save session for future use
    session_data = {
        "session_id": session_id,
        "page_id": None,
        "created_at": asyncio.get_event_loop().time()
    }
    
    print(f"✓ Step 1: Created browser session: {session_id}")
    
    # Step 2: Navigate to FuzzyCode
    await client.connect_session(session_id)
    page_id = await client.new_page("https://fuzzycode.dev")
    session_data["page_id"] = page_id
    
    # Save session data
    with open("fuzzycode_exploration_session.json", "w") as f:
        json.dump(session_data, f, indent=2)
    
    print("✓ Step 2: Navigated to https://fuzzycode.dev")
    
    # Wait for page to fully load
    await client.wait(3000)
    
    # Step 3: Take initial screenshot
    await client.screenshot("fuzzy_explore_01_initial.png")
    print("✓ Step 3: Screenshot saved - fuzzy_explore_01_initial.png")
    
    # Step 4: Analyze page structure
    page_analysis = await client.evaluate("""
        () => {
            // Main elements
            const textarea = document.querySelector('textarea');
            const generateBtn = document.querySelector('#processTextButton') || 
                              Array.from(document.querySelectorAll('button')).find(btn => 
                                  btn.textContent.includes('Fuzzy Code It'));
            
            // Navigation elements
            const navButtons = Array.from(document.querySelectorAll('nav button, header button, [role="navigation"] button'));
            const dropdowns = Array.from(document.querySelectorAll('select, [role="combobox"]'));
            
            // Top bar elements
            const topBarElements = Array.from(document.querySelectorAll('[class*="header"] *, [class*="nav"] *, [class*="top"] *'))
                .filter(el => el.offsetParent !== null && el.getBoundingClientRect().top < 100);
            
            return {
                hasTextarea: textarea !== null,
                textareaPlaceholder: textarea ? textarea.placeholder : null,
                hasGenerateButton: generateBtn !== null,
                generateButtonText: generateBtn ? generateBtn.textContent.trim() : null,
                navButtonCount: navButtons.length,
                navButtonTexts: navButtons.map(btn => btn.textContent.trim()).filter(t => t),
                dropdownCount: dropdowns.length,
                topBarElementTypes: [...new Set(topBarElements.map(el => el.tagName.toLowerCase()))].slice(0, 10)
            };
        }
    """)
    
    print("\n✓ Step 4: Analyzed page structure")
    print(f"  - Textarea: {page_analysis['hasTextarea']} (placeholder: '{page_analysis['textareaPlaceholder']}')")
    print(f"  - Generate button: {page_analysis['hasGenerateButton']} (text: '{page_analysis['generateButtonText']}')")
    print(f"  - Navigation buttons: {page_analysis['navButtonCount']} buttons found")
    if page_analysis['navButtonTexts']:
        print(f"    Buttons: {', '.join(page_analysis['navButtonTexts'][:5])}")
    print(f"  - Dropdowns: {page_analysis['dropdownCount']}")
    print(f"  - Top bar elements: {', '.join(page_analysis['topBarElementTypes'])}")
    
    # Step 5: Look for authentication elements
    auth_elements = await client.evaluate("""
        () => {
            // Look for login/profile elements
            const profileElements = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = el.textContent.toLowerCase();
                const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                return (text.includes('login') || text.includes('sign in') || 
                        text.includes('profile') || text.includes('account') ||
                        ariaLabel.includes('profile') || ariaLabel.includes('account')) &&
                       el.offsetParent !== null;
            });
            
            // Look for avatar elements
            const avatarElements = Array.from(document.querySelectorAll('[class*="avatar"], [id*="avatar"], fuzzy-avatar, img[alt*="profile"], img[alt*="avatar"]'));
            
            // Check top-right area for profile
            const topRightElements = Array.from(document.querySelectorAll('*')).filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.top < 100 && rect.right > window.innerWidth - 150 && el.offsetParent !== null;
            });
            
            return {
                profileElementCount: profileElements.length,
                avatarElementCount: avatarElements.length,
                avatarTags: avatarElements.map(el => el.tagName.toLowerCase()).slice(0, 5),
                topRightElementCount: topRightElements.length,
                topRightClickable: topRightElements.filter(el => 
                    el.tagName === 'BUTTON' || el.tagName === 'A' || el.onclick || el.style.cursor === 'pointer'
                ).length
            };
        }
    """)
    
    print("\n✓ Step 5: Searched for authentication elements")
    print(f"  - Profile elements: {auth_elements['profileElementCount']}")
    print(f"  - Avatar elements: {auth_elements['avatarElementCount']} ({', '.join(auth_elements['avatarTags'])})")
    print(f"  - Top-right elements: {auth_elements['topRightElementCount']} ({auth_elements['topRightClickable']} clickable)")
    
    # Step 6: Test anonymous code generation
    print("\n✓ Step 6: Testing anonymous code generation")
    
    # Fill textarea
    test_prompt = "Write a Python function to reverse a string"
    fill_result = await client.evaluate(f"""
        () => {{
            const textarea = document.querySelector('textarea');
            if (textarea) {{
                textarea.focus();
                textarea.value = '{test_prompt}';
                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return {{ success: true, value: textarea.value }};
            }}
            return {{ success: false }};
        }}
    """)
    
    if fill_result['success']:
        print(f"  - Filled textarea with: '{test_prompt}'")
        await client.wait(500)
        await client.screenshot("fuzzy_explore_02_prompt_filled.png")
        print("  - Screenshot: fuzzy_explore_02_prompt_filled.png")
        
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
                return { success: false, disabled: btn ? btn.disabled : null };
            }
        """)
        
        if generate_result['success']:
            print("  - Clicked generate button")
            await client.wait(3000)
            await client.screenshot("fuzzy_explore_03_after_generate.png")
            print("  - Screenshot: fuzzy_explore_03_after_generate.png")
            
            # Check for output
            output_check = await client.evaluate("""
                () => {
                    const codeBlocks = Array.from(document.querySelectorAll('pre, code, [class*="code"], [class*="output"]'));
                    const hasOutput = codeBlocks.some(el => el.textContent.includes('def') || el.textContent.includes('function'));
                    return {
                        hasOutput: hasOutput,
                        codeBlockCount: codeBlocks.length
                    };
                }
            """)
            
            print(f"  - Code output found: {output_check['hasOutput']} ({output_check['codeBlockCount']} code blocks)")
    
    # Check console logs for any errors
    console_logs = await client.get_console_logs(limit=20)
    errors = [log for log in console_logs["logs"] if log["type"] == "error"]
    if errors:
        print("\n⚠️ Console errors detected:")
        for error in errors[-5:]:
            print(f"  - {error['text'][:100]}...")
    
    print("\n✅ Initial exploration complete. Check tracking files for progress.")

if __name__ == "__main__":
    asyncio.run(explore_fuzzycode())