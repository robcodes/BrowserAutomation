#!/usr/bin/env python3
"""
Client for the Persistent Browser Server
Allows Claude to maintain browser sessions across executions
"""
import httpx
import json
import asyncio
from typing import Optional, Dict, Any

class PersistentBrowserClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.session_id: Optional[str] = None
        self.current_page_id: Optional[str] = None
        
    async def create_session(self, browser_type: str = "chromium") -> str:
        """Create a new browser session"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/sessions",
                params={"browser_type": browser_type}
            )
            response.raise_for_status()
            data = response.json()
            self.session_id = data["session_id"]
            print(f"✓ Created session: {self.session_id}")
            return self.session_id
    
    async def connect_session(self, session_id: str):
        """Connect to an existing session"""
        self.session_id = session_id
        # Verify session exists
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.server_url}/sessions")
            sessions = response.json()["sessions"]
            if not any(s["session_id"] == session_id for s in sessions):
                raise ValueError(f"Session {session_id} not found")
        print(f"✓ Connected to session: {self.session_id}")
    
    async def new_page(self, url: Optional[str] = None) -> str:
        """Create a new page/tab"""
        if not self.session_id:
            raise ValueError("No active session. Call create_session() first")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/sessions/{self.session_id}/pages",
                params={"url": url} if url else {}
            )
            response.raise_for_status()
            data = response.json()
            self.current_page_id = data["page_id"]
            print(f"✓ Created page: {self.current_page_id}")
            return self.current_page_id
    
    async def set_page(self, page_id: str):
        """Set the current page to work with"""
        self.current_page_id = page_id
        print(f"✓ Working with page: {self.current_page_id}")
    
    async def _execute_command(self, action: str, params: Dict[str, Any] = {}) -> Dict:
        """Execute a command on the current page"""
        if not self.current_page_id:
            raise ValueError("No active page. Call new_page() first")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/pages/{self.current_page_id}/command",
                json={"action": action, "params": params}
            )
            response.raise_for_status()
            return response.json()
    
    # Playwright-like API methods
    async def goto(self, url: str) -> Dict:
        """Navigate to a URL"""
        print(f"→ Navigating to: {url}")
        return await self._execute_command("goto", {"url": url})
    
    async def click(self, selector: str) -> Dict:
        """Click an element"""
        print(f"→ Clicking: {selector}")
        return await self._execute_command("click", {"selector": selector})
    
    async def fill(self, selector: str, value: str) -> Dict:
        """Fill an input field"""
        print(f"→ Filling {selector} with: {value}")
        return await self._execute_command("fill", {"selector": selector, "value": value})
    
    async def screenshot(self, filename: Optional[str] = None) -> str:
        """Take a screenshot and return the path"""
        if not filename:
            filename = f"screenshot_{self.current_page_id}.png"
        print(f"→ Taking screenshot: {filename}")
        result = await self._execute_command("screenshot", {"filename": filename})
        if result["status"] == "success":
            return result["path"]
        raise Exception(f"Screenshot failed: {result.get('message')}")
    
    async def wait(self, timeout: int = 1000) -> Dict:
        """Wait for specified time in milliseconds"""
        print(f"→ Waiting {timeout}ms")
        return await self._execute_command("wait", {"timeout": timeout})
    
    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript in the page"""
        print(f"→ Evaluating script")
        result = await self._execute_command("evaluate", {"script": script})
        if result["status"] == "success":
            return result.get("result")
        raise Exception(f"Evaluation failed: {result.get('message')}")
    
    async def get_info(self) -> Dict:
        """Get current page information"""
        result = await self._execute_command("get_info")
        if result["status"] == "success":
            return result["info"]
        raise Exception(f"Failed to get info: {result.get('message')}")
    
    async def close_session(self):
        """Close the browser session"""
        if self.session_id:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{self.server_url}/sessions/{self.session_id}")
                response.raise_for_status()
                print(f"✓ Closed session: {self.session_id}")
                self.session_id = None
                self.current_page_id = None

# Demo functions showing Claude's workflow
async def demo_first_execution():
    """First execution: Create session and take screenshot"""
    print("=== FIRST EXECUTION: Create Session ===\n")
    
    client = PersistentBrowserClient()
    
    # Create a new session
    session_id = await client.create_session()
    
    # Create a page and navigate
    await client.new_page()
    await client.goto("https://example.com")
    
    # Take a screenshot
    screenshot_path = await client.screenshot("example_initial.png")
    
    # Get page info
    info = await client.get_info()
    
    print(f"\n✓ Session ID: {session_id}")
    print(f"✓ Page ID: {client.current_page_id}")
    print(f"✓ Screenshot: {screenshot_path}")
    print(f"✓ Page info: {json.dumps(info, indent=2)}")
    
    print("\n💡 Save these IDs to continue in next execution!")
    print(f"   Session: {session_id}")
    print(f"   Page: {client.current_page_id}")
    
    # DO NOT close session - it stays alive!
    return session_id, client.current_page_id

async def demo_second_execution(session_id: str, page_id: str):
    """Second execution: Continue with same session"""
    print("\n=== SECOND EXECUTION: Continue Session ===\n")
    
    client = PersistentBrowserClient()
    
    # Reconnect to existing session
    await client.connect_session(session_id)
    await client.set_page(page_id)
    
    # Verify we're still on the same page
    info = await client.get_info()
    print(f"✓ Still on: {info['url']}")
    
    # Continue interacting
    await client.fill('input[type="text"]', 'Hello from second execution!')
    await client.wait(1000)
    
    # Take another screenshot
    screenshot_path = await client.screenshot("example_after_action.png")
    print(f"✓ New screenshot: {screenshot_path}")
    
    # The session is STILL alive and can be used again!

async def demo_cleanup(session_id: str):
    """Clean up when done"""
    print("\n=== CLEANUP ===\n")
    
    client = PersistentBrowserClient()
    await client.connect_session(session_id)
    await client.close_session()
    print("✓ Session closed")

# Utility function to save session info
def save_session_info(session_id: str, page_id: str, filename: str = "session_info.json"):
    """Save session info for later use"""
    with open(filename, 'w') as f:
        json.dump({
            "session_id": session_id,
            "page_id": page_id,
            "timestamp": str(asyncio.get_event_loop().time())
        }, f, indent=2)
    print(f"\n✓ Session info saved to: {filename}")

def load_session_info(filename: str = "session_info.json") -> tuple:
    """Load saved session info"""
    with open(filename, 'r') as f:
        data = json.load(f)
    return data["session_id"], data["page_id"]

if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            if sys.argv[1] == "first":
                # First execution
                session_id, page_id = await demo_first_execution()
                save_session_info(session_id, page_id)
                
            elif sys.argv[1] == "second":
                # Second execution - continue session
                session_id, page_id = load_session_info()
                await demo_second_execution(session_id, page_id)
                
            elif sys.argv[1] == "cleanup":
                # Cleanup
                session_id, _ = load_session_info()
                await demo_cleanup(session_id)
        else:
            print("Usage:")
            print("  python browser_client_poc.py first    # Create session")
            print("  python browser_client_poc.py second   # Continue session")
            print("  python browser_client_poc.py cleanup  # Close session")
    
    asyncio.run(main())