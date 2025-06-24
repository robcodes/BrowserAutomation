#!/usr/bin/env python3
"""
Check for generated code output on fuzzycode.dev
"""
import asyncio
import json
from browser_client_poc import PersistentBrowserClient

async def check_output():
    """Check if there's any generated code in the output area"""
    print("=== Checking for Generated Code ===\n")
    
    # Load session
    with open("fuzzycode_session.json", "r") as f:
        session_data = json.load(f)
    
    client = PersistentBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Wait a bit more for generation
    print("\n⏳ Waiting for any delayed generation...")
    await client.wait(3000)
    
    # Try to find and read any code output
    print("\n→ Looking for generated code...")
    
    # Try different selectors for code output
    output_selectors = [
        "pre",
        "code",
        ".output",
        ".code-output",
        ".result",
        "#output",
        "textarea:not(:first-of-type)",
        ".editor-output",
        ".code-editor",
        "[data-testid='output']"
    ]
    
    for selector in output_selectors:
        try:
            output_text = await client.evaluate(f"""
                document.querySelector('{selector}')?.textContent || 
                document.querySelector('{selector}')?.value || ''
            """)
            if output_text and output_text.strip():
                print(f"\n✓ Found output in {selector}:")
                print("=" * 50)
                print(output_text)
                print("=" * 50)
                break
        except:
            pass
    
    # Try to scroll down to see if there's more content
    print("\n→ Scrolling to check for hidden content...")
    await client.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await client.wait(1000)
    
    # Take screenshot after scrolling
    await client.screenshot("fuzzycode_7_after_scroll.png")
    
    # Check all text content on the page
    print("\n→ Checking all visible text content...")
    all_text = await client.evaluate("""
        Array.from(document.querySelectorAll('*')).map(el => {
            const text = el.textContent?.trim();
            if (text && text.length > 50 && text.includes('def') || text.includes('function')) {
                return text;
            }
        }).filter(Boolean).slice(0, 3)
    """)
    
    if all_text:
        print("\n✓ Found potential code content:")
        for i, text in enumerate(all_text):
            print(f"\n{i+1}. {text[:200]}...")
    
    print("\n✅ Output check complete!")

if __name__ == "__main__":
    asyncio.run(check_output())