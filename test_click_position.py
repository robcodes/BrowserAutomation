#!/usr/bin/env python3
"""Test clicking at specific position using existing session"""
import asyncio
import sys
sys.path.append('/home/ubuntu/browser_automation')
from clients.browser_client_crosshair import CrosshairBrowserClient

async def test_position_click():
    # Connect to existing session
    client = CrosshairBrowserClient()
    await client.connect_session("ee91b013")
    client.page_id = "6029627f"
    
    print("Connected to session ee91b013")
    
    # Take screenshot before click
    await client.screenshot("before_click.png")
    print("Screenshot saved: before_click.png")
    
    # Get current URL
    url_before = await client.evaluate("window.location.href")
    print(f"URL before click: {url_before}")
    
    # Try method 1: Using mouse.click directly
    print("\nMethod 1: Using page.mouse.click(795, 60)")
    result1 = await client.execute_raw_command({
        "method": "evaluate",
        "params": {"expression": "page.mouse.click(795, 60)"}
    })
    print(f"Result: {result1}")
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Check URL after
    url_after1 = await client.evaluate("window.location.href")
    print(f"URL after method 1: {url_after1}")
    
    # Take screenshot after
    await client.screenshot("after_click_method1.png")
    print("Screenshot saved: after_click_method1.png")
    
    # Try method 2: Direct page evaluation with click
    print("\nMethod 2: Using direct evaluation")
    await client.evaluate("""
        document.elementFromPoint(795, 60).click();
    """)
    
    await asyncio.sleep(2)
    
    # Check URL after
    url_after2 = await client.evaluate("window.location.href")
    print(f"URL after method 2: {url_after2}")
    
    # Take screenshot
    await client.screenshot("after_click_method2.png")
    print("Screenshot saved: after_click_method2.png")
    
    # Try method 3: Using click_at with crosshair
    print("\nMethod 3: Using click_at with crosshair")
    await client.click_at(795, 60, label="test_click")
    
    await asyncio.sleep(2)
    
    # Check URL after
    url_after3 = await client.evaluate("window.location.href")
    print(f"URL after method 3: {url_after3}")
    
    # Take final screenshot
    await client.screenshot("after_click_method3.png")
    print("Screenshot saved: after_click_method3.png")
    
    # Check what element is at that position
    print("\nChecking what element is at (795, 60):")
    element_info = await client.evaluate("""
        (() => {
            const elem = document.elementFromPoint(795, 60);
            if (!elem) return "No element found";
            return {
                tagName: elem.tagName,
                className: elem.className,
                id: elem.id,
                text: elem.textContent?.substring(0, 50),
                href: elem.href,
                isClickable: elem.onclick !== null || elem.tagName === 'A' || elem.tagName === 'BUTTON'
            };
        })()
    """)
    print(f"Element at position: {element_info}")

if __name__ == "__main__":
    asyncio.run(test_position_click())