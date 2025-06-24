#!/usr/bin/env python3
"""
Wait for login to complete
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def wait_for_login():
    """Wait for login to complete"""
    print("=== Waiting for Login to Complete ===\n")
    
    # Load session
    with open("fuzzycode_login_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Wait and check periodically
    max_attempts = 10
    for attempt in range(max_attempts):
        print(f"\n→ Check #{attempt + 1}...")
        
        await client.wait(2000)
        
        # Check if login iframe is still visible
        status = await client.evaluate("""
            () => {
                // Check login iframe
                const loginIframe = Array.from(document.querySelectorAll('iframe'))
                    .find(iframe => iframe.src.includes('user_login'));
                
                const loginVisible = loginIframe ? 
                    (loginIframe.offsetParent !== null && 
                     loginIframe.getBoundingClientRect().width > 100) : false;
                
                // Check for any success indicators
                const pageText = document.body.textContent;
                const hasUserEmail = pageText.includes('robert.norbeau');
                
                // Check if we can find the main textarea for code input
                const mainTextarea = document.querySelector('textarea#userInput') ||
                                   document.querySelector('textarea[placeholder*="Enter your request"]');
                
                return {
                    loginIframeVisible: loginVisible,
                    hasUserEmail: hasUserEmail,
                    mainTextareaFound: mainTextarea !== null,
                    url: window.location.href
                };
            }
        """)
        
        print(f"  Login iframe visible: {status['loginIframeVisible']}")
        print(f"  User email in page: {status['hasUserEmail']}")
        print(f"  Main textarea found: {status['mainTextareaFound']}")
        
        if not status['loginIframeVisible']:
            print("\n✅ Login completed! Login iframe is no longer visible.")
            
            # Take screenshot
            await client.screenshot("fuzzycode_logged_in.png")
            
            # Now try to generate code
            print("\n→ Attempting to generate code...")
            
            prompt_text = "Create a Python function that generates the Fibonacci sequence up to n terms"
            
            # Fill the textarea
            fill_result = await client.evaluate(f"""
                () => {{
                    const textarea = document.querySelector('textarea');
                    if (textarea) {{
                        textarea.focus();
                        textarea.value = `{prompt_text}`;
                        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                }}
            """)
            
            print(f"  Prompt filled: {fill_result}")
            
            if fill_result:
                await client.wait(1000)
                
                # Click generate button
                generate_result = await client.evaluate("""
                    () => {
                        const button = Array.from(document.querySelectorAll('button')).find(btn =>
                            btn.textContent.includes('Fuzzy Code It') || 
                            btn.textContent.includes('Generate') ||
                            btn.id === 'processTextButton'
                        );
                        
                        if (button && !button.disabled) {
                            button.click();
                            return { success: true, text: button.textContent };
                        }
                        return { success: false, disabled: button ? button.disabled : null };
                    }
                """)
                
                print(f"  Generate button: {generate_result}")
                
                if generate_result['success']:
                    print("\n⏳ Waiting for code generation...")
                    await client.wait(5000)
                    
                    await client.screenshot("fuzzycode_code_generated.png")
                    
                    # Check network for API calls
                    api_logs = await client.get_network_logs(limit=10)
                    api_calls = [log for log in api_logs["logs"] if 'prompt_to_code' in log['url']]
                    
                    if api_calls:
                        print(f"\n📡 API calls made:")
                        for call in api_calls:
                            status = f" -> {call.get('status', '?')}" if call['type'] == 'response' else ""
                            print(f"  {call['type']}: {call['url'][-50:]}{status}")
                    
                    print("\n✅ Process completed! Check the screenshots.")
                else:
                    print(f"\n⚠️ Could not click generate button: {generate_result}")
            
            break
        
        # Check for errors in iframe if still visible
        if status['loginIframeVisible']:
            iframe_check = await client.evaluate("""
                () => {
                    const loginIframe = Array.from(document.querySelectorAll('iframe'))
                        .find(iframe => iframe.src.includes('user_login'));
                    
                    if (!loginIframe) return null;
                    
                    try {
                        const iframeDoc = loginIframe.contentDocument;
                        
                        // Check button state
                        const submitBtn = iframeDoc.querySelector('button[type="submit"]');
                        
                        // Look for any visible text that might be an error
                        const visibleTexts = Array.from(iframeDoc.querySelectorAll('div, span, p'))
                            .map(el => el.textContent.trim())
                            .filter(text => text.length > 5 && text.length < 200);
                        
                        return {
                            buttonDisabled: submitBtn ? submitBtn.disabled : null,
                            visibleTexts: visibleTexts.slice(-5)  // Last 5 texts
                        };
                    } catch (e) {
                        return null;
                    }
                }
            """)
            
            if iframe_check and iframe_check['visibleTexts']:
                print(f"  Button disabled: {iframe_check['buttonDisabled']}")
                for text in iframe_check['visibleTexts']:
                    if 'error' in text.lower() or 'invalid' in text.lower():
                        print(f"  ⚠️ Possible error: {text}")
    
    if attempt == max_attempts - 1:
        print("\n⚠️ Login did not complete after maximum attempts")

if __name__ == "__main__":
    asyncio.run(wait_for_login())