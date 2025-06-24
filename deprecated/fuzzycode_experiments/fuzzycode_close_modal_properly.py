#!/usr/bin/env python3
"""
Close the login modal properly
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def close_modal_properly():
    """Close the login modal by clicking the X button"""
    print("=== Closing Login Modal ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Click the X button in the top right of the modal
    print("→ Looking for modal close button...")
    
    close_result = await client.evaluate("""
        () => {
            // Look for the X button in the Sign In modal header
            const modalHeader = document.querySelector('[class*="modal-header"], .modal-header, header');
            if (modalHeader) {
                // Find X button - it's likely in the top right
                const closeBtn = modalHeader.querySelector('button[aria-label*="close"], button[title*="close"], button.close, button:has(svg)');
                if (closeBtn) {
                    closeBtn.click();
                    return { success: true, method: 'header-close-button' };
                }
            }
            
            // Look for any button with × or X
            const allButtons = Array.from(document.querySelectorAll('button'));
            for (let btn of allButtons) {
                const rect = btn.getBoundingClientRect();
                // Check if button is in top-right area and contains close symbol
                if (rect.top < 100 && rect.right > window.innerWidth - 100) {
                    if (btn.textContent.includes('×') || btn.textContent.includes('X') || 
                        btn.innerHTML.includes('close') || btn.innerHTML.includes('svg')) {
                        btn.click();
                        return { success: true, method: 'top-right-button', text: btn.textContent.trim() };
                    }
                }
            }
            
            // Try clicking on any visible backdrop/overlay
            const overlays = document.querySelectorAll('[class*="backdrop"], [class*="overlay"], .modal-backdrop');
            for (let overlay of overlays) {
                if (overlay.offsetParent !== null) {
                    overlay.click();
                    return { success: true, method: 'backdrop-click' };
                }
            }
            
            return { success: false, message: 'Could not find close button' };
        }
    """)
    
    print(f"  Close result: {close_result}")
    
    await client.wait(1000)
    
    # Verify modal is closed
    modal_check = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login'));
            const hasModal = loginIframe ? (loginIframe.offsetParent !== null) : false;
            
            // Check if main content is accessible
            const textarea = document.querySelector('textarea');
            const hasTextarea = textarea !== null;
            
            return {
                modalStillVisible: hasModal,
                mainContentAccessible: hasTextarea
            };
        }
    """)
    
    print(f"\n  Modal still visible: {modal_check['modalStillVisible']}")
    print(f"  Main content accessible: {modal_check['mainContentAccessible']}")
    
    if modal_check['modalStillVisible']:
        # Force reload the page
        print("\n→ Modal still visible, reloading page...")
        await client.goto("https://fuzzycode.dev")
        await client.wait(3000)
    
    await client.screenshot("screenshots/modal_closed_main_page.png")
    print("\n✓ Screenshot saved: modal_closed_main_page.png")
    
    # Now try to generate code
    print("\n→ Attempting to generate code...")
    
    # Fill the textarea
    prompt_text = "Create a Python function that calculates the factorial of a number using recursion"
    
    fill_result = await client.evaluate(f"""
        () => {{
            const textarea = document.querySelector('textarea');
            if (textarea) {{
                textarea.focus();
                textarea.value = `{prompt_text}`;
                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return {{ success: true }};
            }}
            return {{ success: false, message: 'No textarea found' }};
        }}
    """)
    
    print(f"  Fill textarea: {fill_result}")
    
    if fill_result['success']:
        await client.wait(500)
        await client.screenshot("screenshots/prompt_filled_logged_in.png")
        print("✓ Screenshot saved: prompt_filled_logged_in.png")
        
        # Click generate button
        generate_result = await client.evaluate("""
            () => {
                const button = document.querySelector('#processTextButton') ||
                             Array.from(document.querySelectorAll('button')).find(btn =>
                                 btn.textContent.includes('Fuzzy Code It') ||
                                 btn.textContent.includes('Generate')
                             );
                
                if (button && !button.disabled) {
                    button.click();
                    return { success: true };
                }
                return { success: false, buttonFound: button !== null };
            }
        """)
        
        print(f"  Generate click: {generate_result}")
        
        if generate_result['success']:
            print("\n⏳ Waiting for code generation...")
            await client.wait(5000)
            
            await client.screenshot("screenshots/code_generated_logged_in.png")
            print("✓ Screenshot saved: code_generated_logged_in.png")
            
            # Check network logs
            network_logs = await client.get_network_logs(limit=10)
            api_calls = [log for log in network_logs["logs"] if 'api' in log['url'] or 'prompt' in log['url']]
            
            if api_calls:
                print("\n📡 Recent API calls:")
                for call in api_calls[-5:]:
                    print(f"  {call['type']}: {call['url']} -> {call.get('status', '?')}")
            
            print("\n✅ Process completed! Check the screenshots.")

if __name__ == "__main__":
    asyncio.run(close_modal_properly())