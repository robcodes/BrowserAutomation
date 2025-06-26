#!/usr/bin/env python3
"""
Helper to find the login iframe robustly
"""

def get_find_login_iframe_js():
    """Returns JavaScript to find the login iframe"""
    return """
        (() => {
            const iframes = Array.from(document.querySelectorAll('iframe'));
            
            // Find iframe that contains login form
            for (let i = 0; i < iframes.length; i++) {
                const iframe = iframes[i];
                try {
                    const doc = iframe.contentDocument;
                    if (!doc) continue;
                    
                    // Check if this iframe has login-related content
                    const hasLoginForm = doc.querySelector('form') !== null;
                    const hasPasswordInput = doc.querySelector('input[type="password"]') !== null;
                    const hasSignInText = doc.body && doc.body.textContent.includes('Sign In');
                    const hasUserLoginSrc = iframe.src.includes('user_login');
                    
                    // If it looks like a login iframe, return info about it
                    if (hasLoginForm || hasPasswordInput || hasSignInText || hasUserLoginSrc) {
                        return {
                            found: true,
                            index: i,
                            src: iframe.src,
                            hasForm: hasLoginForm,
                            hasPasswordInput: hasPasswordInput,
                            hasSignInText: hasSignInText,
                            inputCount: doc.querySelectorAll('input').length,
                            formCount: doc.querySelectorAll('form').length
                        };
                    }
                } catch (e) {
                    // Cross-origin iframe, check by src
                    if (iframe.src.includes('login') || iframe.src.includes('auth')) {
                        return {
                            found: true,
                            index: i,
                            src: iframe.src,
                            crossOrigin: true
                        };
                    }
                }
            }
            
            return { found: false, iframeCount: iframes.length };
        })()
    """

def get_login_iframe_accessor_js(fill_username=None, fill_password=None):
    """Returns JavaScript to access and optionally fill the login iframe"""
    return f"""
        (() => {{
            // First find the login iframe
            const findResult = {get_find_login_iframe_js()};
            
            if (!findResult.found) {{
                return {{ success: false, reason: 'No login iframe found' }};
            }}
            
            const loginIframe = document.querySelectorAll('iframe')[findResult.index];
            const iframeDoc = loginIframe.contentDocument;
            
            if (!iframeDoc) {{
                return {{ success: false, reason: 'Cannot access iframe document' }};
            }}
            
            const result = {{
                success: true,
                iframeIndex: findResult.index,
                inputs: []
            }};
            
            // Get input information
            const inputs = iframeDoc.querySelectorAll('input');
            inputs.forEach((input, idx) => {{
                result.inputs.push({{
                    index: idx,
                    type: input.type,
                    placeholder: input.placeholder,
                    value: input.value ? '***' : 'empty'
                }});
            }});
            
            // Fill if requested
            if ({repr(fill_username)} && {repr(fill_password)}) {{
                if (inputs.length >= 2) {{
                    inputs[0].value = {repr(fill_username)};
                    inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[1].value = {repr(fill_password)};
                    inputs[1].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    result.filled = true;
                }}
            }}
            
            return result;
        }})()
    """