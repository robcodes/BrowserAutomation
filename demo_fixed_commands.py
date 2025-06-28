#!/usr/bin/env python3
"""
Demo script showing how to use the fixed Playwright command execution
"""
import asyncio
from clients.browser_client_crosshair import CrosshairBrowserClient

async def main():
    """Demonstrate the fixed command execution"""
    client = CrosshairBrowserClient()
    
    print("Starting browser session...")
    session_id = await client.create_session(headless=False)
    print(f"Session: {session_id}")
    
    print("Creating page...")
    page_id = await client.new_page()
    print(f"Page: {page_id}")
    
    print("\nNavigating to example.com...")
    await client.goto("https://example.com")
    
    print("\nTaking screenshot to see the page...")
    screenshot_path = await client.screenshot("screenshots/example_page.png")
    print(f"Screenshot saved: {screenshot_path}")
    
    print("\nExecuting Playwright commands via the /command endpoint...")
    
    # Test 1: Click at specific position (this was failing before)
    print("\n1. Testing position-based click...")
    result = await client.execute_command(
        session_id, 
        page_id,
        "await page.click({position: {x: 400, y: 200}})"
    )
    print(f"   Result: {result}")
    
    # Test 2: Click without await (should also work now)
    print("\n2. Testing click without await...")
    result = await client.execute_command(
        session_id,
        page_id, 
        "page.click({position: {x: 400, y: 300}})"
    )
    print(f"   Result: {result}")
    
    # Test 3: Type text
    print("\n3. Testing typing text...")
    result = await client.execute_command(
        session_id,
        page_id,
        "page.type('Hello from fixed command execution!')"
    )
    print(f"   Result: {result}")
    
    # Test 4: Take screenshot via command
    print("\n4. Testing screenshot command...")
    result = await client.execute_command(
        session_id,
        page_id,
        "page.screenshot()"
    )
    if result['status'] == 'success':
        print(f"   Screenshot taken, data length: {len(result.get('screenshot', ''))}")
    
    # Test 5: Wait command
    print("\n5. Testing wait command...")
    result = await client.execute_command(
        session_id,
        page_id,
        "page.wait_for_timeout(2000)"
    )
    print(f"   Result: {result}")
    
    print("\nDemo completed! Check the browser window.")
    print("\nPress Enter to close the browser...")
    input()
    
    # Close the session manually via HTTP request
    import httpx
    async with httpx.AsyncClient() as http_client:
        response = await http_client.delete(f"{client.server_url}/sessions/{session_id}")
        if response.status_code == 200:
            print("Session closed.")
        else:
            print(f"Failed to close session: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(main())