#!/usr/bin/env python3
"""
Check for login error messages
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def check_login_error():
    """Check for login error messages"""
    print("=== Checking for Login Errors ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Check for error messages in the login iframe
    error_check = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(iframe => iframe.src.includes('user_login'));
            
            if (!loginIframe) return { error: 'Login iframe not found' };
            
            try {
                const iframeDoc = loginIframe.contentDocument || loginIframe.contentWindow.document;
                
                // Check current form values
                const emailInput = iframeDoc.querySelector('input[type="email"]') || 
                                 iframeDoc.querySelector('input[type="text"]');
                const passwordInput = iframeDoc.querySelector('input[type="password"]');
                
                const formValues = {
                    email: emailInput ? emailInput.value : 'not found',
                    password: passwordInput ? (passwordInput.value ? 'filled' : 'empty') : 'not found'
                };
                
                // Look for error messages
                const errorSelectors = [
                    '.error', '.alert', '.message', '[class*="error"]', '[class*="alert"]',
                    'span', 'div', 'p'
                ];
                
                const errorMessages = [];
                errorSelectors.forEach(selector => {
                    iframeDoc.querySelectorAll(selector).forEach(el => {
                        const text = el.textContent.trim().toLowerCase();
                        if (text && (text.includes('error') || text.includes('invalid') || 
                                    text.includes('incorrect') || text.includes('failed') ||
                                    text.includes('wrong') || text.includes('try again'))) {
                            errorMessages.push({
                                selector: selector,
                                text: el.textContent.trim()
                            });
                        }
                    });
                });
                
                // Check if form is in loading state
                const submitButton = iframeDoc.querySelector('button[type="submit"]') ||
                                   Array.from(iframeDoc.querySelectorAll('button')).find(btn =>
                                       /sign\s*in|login/i.test(btn.textContent));
                
                const buttonState = {
                    exists: submitButton !== null,
                    disabled: submitButton ? submitButton.disabled : null,
                    text: submitButton ? submitButton.textContent : null
                };
                
                // Check for any loading indicators
                const hasLoader = iframeDoc.querySelector('.loader, .loading, .spinner, [class*="load"]') !== null;
                
                return {
                    success: true,
                    formValues: formValues,
                    errorMessages: errorMessages,
                    buttonState: buttonState,
                    hasLoader: hasLoader,
                    iframeUrl: loginIframe.src
                };
            } catch (e) {
                return {
                    success: false,
                    error: e.toString()
                };
            }
        }
    """)
    
    print("Login Form Status:")
    print(f"  Email: {error_check['formValues']['email']}")
    print(f"  Password: {error_check['formValues']['password']}")
    
    print(f"\nButton State:")
    print(f"  Exists: {error_check['buttonState']['exists']}")
    print(f"  Disabled: {error_check['buttonState']['disabled']}")
    print(f"  Text: {error_check['buttonState']['text']}")
    
    print(f"\nLoading indicator present: {error_check['hasLoader']}")
    
    if error_check['errorMessages']:
        print(f"\n⚠️ Error messages found ({len(error_check['errorMessages'])}):")
        for msg in error_check['errorMessages']:
            print(f"  - {msg['text']}")
    else:
        print("\n✅ No error messages found")
    
    # Check network activity for login API calls
    print("\n→ Checking recent network activity...")
    
    network_logs = await client.get_network_logs(limit=20)
    login_requests = [
        log for log in network_logs["logs"] 
        if 'login' in log['url'].lower() or 'auth' in log['url'].lower()
    ]
    
    if login_requests:
        print(f"\nFound {len(login_requests)} login-related network requests:")
        for req in login_requests[-5:]:  # Last 5
            status = f" -> {req.get('status', '?')}" if req['type'] == 'response' else ""
            print(f"  {req['type']}: {req['method']} {req['url'][-50:]}{status}")
            if req.get('failure'):
                print(f"    FAILED: {req['failure']}")
    
    # If no errors, maybe we need to close the modal?
    if not error_check['errorMessages']:
        print("\n→ Attempting to close login modal...")
        
        close_result = await client.evaluate("""
            () => {
                // Look for close button
                const closeButtons = document.querySelectorAll('[aria-label="Close"], .close, .modal-close, button[title="Close"]');
                for (let btn of closeButtons) {
                    if (btn.offsetParent !== null) {
                        btn.click();
                        return { closed: true, element: btn.tagName + '.' + btn.className };
                    }
                }
                
                // Try clicking outside the modal
                const backdrop = document.querySelector('.modal-backdrop, .overlay');
                if (backdrop) {
                    backdrop.click();
                    return { closed: true, element: 'backdrop' };
                }
                
                return { closed: false };
            }
        """)
        
        print(f"Close attempt: {close_result}")

if __name__ == "__main__":
    asyncio.run(check_login_error())