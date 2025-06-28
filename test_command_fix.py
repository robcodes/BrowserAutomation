#!/usr/bin/env python3
"""
Test script to verify the Playwright command execution fix
"""
import asyncio
import aiohttp
import json

async def test_command_execution():
    """Test the fixed command execution endpoint"""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # 1. Create a browser session
        print("1. Creating browser session...")
        async with session.post(f"{base_url}/sessions", 
                              json={"browser_type": "chromium", "headless": False}) as resp:
            session_data = await resp.json()
            session_id = session_data["session_id"]
            print(f"   ✓ Session created: {session_id}")
        
        # 2. Create a page
        print("\n2. Creating page...")
        async with session.post(f"{base_url}/sessions/{session_id}/pages") as resp:
            page_data = await resp.json()
            page_id = page_data["page_id"]
            print(f"   ✓ Page created: {page_id}")
        
        # 3. Test various Playwright commands
        print("\n3. Testing Playwright commands...")
        
        test_commands = [
            # Navigation
            ("page.goto('https://example.com')", "Navigate to example.com"),
            
            # Click with position (this was failing before)
            ("await page.click({position: {x: 100, y: 100}})", "Click at position"),
            ("page.click({position: {x: 200, y: 200}})", "Click without await"),
            
            # Type text
            ("page.type('Hello World')", "Type text"),
            
            # Screenshot
            ("page.screenshot()", "Take screenshot"),
            
            # Wait
            ("page.wait_for_timeout(1000)", "Wait 1 second"),
            
            # Press key
            ("page.press('Tab')", "Press Tab key"),
        ]
        
        for command, description in test_commands:
            print(f"\n   Testing: {description}")
            print(f"   Command: {command}")
            
            async with session.post(f"{base_url}/command",
                                  json={
                                      "session_id": session_id,
                                      "page_id": page_id,
                                      "command": command
                                  }) as resp:
                result = await resp.json()
                
                if result["status"] == "success":
                    print(f"   ✓ Success: {result.get('message', 'Command executed')}")
                    if "screenshot" in result:
                        print(f"     Screenshot data length: {len(result['screenshot'])}")
                else:
                    print(f"   ✗ Error: {result.get('error', 'Unknown error')}")
                    if "traceback" in result:
                        print(f"     Traceback:\n{result['traceback']}")
        
        # 4. Test complex commands
        print("\n4. Testing complex commands...")
        
        complex_commands = [
            ("page.fill('#search', 'test query')", "Fill form field"),
            ("page.select_option('#dropdown', 'option1')", "Select dropdown option"),
            ("page.reload()", "Reload page"),
        ]
        
        for command, description in complex_commands:
            print(f"\n   Testing: {description}")
            print(f"   Command: {command}")
            
            async with session.post(f"{base_url}/command",
                                  json={
                                      "session_id": session_id,
                                      "page_id": page_id,
                                      "command": command
                                  }) as resp:
                result = await resp.json()
                
                if result["status"] == "success":
                    print(f"   ✓ Success: {result.get('message', 'Command executed')}")
                else:
                    print(f"   ✗ Error: {result.get('error', 'Unknown error')}")
        
        # 5. Cleanup
        print("\n5. Cleaning up...")
        async with session.delete(f"{base_url}/sessions/{session_id}") as resp:
            if resp.status == 200:
                print("   ✓ Session closed")
            else:
                print("   ✗ Failed to close session")

if __name__ == "__main__":
    print("Testing Playwright Command Execution Fix")
    print("=" * 40)
    print("\nMake sure the browser server is running at http://localhost:8000")
    print("Start it with: python3 server/browser_server_enhanced.py\n")
    
    asyncio.run(test_command_execution())