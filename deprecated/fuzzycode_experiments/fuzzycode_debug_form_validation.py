#!/usr/bin/env python3
"""
Debug form validation requirements
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def debug_form_validation():
    """Debug why form validation is failing"""
    print("=== Debugging Form Validation ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Take initial screenshot
    await client.screenshot("screenshots/debug_1_initial.png")
    print("✓ Screenshot 1: Initial state")
    
    # Examine form structure and requirements
    form_analysis = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            if (!loginIframe) return { error: 'No login iframe' };
            
            const iframeDoc = loginIframe.contentDocument;
            const form = iframeDoc.querySelector('form');
            const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                             iframeDoc.querySelector('input[type="text"]');
            const passwordInput = iframeDoc.querySelector('input[type="password"]');
            
            // Get all input attributes and validation
            const result = {
                formExists: form !== null,
                formId: form ? form.id : null,
                formClass: form ? form.className : null,
                emailField: {
                    exists: emailInput !== null,
                    type: emailInput ? emailInput.type : null,
                    name: emailInput ? emailInput.name : null,
                    id: emailInput ? emailInput.id : null,
                    required: emailInput ? emailInput.required : null,
                    pattern: emailInput ? emailInput.pattern : null,
                    minLength: emailInput ? emailInput.minLength : null,
                    maxLength: emailInput ? emailInput.maxLength : null,
                    placeholder: emailInput ? emailInput.placeholder : null,
                    value: emailInput ? emailInput.value : null,
                    validity: emailInput ? {
                        valid: emailInput.validity.valid,
                        valueMissing: emailInput.validity.valueMissing,
                        typeMismatch: emailInput.validity.typeMismatch,
                        patternMismatch: emailInput.validity.patternMismatch
                    } : null
                },
                passwordField: {
                    exists: passwordInput !== null,
                    type: passwordInput ? passwordInput.type : null,
                    name: passwordInput ? passwordInput.name : null,
                    id: passwordInput ? passwordInput.id : null,
                    required: passwordInput ? passwordInput.required : null,
                    minLength: passwordInput ? passwordInput.minLength : null,
                    maxLength: passwordInput ? passwordInput.maxLength : null,
                    placeholder: passwordInput ? passwordInput.placeholder : null,
                    hasValue: passwordInput ? passwordInput.value.length > 0 : false,
                    validity: passwordInput ? {
                        valid: passwordInput.validity.valid,
                        valueMissing: passwordInput.validity.valueMissing,
                        tooShort: passwordInput.validity.tooShort
                    } : null
                }
            };
            
            return result;
        }
    """)
    
    print("\nForm Analysis:")
    print(f"  Form exists: {form_analysis['formExists']}")
    print(f"  Form ID: {form_analysis['formId']}")
    print(f"  Form class: {form_analysis['formClass']}")
    
    print("\nEmail Field:")
    email = form_analysis['emailField']
    print(f"  Type: {email['type']}")
    print(f"  Name: {email['name']}")
    print(f"  Required: {email['required']}")
    print(f"  Pattern: {email['pattern']}")
    print(f"  Current value: {email['value']}")
    if email['validity']:
        print(f"  Valid: {email['validity']['valid']}")
        print(f"  Value missing: {email['validity']['valueMissing']}")
        print(f"  Type mismatch: {email['validity']['typeMismatch']}")
    
    print("\nPassword Field:")
    password = form_analysis['passwordField']
    print(f"  Type: {password['type']}")
    print(f"  Name: {password['name']}")
    print(f"  Required: {password['required']}")
    print(f"  Min length: {password['minLength']}")
    print(f"  Has value: {password['hasValue']}")
    if password['validity']:
        print(f"  Valid: {password['validity']['valid']}")
        print(f"  Value missing: {password['validity']['valueMissing']}")
    
    # Clear fields and fill them properly
    print("\n→ Clearing and filling fields properly...")
    
    fill_result = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            const iframeDoc = loginIframe.contentDocument;
            const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                             iframeDoc.querySelector('input[type="text"]');
            const passwordInput = iframeDoc.querySelector('input[type="password"]');
            
            // Clear and fill email
            if (emailInput) {
                emailInput.focus();
                emailInput.select();
                // Simulate backspace to clear
                emailInput.value = '';
                emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                
                // Type each character
                const email = 'robert.norbeau+test2@gmail.com';
                for (let char of email) {
                    emailInput.value += char;
                    emailInput.dispatchEvent(new Event('input', { bubbles: true }));
                    emailInput.dispatchEvent(new KeyboardEvent('keyup', { key: char, bubbles: true }));
                }
                emailInput.dispatchEvent(new Event('change', { bubbles: true }));
                emailInput.blur();
            }
            
            // Clear and fill password
            if (passwordInput) {
                passwordInput.focus();
                passwordInput.select();
                passwordInput.value = '';
                passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                
                // Type each character
                const password = 'robert.norbeau+test2';
                for (let char of password) {
                    passwordInput.value += char;
                    passwordInput.dispatchEvent(new Event('input', { bubbles: true }));
                    passwordInput.dispatchEvent(new KeyboardEvent('keyup', { key: char, bubbles: true }));
                }
                passwordInput.dispatchEvent(new Event('change', { bubbles: true }));
                passwordInput.blur();
            }
            
            return {
                emailValue: emailInput ? emailInput.value : '',
                passwordLength: passwordInput ? passwordInput.value.length : 0
            };
        }
    """)
    
    print(f"\nFill result:")
    print(f"  Email: {fill_result['emailValue']}")
    print(f"  Password length: {fill_result['passwordLength']}")
    
    await client.wait(1000)
    await client.screenshot("screenshots/debug_2_after_fill.png")
    print("✓ Screenshot 2: After filling fields")
    
    # Check validation state after filling
    validation_check = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
            
            const iframeDoc = loginIframe.contentDocument;
            const form = iframeDoc.querySelector('form');
            const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                             iframeDoc.querySelector('input[type="text"]');
            const passwordInput = iframeDoc.querySelector('input[type="password"]');
            const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                               Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                   btn.textContent.includes('Sign'));
            
            // Get detailed validation info
            const result = {
                formValid: form ? form.checkValidity() : null,
                emailValid: emailInput ? emailInput.checkValidity() : null,
                emailValidationMessage: emailInput ? emailInput.validationMessage : null,
                passwordValid: passwordInput ? passwordInput.checkValidity() : null,
                passwordValidationMessage: passwordInput ? passwordInput.validationMessage : null,
                buttonDisabled: submitButton ? submitButton.disabled : null,
                buttonClasses: submitButton ? submitButton.className : null
            };
            
            // Try to find any validation error messages
            const errorElements = Array.from(iframeDoc.querySelectorAll('.error, .invalid, [class*="error"], [class*="invalid"]'));
            result.errorMessages = errorElements.map(el => ({
                text: el.textContent.trim(),
                class: el.className
            })).filter(e => e.text);
            
            return result;
        }
    """)
    
    print("\nValidation State:")
    print(f"  Form valid: {validation_check['formValid']}")
    print(f"  Email valid: {validation_check['emailValid']}")
    print(f"  Email validation message: {validation_check['emailValidationMessage']}")
    print(f"  Password valid: {validation_check['passwordValid']}")
    print(f"  Password validation message: {validation_check['passwordValidationMessage']}")
    print(f"  Button disabled: {validation_check['buttonDisabled']}")
    print(f"  Button classes: {validation_check['buttonClasses']}")
    
    if validation_check['errorMessages']:
        print("\nError messages found:")
        for error in validation_check['errorMessages']:
            print(f"  - {error['text']} (class: {error['class']})")
    
    # Check console logs for any validation errors
    console_logs = await client.get_console_logs(limit=20)
    print("\nRecent console logs:")
    for log in console_logs["logs"][-10:]:
        if log["type"] in ["error", "warning"]:
            print(f"  [{log['type']}] {log['text']}")
    
    # If button is still disabled, try clicking anyway
    if validation_check['buttonDisabled']:
        print("\n⚠️ Button is disabled. Checking if we can force enable...")
        
        force_result = await client.evaluate("""
            () => {
                const loginIframe = Array.from(document.querySelectorAll('iframe'))
                    .find(iframe => iframe.src.includes('user_login') && iframe.offsetParent !== null);
                
                const iframeDoc = loginIframe.contentDocument;
                const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                                   Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                       btn.textContent.includes('Sign'));
                
                if (submitButton) {
                    // Check what's keeping it disabled
                    const form = iframeDoc.querySelector('form');
                    const inputs = form ? form.querySelectorAll('input') : [];
                    const inputStates = [];
                    
                    inputs.forEach(input => {
                        inputStates.push({
                            name: input.name || input.type,
                            value: input.value,
                            valid: input.checkValidity(),
                            required: input.required,
                            type: input.type
                        });
                    });
                    
                    return {
                        buttonFound: true,
                        inputCount: inputs.length,
                        inputStates: inputStates
                    };
                }
                
                return { buttonFound: false };
            }
        """)
        
        print("\nForm input states:")
        if force_result['buttonFound'] and force_result['inputStates']:
            for input in force_result['inputStates']:
                print(f"  {input['name']}: value='{input['value']}', valid={input['valid']}, required={input['required']}")

if __name__ == "__main__":
    asyncio.run(debug_form_validation())