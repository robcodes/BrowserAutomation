#!/usr/bin/env python3
"""
Complete login and generate code
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def complete_login_and_generate():
    """Complete the login process and generate code"""
    print("=== Completing Login and Generating Code ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    print("✓ Login successful - welcome message displayed")
    
    # Close the login modal by clicking outside or X button
    print("\n→ Closing login modal...")
    
    close_result = await client.evaluate("""
        () => {
            // Try to find and click the X button
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login'));
            
            if (loginIframe) {
                // Try clicking the X button on the modal container
                const closeButtons = Array.from(document.querySelectorAll('button, [aria-label*="close"], [title*="close"], .close'));
                for (let btn of closeButtons) {
                    if (btn.offsetParent && (btn.textContent.includes('×') || btn.textContent.includes('X'))) {
                        btn.click();
                        return { method: 'x-button', success: true };
                    }
                }
                
                // Try clicking outside the iframe
                const backdrop = document.querySelector('.modal-backdrop, [class*="backdrop"], [class*="overlay"]');
                if (backdrop) {
                    backdrop.click();
                    return { method: 'backdrop', success: true };
                }
                
                // As last resort, hide the iframe
                loginIframe.style.display = 'none';
                if (loginIframe.parentElement) {
                    loginIframe.parentElement.style.display = 'none';
                }
                return { method: 'hide', success: true };
            }
            
            return { method: 'none', success: false, message: 'No login iframe found' };
        }
    """)
    
    print(f"  Close result: {close_result}")
    
    await client.wait(1000)
    await client.screenshot("screenshots/after_login_closed.png")
    print("✓ Screenshot saved: after_login_closed.png")
    
    # Now try to generate code
    print("\n→ Looking for code generation interface...")
    
    interface_check = await client.evaluate("""
        () => {
            // Look for the main textarea
            const textareas = Array.from(document.querySelectorAll('textarea'));
            const mainTextarea = textareas.find(ta => 
                ta.placeholder.toLowerCase().includes('enter') || 
                ta.placeholder.toLowerCase().includes('code') ||
                ta.id === 'userInput'
            );
            
            // Look for generate button
            const buttons = Array.from(document.querySelectorAll('button'));
            const generateButton = buttons.find(btn => 
                btn.textContent.includes('Fuzzy Code It') ||
                btn.textContent.includes('Generate') ||
                btn.id === 'processTextButton'
            );
            
            return {
                hasTextarea: mainTextarea !== null,
                textareaId: mainTextarea ? mainTextarea.id : null,
                textareaPlaceholder: mainTextarea ? mainTextarea.placeholder : null,
                hasGenerateButton: generateButton !== null,
                buttonText: generateButton ? generateButton.textContent.trim() : null,
                buttonId: generateButton ? generateButton.id : null
            };
        }
    """)
    
    print(f"\nInterface check:")
    print(f"  Textarea found: {interface_check['hasTextarea']}")
    print(f"  Textarea placeholder: {interface_check['textareaPlaceholder']}")
    print(f"  Generate button found: {interface_check['hasGenerateButton']}")
    print(f"  Button text: {interface_check['buttonText']}")
    
    if interface_check['hasTextarea'] and interface_check['hasGenerateButton']:
        # Fill the textarea with a code request
        print("\n→ Filling code request...")
        
        prompt_text = "Create a Python function that calculates the factorial of a number using recursion"
        
        fill_result = await client.evaluate(f"""
            () => {{
                const textarea = document.querySelector('textarea#{interface_check['textareaId']}') || 
                               document.querySelector('textarea');
                if (textarea) {{
                    textarea.focus();
                    textarea.value = `{prompt_text}`;
                    textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return {{ success: true, value: textarea.value }};
                }}
                return {{ success: false }};
            }}
        """)
        
        print(f"  Fill result: {fill_result}")
        
        await client.wait(500)
        await client.screenshot("screenshots/code_request_filled.png")
        print("✓ Screenshot saved: code_request_filled.png")
        
        # Click generate button
        print("\n→ Clicking generate button...")
        
        generate_result = await client.evaluate("""
            () => {
                const button = document.querySelector('#processTextButton') ||
                             Array.from(document.querySelectorAll('button')).find(btn =>
                                 btn.textContent.includes('Fuzzy Code It') ||
                                 btn.textContent.includes('Generate')
                             );
                
                if (button && !button.disabled) {
                    button.click();
                    return { success: true, clicked: true };
                }
                return { success: false, disabled: button ? button.disabled : null };
            }
        """)
        
        print(f"  Generate result: {generate_result}")
        
        if generate_result['success']:
            print("\n⏳ Waiting for code generation...")
            await client.wait(3000)
            
            await client.screenshot("screenshots/code_generated_final.png")
            print("✓ Screenshot saved: code_generated_final.png")
            
            # Check for generated code
            code_check = await client.evaluate("""
                () => {
                    // Look for code output areas
                    const codeElements = Array.from(document.querySelectorAll('pre, code, .code-output, [class*="output"]'));
                    const hasCode = codeElements.some(el => el.textContent.includes('def') || el.textContent.includes('function'));
                    
                    return {
                        hasCodeOutput: hasCode,
                        codeElementCount: codeElements.length
                    };
                }
            """)
            
            print(f"\n  Code output found: {code_check['hasCodeOutput']}")
            print(f"  Code elements: {code_check['codeElementCount']}")
            
            # Get console logs to see if there were any API calls
            console_logs = await client.get_console_logs(limit=10)
            errors = [log for log in console_logs["logs"] if log["type"] == "error"]
            if errors:
                print("\n⚠️ Recent console errors:")
                for error in errors[-5:]:
                    print(f"  {error['text']}")
            
            print("\n✅ Process completed! Check the screenshots to see the results.")
    else:
        print("\n❌ Could not find code generation interface. The page may need to reload.")

if __name__ == "__main__":
    asyncio.run(complete_login_and_generate())