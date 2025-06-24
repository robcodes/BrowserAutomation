#!/usr/bin/env python3
"""
Verify login succeeded
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def verify_login():
    """Verify login was successful"""
    print("=== Verifying Login Success ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Wait and take screenshot
    await client.wait(2000)
    await client.screenshot("fuzzy_explore_20_login_status.png")
    print("✓ Screenshot: fuzzy_explore_20_login_status.png")
    
    # Check state
    state = await client.evaluate("""
        () => {
            const loginIframe = Array.from(document.querySelectorAll('iframe'))
                .find(f => f.src.includes('user_login'));
            return {
                loginModalVisible: loginIframe ? loginIframe.offsetParent !== null : false,
                pageHasEmail: document.body.textContent.includes('robert.norbeau')
            };
        }
    """)
    
    print(f"\nLogin modal visible: {state['loginModalVisible']}")
    print(f"User email in page: {state['pageHasEmail']}")
    
    if state['loginModalVisible']:
        # Check if we got a welcome message
        welcome_check = await client.evaluate("""
            () => {
                const iframe = Array.from(document.querySelectorAll('iframe'))[1];
                try {
                    const iframeDoc = iframe.contentDocument;
                    const text = iframeDoc.body.textContent;
                    return {
                        hasWelcome: text.includes('Welcome'),
                        content: text.substring(0, 200)
                    };
                } catch (e) {
                    return { error: e.message };
                }
            }
        """)
        print(f"\nIframe content check: {welcome_check}")

if __name__ == "__main__":
    asyncio.run(verify_login())