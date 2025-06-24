"""
Test script to demonstrate the persistent browser server functionality
This shows how Claude can maintain browser sessions between executions
"""

import asyncio
import sys
from browser_client import BrowserClient
import json
from datetime import datetime


async def test_create_session():
    """Test 1: Create a new browser session and navigate to a page"""
    print("=" * 60)
    print("TEST 1: Creating new browser session")
    print("=" * 60)
    
    async with BrowserClient() as client:
        # Check server health first
        health = await client.health_check()
        print(f"Server health: {json.dumps(health, indent=2)}")
        
        # Create a new session
        await client.create_session(
            browser_type="chromium",
            headless=True,  # Set to False to see the browser
            viewport={"width": 1280, "height": 720}
        )
        
        print(f"Created session: {client.session_id}")
        
        # Navigate to a test page
        page = await client.new_page("https://example.com")
        print(f"Created page: {list(client.pages.keys())[0]}")
        
        # Take a screenshot
        screenshot = await page.screenshot("test_screenshot_1.png")
        print(f"Screenshot saved: {screenshot}")
        
        # Get page info
        title = await page.title()
        url = await page.url()
        print(f"Page title: {title}")
        print(f"Page URL: {url}")
        
        # Evaluate some JavaScript
        page_info = await page.evaluate("""
            () => ({
                title: document.title,
                url: window.location.href,
                links: document.querySelectorAll('a').length,
                timestamp: new Date().toISOString()
            })
        """)
        print(f"Page info from JS: {json.dumps(page_info, indent=2)}")
        
        # Save session info for next test
        with open("session_info.json", "w") as f:
            json.dump({
                "session_id": client.session_id,
                "page_id": list(client.pages.keys())[0],
                "created_at": datetime.now().isoformat()
            }, f, indent=2)
        
        print("\nSession info saved to session_info.json")
        print("Run with --continue to continue this session")


async def test_continue_session():
    """Test 2: Continue an existing session"""
    print("=" * 60)
    print("TEST 2: Continuing existing browser session")
    print("=" * 60)
    
    # Load session info
    try:
        with open("session_info.json", "r") as f:
            session_info = json.load(f)
    except FileNotFoundError:
        print("No session info found. Run without --continue first.")
        return
    
    print(f"Loaded session info: {json.dumps(session_info, indent=2)}")
    
    async with BrowserClient() as client:
        # Reconnect to existing session
        try:
            await client.connect_session(session_info["session_id"])
            print(f"Successfully connected to session: {session_info['session_id']}")
        except Exception as e:
            print(f"Failed to connect to session: {e}")
            print("The session may have expired. Run without --continue to create a new one.")
            return
        
        # Get the existing page
        page = await client.get_page(session_info["page_id"])
        print(f"Retrieved page: {session_info['page_id']}")
        
        # Verify we're on the same page
        current_url = await page.url()
        print(f"Current URL: {current_url}")
        
        # Navigate to a different page
        print("\nNavigating to a new page...")
        await page.goto("https://www.wikipedia.org")
        await page.wait_for_load_state("networkidle")
        
        # Interact with the page
        print("Interacting with Wikipedia...")
        
        # Take a screenshot
        screenshot = await page.screenshot("test_screenshot_2.png", full_page=False)
        print(f"Screenshot saved: {screenshot}")
        
        # Search for something
        await page.fill("input[name='search']", "Artificial Intelligence")
        await page.press("input[name='search']", "Enter")
        
        # Wait for navigation
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass  # Sometimes Wikipedia search is quick
        
        # Take another screenshot
        screenshot = await page.screenshot("test_screenshot_3.png")
        print(f"Search results screenshot: {screenshot}")
        
        # Get the new page info
        new_title = await page.title()
        new_url = await page.url()
        print(f"\nNew page title: {new_title}")
        print(f"New page URL: {new_url}")
        
        # List all sessions to show ours is still active
        print("\nAll active sessions:")
        sessions = await client.list_sessions()
        for session in sessions:
            print(f"  - {session['session_id']} ({session['browser_type']}, {session['pages']} pages)")


async def test_multiple_pages():
    """Test 3: Work with multiple pages in a session"""
    print("=" * 60)
    print("TEST 3: Multiple pages in one session")
    print("=" * 60)
    
    async with BrowserClient() as client:
        await client.create_session(headless=True)
        
        print(f"Created session: {client.session_id}")
        
        # Open multiple pages
        pages_info = []
        urls = [
            "https://example.com",
            "https://www.wikipedia.org",
            "https://www.python.org"
        ]
        
        for i, url in enumerate(urls):
            print(f"\nOpening page {i+1}: {url}")
            page = await client.new_page(url)
            await page.wait_for_load_state("domcontentloaded")
            
            title = await page.title()
            screenshot = await page.screenshot(f"test_multi_page_{i+1}.png")
            
            pages_info.append({
                "url": url,
                "title": title,
                "page_id": list(client.pages.keys())[-1],
                "screenshot": screenshot["path"]
            })
            
            print(f"  Title: {title}")
            print(f"  Screenshot: {screenshot['path']}")
        
        # List all pages
        print("\nAll pages in session:")
        all_pages = await client.list_pages()
        for page_info in all_pages:
            print(f"  - {page_info['page_id']}: {page_info['title']} ({page_info['url']})")
        
        # Work with a specific page
        python_page = await client.get_page(pages_info[2]["page_id"])
        print(f"\nWorking with Python.org page...")
        
        # Click on documentation link
        try:
            await python_page.click("a[href*='docs']")
            await python_page.wait_for_navigation(timeout=5000)
            new_url = await python_page.url()
            print(f"Navigated to: {new_url}")
        except:
            print("Could not find docs link")


async def test_cleanup():
    """Test 4: Clean up sessions"""
    print("=" * 60)
    print("TEST 4: Cleaning up sessions")
    print("=" * 60)
    
    async with BrowserClient() as client:
        # List all sessions
        sessions = await client.list_sessions()
        print(f"Found {len(sessions)} active sessions")
        
        if sessions:
            print("\nActive sessions:")
            for session in sessions:
                print(f"  - {session['session_id']} (created: {session['created_at']})")
            
            # Clean up old session from session_info.json if it exists
            try:
                with open("session_info.json", "r") as f:
                    old_session = json.load(f)
                
                if any(s['session_id'] == old_session['session_id'] for s in sessions):
                    await client.connect_session(old_session['session_id'])
                    await client.close_session()
                    print(f"\nClosed session: {old_session['session_id']}")
            except:
                pass
        else:
            print("No active sessions to clean up")


async def main():
    """Run the appropriate test based on command line arguments"""
    if len(sys.argv) > 1 and sys.argv[1] == "--continue":
        await test_continue_session()
    elif len(sys.argv) > 1 and sys.argv[1] == "--multiple":
        await test_multiple_pages()
    elif len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        await test_cleanup()
    else:
        await test_create_session()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    print("Persistent Browser Server Test Script")
    print("Usage:")
    print("  python test_browser_server.py          # Create new session")
    print("  python test_browser_server.py --continue   # Continue existing session")
    print("  python test_browser_server.py --multiple   # Test multiple pages")
    print("  python test_browser_server.py --cleanup    # Clean up sessions")
    print()
    
    asyncio.run(main())