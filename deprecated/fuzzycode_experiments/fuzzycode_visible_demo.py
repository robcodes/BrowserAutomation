#!/usr/bin/env python3
"""
Demo script to run FuzzyCode automation in visible (non-headless) mode
You can watch the browser perform each action!
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clients.browser_client_enhanced import EnhancedBrowserClient

async def fuzzycode_visible_demo():
    """Run FuzzyCode automation with visible browser"""
    client = EnhancedBrowserClient()
    
    try:
        print("🌟 Starting VISIBLE browser session...")
        print("   You should see a browser window open!\n")
        
        # Create session with headless=False for visible browser
        session_id = await client.create_session(headless=False)
        print(f"✓ Session created: {session_id}")
        
        print("\n📍 Navigating to FuzzyCode...")
        page_id = await client.new_page("https://fuzzycode.dev")
        await client.wait(2000)
        
        print("\n👤 Clicking profile icon...")
        await client.evaluate("""
            (() => {
                const profileIcon = document.querySelector('.user-profile-icon');
                if (profileIcon) profileIcon.click();
                return profileIcon ? 'clicked' : 'not found';
            })()
        """)
        await client.wait(3000)  # Give modal time to load
        
        print("\n🔐 Checking for login iframe...")
        iframe_check = await client.evaluate("""
            (() => {
                const iframes = Array.from(document.querySelectorAll('iframe'));
                if (iframes.length > 1) {
                    try {
                        const loginIframe = iframes[1];
                        const iframeDoc = loginIframe.contentDocument;
                        const inputs = iframeDoc.querySelectorAll('input');
                        return { found: true, inputCount: inputs.length };
                    } catch (e) {
                        return { found: false, error: e.message };
                    }
                }
                return { found: false, iframeCount: iframes.length };
            })()
        """)
        print(f"   Iframe status: {iframe_check}")
        
        if iframe_check.get('found') and iframe_check.get('inputCount', 0) > 0:
            print("\n🔐 Filling login form...")
            await client.evaluate("""
                (() => {
                    const loginIframe = Array.from(document.querySelectorAll('iframe'))[1];
                    const iframeDoc = loginIframe.contentDocument;
                    const inputs = iframeDoc.querySelectorAll('input');
                    
                    // Fill credentials
                    inputs[0].value = 'robert.norbeau+test2@gmail.com';
                    inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                    
                    inputs[1].value = 'robert.norbeau+test2';
                    inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
                    
                    return 'Credentials filled';
                })()
            """)
        else:
            print("   ⚠️  Login iframe not ready, waiting...")
            await client.wait(2000)
        await client.wait(1000)
        
        print("\n🚀 Clicking Sign In...")
        if iframe_check.get('found'):
            await client.evaluate("""
                (() => {
                    const loginIframe = Array.from(document.querySelectorAll('iframe'))[1];
                    const iframeDoc = loginIframe.contentDocument;
                    const signInBtn = Array.from(iframeDoc.querySelectorAll('button'))
                        .find(btn => btn.textContent.includes('Sign'));
                    if (signInBtn) {
                        signInBtn.click();
                        return 'Sign In clicked';
                    }
                    return 'Sign In button not found';
                })()
            """)
        
        print("\n⏳ Waiting for login to complete...")
        await client.wait(3000)
        
        print("\n🔄 Reloading page to close modal...")
        await client.evaluate("window.location.reload()")
        await client.wait(3000)
        
        print("\n✍️  Entering a prompt...")
        await client.evaluate("""
            (() => {
                const textarea = document.querySelector('textarea');
                if (textarea) {
                    textarea.value = 'Write a Python function to generate the Fibonacci sequence';
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                }
            })()
        """)
        await client.wait(1000)
        
        print("\n🎯 Clicking 'Fuzzy Code It!' button...")
        await client.evaluate("""
            (() => {
                const generateBtn = Array.from(document.querySelectorAll('button'))
                    .find(btn => btn.textContent.includes('Fuzzy Code It'));
                if (generateBtn) generateBtn.click();
            })()
        """)
        
        print("\n⏳ Waiting for code generation...")
        await client.wait(5000)
        
        print("\n✅ Demo completed! Check the browser window.")
        print("   The browser will stay open for 10 seconds...")
        await client.wait(10000)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("FuzzyCode Visible Browser Demo")
    print("=" * 60)
    print("\nThis will open a real browser window that you can watch!")
    print("Make sure you have a display available.\n")
    
    asyncio.run(fuzzycode_visible_demo())