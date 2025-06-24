#!/usr/bin/env python3
"""
Find and fill the hidden required field
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def find_hidden_field():
    """Find and fill the hidden required field"""
    print("=== Finding Hidden Required Field ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Find all input fields including hidden ones
    all_inputs = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            const iframeDoc = loginIframe.contentDocument;
            const form = iframeDoc.querySelector('form');
            const inputs = form ? Array.from(form.querySelectorAll('input')) : [];
            
            return inputs.map((input, index) => ({
                index: index,
                type: input.type,
                name: input.name,
                id: input.id,
                placeholder: input.placeholder,
                required: input.required,
                value: input.value,
                visible: input.offsetParent !== null,
                display: window.getComputedStyle(input).display,
                visibility: window.getComputedStyle(input).visibility,
                width: input.offsetWidth,
                height: input.offsetHeight,
                className: input.className,
                hasLabel: iframeDoc.querySelector(`label[for="${input.id}"]`) !== null
            }));
        }
    """)
    
    print("All form inputs found:")
    for input in all_inputs:
        print(f"\n  Input #{input['index']}:")
        print(f"    Type: {input['type']}")
        print(f"    Name: {input['name']}")
        print(f"    ID: {input['id']}")
        print(f"    Placeholder: {input['placeholder']}")
        print(f"    Required: {input['required']}")
        print(f"    Value: '{input['value']}'")
        print(f"    Visible: {input['visible']}")
        print(f"    Display: {input['display']}")
        print(f"    Dimensions: {input['width']}x{input['height']}")
        print(f"    Has label: {input['hasLabel']}")
    
    # Find the empty required text field
    empty_text_field = next((inp for inp in all_inputs if inp['type'] == 'text' and inp['required'] and not inp['value']), None)
    
    if empty_text_field:
        print(f"\n⚠️ Found empty required text field: {empty_text_field}")
        
        # Check if it's the username field that might be separate from email
        fill_result = await client.evaluate("""
            () => {
                const loginIframe = Array.from(document.querySelectorAll('iframe'))
                    .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
                
                const iframeDoc = loginIframe.contentDocument;
                const form = iframeDoc.querySelector('form');
                const textInputs = form ? Array.from(form.querySelectorAll('input[type="text"]')) : [];
                
                // Fill the first empty required text input with the email
                for (let input of textInputs) {
                    if (input.required && !input.value) {
                        input.focus();
                        input.value = 'robert.norbeau+test2@gmail.com';
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        return {
                            filled: true,
                            fieldId: input.id,
                            fieldName: input.name
                        };
                    }
                }
                
                return { filled: false };
            }
        """)
        
        print(f"\nFill result: {fill_result}")
        
        await client.wait(1000)
        
    # Re-check form validity
    final_check = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            const iframeDoc = loginIframe.contentDocument;
            const form = iframeDoc.querySelector('form');
            const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                               Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                   btn.textContent.includes('Sign'));
            
            // Get all input values
            const inputs = form ? Array.from(form.querySelectorAll('input')) : [];
            const inputValues = {};
            inputs.forEach(input => {
                const key = input.name || input.type || `input_${input.id}`;
                inputValues[key] = {
                    value: input.value,
                    valid: input.checkValidity(),
                    required: input.required
                };
            });
            
            return {
                formValid: form ? form.checkValidity() : null,
                buttonDisabled: submitButton ? submitButton.disabled : null,
                inputs: inputValues
            };
        }
    """)
    
    print("\nFinal form state:")
    print(f"  Form valid: {final_check['formValid']}")
    print(f"  Button disabled: {final_check['buttonDisabled']}")
    print("\n  Input values:")
    for key, value in final_check['inputs'].items():
        print(f"    {key}: '{value['value']}' (valid: {value['valid']}, required: {value['required']})")
    
    # Take screenshot
    await client.screenshot("screenshots/debug_3_all_fields_filled.png")
    print("\n✓ Screenshot saved: debug_3_all_fields_filled.png")
    
    # If button is enabled, click it
    if not final_check['buttonDisabled']:
        print("\n✅ Button is enabled! Clicking Sign In...")
        
        click_result = await client.evaluate("""
            () => {
                const loginIframe = Array.from(document.querySelectorAll('iframe'))
                    .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
                
                const iframeDoc = loginIframe.contentDocument;
                const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                                   Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                       btn.textContent.includes('Sign'));
                
                if (submitButton && !submitButton.disabled) {
                    submitButton.click();
                    return { success: true };
                }
                return { success: false };
            }
        """)
        
        if click_result['success']:
            print("✓ Clicked Sign In button!")
            await client.wait(2000)
            await client.screenshot("screenshots/debug_4_after_login.png")
            print("✓ Screenshot saved: debug_4_after_login.png")

if __name__ == "__main__":
    asyncio.run(find_hidden_field())