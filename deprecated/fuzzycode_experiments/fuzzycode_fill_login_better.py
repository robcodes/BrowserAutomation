#!/usr/bin/env python3
"""
Better login form filling
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def fill_login_better():
    """Fill login form with better selectors"""
    print("=== Filling Login Form (Better Method) ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # First, let's find all input fields in the visible modal
    inputs_info = await client.evaluate("""
        () => {
            const inputs = Array.from(document.querySelectorAll('input'));
            return inputs.map((input, index) => ({
                index: index,
                type: input.type,
                name: input.name,
                placeholder: input.placeholder,
                id: input.id,
                visible: input.offsetParent !== null,
                value: input.value,
                position: {
                    x: input.getBoundingClientRect().left,
                    y: input.getBoundingClientRect().top
                }
            })).filter(i => i.visible);
        }
    """)
    
    print(f"Found {len(inputs_info)} visible input fields:")
    for inp in inputs_info:
        print(f"  #{inp['index']}: type='{inp['type']}', placeholder='{inp['placeholder']}', name='{inp['name']}'")
    
    # Fill by index if we found exactly 2 inputs (username and password)
    if len(inputs_info) >= 2:
        print("\n→ Filling by input index...")
        
        # Fill first input (email/username)
        email_result = await client.evaluate(f"""
            () => {{
                const inputs = Array.from(document.querySelectorAll('input')).filter(i => i.offsetParent !== null);
                if (inputs.length >= 1) {{
                    inputs[0].focus();
                    inputs[0].value = 'robert.norbeau+test2@gmail.com';
                    inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }}
                return false;
            }}
        """)
        
        print(f"  Email filled: {email_result}")
        
        await client.wait(500)
        
        # Fill second input (password)
        password_result = await client.evaluate(f"""
            () => {{
                const inputs = Array.from(document.querySelectorAll('input')).filter(i => i.offsetParent !== null);
                if (inputs.length >= 2) {{
                    inputs[1].focus();
                    inputs[1].value = 'robert.norbeau+test2';
                    inputs[1].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[1].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }}
                return false;
            }}
        """)
        
        print(f"  Password filled: {password_result}")
        
        if email_result and password_result:
            await client.wait(1000)
            await client.screenshot("fuzzycode_login_form_filled.png")
            print("\n✓ Form filled! Screenshot taken.")
            
            # Find and click submit button
            print("\n→ Looking for Sign In button...")
            
            button_info = await client.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button')).filter(b => b.offsetParent !== null);
                    return buttons.map(b => ({
                        text: b.textContent.trim(),
                        type: b.type,
                        visible: b.offsetParent !== null
                    }));
                }
            """)
            
            print(f"Found {len(button_info)} visible buttons:")
            for btn in button_info:
                print(f"  - '{btn['text']}' (type: {btn['type']})")
            
            # Click the Sign In button
            sign_in_result = await client.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button')).filter(b => b.offsetParent !== null);
                    const signInBtn = buttons.find(b => b.textContent.trim().toLowerCase() === 'sign in');
                    
                    if (signInBtn) {
                        signInBtn.click();
                        return { clicked: true, text: signInBtn.textContent };
                    }
                    
                    // If not found, click the first visible button
                    if (buttons.length > 0) {
                        buttons[0].click();
                        return { clicked: true, text: buttons[0].textContent };
                    }
                    
                    return { clicked: false };
                }
            """)
            
            print(f"\n  Sign In result: {sign_in_result}")
            
            if sign_in_result['clicked']:
                print("\n✓ Submitted! Waiting for response...")
                await client.wait(3000)
                await client.screenshot("fuzzycode_after_signin.png")
                
                # Check if we're logged in
                page_state = await client.evaluate("""
                    () => {
                        // Check if modal is gone
                        const modal = document.querySelector('.modal, [role="dialog"]');
                        const modalGone = !modal || modal.offsetParent === null;
                        
                        // Check URL
                        const url = window.location.href;
                        
                        // Look for user info
                        const pageText = document.body.textContent;
                        const hasUserEmail = pageText.includes('robert.norbeau');
                        
                        return {
                            modalGone: modalGone,
                            url: url,
                            hasUserEmail: hasUserEmail
                        };
                    }
                """)
                
                print(f"\nPost-login state:")
                print(f"  Modal gone: {page_state['modalGone']}")
                print(f"  URL: {page_state['url']}")
                print(f"  User email visible: {page_state['hasUserEmail']}")

if __name__ == "__main__":
    asyncio.run(fill_login_better())