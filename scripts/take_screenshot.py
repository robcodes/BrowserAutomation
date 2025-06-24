#!/usr/bin/env python3
"""Take a screenshot of current state"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.fuzzycode_steps.common import *

async def main():
    # Load session
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    # Take screenshot
    screenshot_name = sys.argv[1] if len(sys.argv) > 1 else "current_state.png"
    await client.screenshot(screenshot_name)
    print(f"Screenshot saved: {screenshot_name}")
    
    # Check state
    state = await client.evaluate("""
        (() => {
            const popup = document.querySelector('.popup-overlay');
            const welcome = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
            const textarea = document.querySelector('textarea#prompt');
            const genButton = document.querySelector('button.btn-primary');
            const codeOutput = document.querySelector('.hljs');
            
            return {
                popupVisible: popup && popup.style.display !== 'none',
                welcomeVisible: welcome,
                textareaValue: textarea ? textarea.value : '',
                hasGenerateButton: genButton !== null,
                hasCodeOutput: codeOutput !== null,
                codePreview: codeOutput ? codeOutput.textContent.substring(0, 100) : ''
            };
        })()
    """)
    
    print("\nCurrent state:")
    print(f"- Popup visible: {state['popupVisible']}")
    print(f"- Welcome visible: {state['welcomeVisible']}")
    print(f"- Textarea value: {state['textareaValue']}")
    print(f"- Has generate button: {state['hasGenerateButton']}")
    print(f"- Has code output: {state['hasCodeOutput']}")
    if state['codePreview']:
        print(f"- Code preview: {state['codePreview']}...")

if __name__ == "__main__":
    asyncio.run(main())