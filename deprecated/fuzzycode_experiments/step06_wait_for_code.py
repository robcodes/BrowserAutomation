#!/usr/bin/env python3
"""
Step 6b: Wait for code generation
- Waits for the code to appear
- Takes screenshot of generated code
"""
from common import *

async def wait_for_code():
    """Wait for code generation to complete"""
    print_step_header(6, "Wait for Code Generation")
    
    # Load session from previous step
    session_info = await load_session_info()
    if not session_info:
        print("❌ No session info found!")
        return False
    
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        print("\n1. Waiting for code generation...")
        
        # Multiple wait cycles with screenshots
        wait_times = [3000, 3000, 3000, 3000]  # Total 12 seconds
        for i, wait_time in enumerate(wait_times):
            await wait_and_check(client, wait_time, f"Wait cycle {i+1}/{len(wait_times)}")
            
            # Take progress screenshot
            await take_screenshot_and_check(
                client,
                f"step06_progress_{i+1}.png",
                f"Code generation progress - {(i+1)*3} seconds"
            )
            
            # Check if code has appeared
            code_check = await client.evaluate("""
                (() => {
                    // Look for any code elements
                    const codeBlocks = document.querySelectorAll('pre, code, .code, .output');
                    const hasCode = codeBlocks.length > 0;
                    
                    // Check textarea for any output
                    const textarea = document.querySelector('textarea');
                    const textContent = textarea ? textarea.value : '';
                    
                    // Look for generated content area
                    const outputDivs = Array.from(document.querySelectorAll('div'))
                        .filter(div => div.textContent.includes('def') || 
                                      div.textContent.includes('function') ||
                                      div.textContent.includes('prime'));
                    
                    return {
                        hasCodeBlocks: hasCode,
                        codeBlockCount: codeBlocks.length,
                        textareaContent: textContent.substring(0, 100),
                        hasOutputDivs: outputDivs.length > 0,
                        pageText: document.body.innerText.substring(0, 200)
                    };
                })()
            """)
            
            print(f"\n   Code check {i+1}:")
            print(f"   - Code blocks found: {code_check['hasCodeBlocks']} ({code_check['codeBlockCount']} blocks)")
            print(f"   - Output divs with code: {code_check['hasOutputDivs']}")
            print(f"   - Textarea content: {code_check['textareaContent']}")
            
            if code_check['hasCodeBlocks'] or code_check['hasOutputDivs']:
                print("\n   ✅ Code generation detected!")
                break
        
        print("\n2. Taking final screenshot...")
        await take_screenshot_and_check(
            client,
            "step06_final_code.png",
            "Final state - should show generated code"
        )
        
        print_step_result(True, "Code generation wait completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step06_wait_error.png", "Error state")
        return False

if __name__ == "__main__":
    result = asyncio.run(wait_for_code())
    import sys
    sys.exit(0 if result else 1)