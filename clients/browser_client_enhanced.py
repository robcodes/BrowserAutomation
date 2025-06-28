#!/usr/bin/env python3
"""
Enhanced Browser Client with Console Log Support
Client library for interacting with the enhanced browser server
"""
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json

class EnhancedBrowserClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.session_id = None
        self.page_id = None
    
    async def create_session(self, browser_type: str = "chromium", headless: bool = True) -> str:
        """Create a new browser session"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/sessions",
                json={"browser_type": browser_type, "headless": headless}
            )
            response.raise_for_status()
            data = response.json()
            self.session_id = data["session_id"]
            return self.session_id
    
    async def connect_session(self, session_id: str):
        """Connect to an existing session"""
        # Check if session exists
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.server_url}/sessions")
            response.raise_for_status()
            sessions = response.json()["sessions"]
            if session_id not in sessions:
                raise ValueError(f"Session {session_id} not found")
        
        self.session_id = session_id
    
    async def new_page(self, url: Optional[str] = None) -> str:
        """Create a new page in the current session"""
        if not self.session_id:
            raise ValueError("No session connected")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/sessions/{self.session_id}/pages",
                params={"url": url} if url else {}
            )
            response.raise_for_status()
            data = response.json()
            self.page_id = data["page_id"]
            return self.page_id
    
    async def set_page(self, page_id: str):
        """Set the current page"""
        self.page_id = page_id
    
    async def _execute(self, command: str, *args, **kwargs):
        """Execute a command on the current page"""
        if not self.page_id:
            raise ValueError("No page selected")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.server_url}/pages/{self.page_id}/command",
                json={
                    "command": command,
                    "args": list(args),
                    "kwargs": kwargs
                }
            )
            response.raise_for_status()
            return response.json()
    
    # Console log methods
    async def get_console_logs(
        self, 
        types: Optional[List[str]] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = 100,
        text_contains: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get console logs with filtering"""
        if not self.page_id:
            raise ValueError("No page selected")
        
        params = {}
        if types:
            params["types"] = types
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()
        if limit:
            params["limit"] = limit
        if text_contains:
            params["text_contains"] = text_contains
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/pages/{self.page_id}/console",
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_errors(self, limit: int = 50) -> Dict[str, Any]:
        """Get only error and warning console logs"""
        if not self.page_id:
            raise ValueError("No page selected")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/pages/{self.page_id}/errors",
                params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_network_logs(
        self, 
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get network request/response logs"""
        if not self.page_id:
            raise ValueError("No page selected")
        
        params = {"limit": limit}
        if since:
            params["since"] = since.isoformat()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.server_url}/pages/{self.page_id}/network",
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def print_recent_errors(self):
        """Print recent errors in a nice format"""
        errors = await self.get_errors()
        if errors["errors"]:
            print("\n🚨 Recent Errors:")
            for error in errors["errors"]:
                print(f"  [{error['timestamp']}] {error['type'].upper()}: {error['text']}")
                if error.get('location'):
                    print(f"     Location: {error['location']}")
        else:
            print("✅ No errors found")
    
    async def check_for_issues(self) -> bool:
        """Check if there are any console errors or network failures"""
        # Check console errors
        errors = await self.get_errors()
        has_errors = len(errors["errors"]) > 0
        
        # Check network failures
        network = await self.get_network_logs()
        failures = [log for log in network["logs"] if log.get("failure")]
        has_failures = len(failures) > 0
        
        if has_errors or has_failures:
            print("\n⚠️  Issues detected:")
            if has_errors:
                print(f"  - {len(errors['errors'])} console errors")
            if has_failures:
                print(f"  - {len(failures)} network failures")
            return True
        return False
    
    # Navigation methods
    async def goto(self, url: str, **kwargs):
        """Navigate to a URL"""
        result = await self._execute("goto", url, **kwargs)
        return result.get("url")
    
    async def click(self, selector: str, **kwargs):
        """Click an element"""
        await self._execute("click", selector, **kwargs)
    
    async def fill(self, selector: str, value: str, **kwargs):
        """Fill an input field"""
        await self._execute("fill", selector, value, **kwargs)
    
    async def type(self, selector: str, text: str, **kwargs):
        """Type text into an element"""
        await self._execute("type", selector, text, **kwargs)
    
    async def press(self, selector: str, key: str, **kwargs):
        """Press a key"""
        await self._execute("press", selector, key, **kwargs)
    
    async def screenshot(self, filename: str = None, **kwargs):
        """Take a screenshot"""
        if filename:
            # Create screenshots directory if needed
            Path("screenshots").mkdir(exist_ok=True)
            kwargs["path"] = f"screenshots/{filename}"
        
        result = await self._execute("screenshot", **kwargs)
        return result.get("path") or result.get("data")
    
    async def wait(self, timeout: int):
        """Wait for a timeout in milliseconds"""
        await self._execute("wait", timeout)
    
    async def wait_for_selector(self, selector: str, **kwargs):
        """Wait for a selector to appear"""
        await self._execute("wait_for_selector", selector, **kwargs)
    
    async def evaluate(self, expression: str, *args):
        """Evaluate JavaScript in the page"""
        result = await self._execute("evaluate", expression, *args)
        return result.get("result")
    
    async def get_info(self):
        """Get page info (URL, title, etc)"""
        result = await self._execute("get_info")
        return result.get("info", {})
    
    async def close_session(self):
        """Close the current session"""
        if self.session_id:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.server_url}/sessions/{self.session_id}"
                )
                response.raise_for_status()
            self.session_id = None
            self.page_id = None


# Convenience functions for common patterns
async def debug_failed_action(client: EnhancedBrowserClient, action_description: str):
    """Helper to debug why an action failed"""
    print(f"\n🔍 Debugging failed action: {action_description}")
    
    # Check for recent errors
    await client.print_recent_errors()
    
    # Check network issues
    network = await client.get_network_logs(limit=20)
    failures = [log for log in network["logs"] if log.get("failure")]
    if failures:
        print("\n🌐 Network failures:")
        for failure in failures:
            print(f"  - {failure['method']} {failure['url']}: {failure['failure']}")
    
    # Get recent console logs
    logs = await client.get_console_logs(limit=10)
    if logs["logs"]:
        print("\n📋 Recent console logs:")
        for log in logs["logs"][-5:]:  # Last 5
            print(f"  [{log['type']}] {log['text']}")


# Example usage
if __name__ == "__main__":
    async def test_console_capture():
        client = EnhancedBrowserClient()
        
        # Create session
        await client.create_session()
        await client.new_page("https://example.com")
        
        # Wait a bit for any console messages
        await client.wait(2000)
        
        # Get all console logs
        logs = await client.get_console_logs()
        print(f"\nTotal console logs: {logs['count']}")
        
        # Check for errors
        await client.print_recent_errors()
        
        # Check for any issues
        has_issues = await client.check_for_issues()
        
        await client.close_session()
    
    asyncio.run(test_console_capture())