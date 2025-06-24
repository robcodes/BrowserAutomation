#!/usr/bin/env python3
"""Check iframe content for welcome message"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient
from scripts.fuzzycode_steps.common import load_session_info

async def main():
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    # Check iframe content
    iframe_info = await client.evaluate("""
        (() => {
            const iframe = document.querySelector('iframe');
            if (!iframe) return { hasIframe: false };
            
            try {
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const iframeText = iframeDoc.body.textContent;
                
                return {
                    hasIframe: true,
                    accessible: true,
                    hasWelcome: iframeText.includes('Welcome'),
                    hasEmail: iframeText.includes('robert.norbeau+test2@gmail.com'),
                    textPreview: iframeText.slice(0, 200).replace(/\\s+/g, ' ').trim(),
                    src: iframe.src
                };
            } catch (e) {
                return {
                    hasIframe: true,
                    accessible: false,
                    error: e.message,
                    src: iframe.src
                };
            }
        })()
    """)
    
    print("Iframe check:")
    for key, value in iframe_info.items():
        print(f"  {key}: {value}")
    
    # Also check visible text
    visible_text = await client.evaluate("document.body.innerText.slice(0, 500)")
    print(f"\nVisible text on page:\n{visible_text}")

if __name__ == "__main__":
    asyncio.run(main())