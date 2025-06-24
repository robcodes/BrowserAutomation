#!/usr/bin/env python3
"""
Final login attempt with proper field identification
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def login_final():
    """Login with proper field identification"""
    print("=== Final Login Attempt ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # First, let's identify the fields properly
    print("→ Identifying form fields in iframe...")
    
    field_analysis = await client.evaluate("""
        () => {
            const iframe = Array.from(document.querySelectorAll('iframe'))
                .find(f => f.offsetParent !== null);
            
            if (!iframe) return { error: 'No iframe' };
            
            const iframeDoc = iframe.contentDocument;
            const inputs = Array.from(iframeDoc.querySelectorAll('input'));
            
            return inputs.map((input, idx) => ({
                index: idx,
                type: input.type,
                placeholder: input.placeholder,
                id: input.id,
                name: input.name,
                value: input.value,
                visible: input.offsetParent !== null
            }));
        }
    """)
    
    print("  Found inputs:")
    for inp in field_analysis:
        print(f"    [{inp['index']}] type={inp['type']}, placeholder='{inp['placeholder']}', value='{inp['value']}'")
    
    # Now fill both fields correctly
    print("\n→ Filling both fields by placeholder...")
    
    fill_result = await client.evaluate("""
        () => {
            const iframe = Array.from(document.querySelectorAll('iframe'))
                .find(f => f.offsetParent !== null);
            
            if (!iframe) return { error: 'No iframe' };
            
            const iframeDoc = iframe.contentDocument;
            
            // Find username field by placeholder
            const usernameInput = Array.from(iframeDoc.querySelectorAll('input')).find(input => 
                input.placeholder.toLowerCase().includes('username') || 
                input.placeholder.toLowerCase().includes('email')
            );
            
            // Find password field by type
            const passwordInput = iframeDoc.querySelector('input[type="password"]');
            
            if (usernameInput && passwordInput) {
                // Clear and fill username
                usernameInput.focus();
                usernameInput.value = '';
                usernameInput.value = 'robert.norbeau+test2@gmail.com';
                usernameInput.dispatchEvent(new Event('input', { bubbles: true }));
                usernameInput.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Clear and fill password
                passwordInput.focus();
                passwordInput.value = '';
                passwordInput.value = 'robert.norbeau+test2';
                passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                
                return {
                    success: true,
                    usernameValue: usernameInput.value,
                    passwordLength: passwordInput.value.length
                };
            }
            
            return { success: false };
        }
    """)
    
    print(f"  Fill result: {fill_result}")
    
    if fill_result['success']:
        await client.wait(500)
        await client.screenshot("fuzzy_explore_17_correctly_filled.png")
        print("  ✓ Screenshot: fuzzy_explore_17_correctly_filled.png")
        
        # Now click Sign In
        print("\n→ Clicking Sign In button...")
        
        click_result = await client.evaluate("""
            () => {
                const iframe = Array.from(document.querySelectorAll('iframe'))
                    .find(f => f.offsetParent !== null);
                const iframeDoc = iframe.contentDocument;
                
                // Find Sign In button
                const signInButton = Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                    btn.textContent.includes('Sign')
                );
                
                if (signInButton && !signInButton.disabled) {
                    signInButton.click();
                    return { success: true, clicked: true };
                }
                
                return { 
                    success: false, 
                    disabled: signInButton ? signInButton.disabled : null,
                    found: signInButton !== null
                };
            }
        """)
        
        print(f"  Click result: {click_result}")
        
        if click_result.get('success'):
            print("  ✓ Successfully clicked Sign In!")
            await client.wait(3000)
            await client.screenshot("fuzzy_explore_18_login_complete.png")
            print("  ✓ Screenshot: fuzzy_explore_18_login_complete.png")
            
            # Check if login succeeded
            login_check = await client.evaluate("""
                () => {
                    // Check if iframe is still visible
                    const iframe = Array.from(document.querySelectorAll('iframe'))
                        .find(f => f.offsetParent !== null && f.getBoundingClientRect().width > 100);
                    
                    return {
                        iframeStillVisible: iframe !== undefined,
                        pageText: document.body.textContent.substring(0, 200)
                    };
                }
            """)
            
            print("\n  Login check:")
            print(f"    Login modal still visible: {login_check['iframeStillVisible']}")

if __name__ == "__main__":
    asyncio.run(login_final())