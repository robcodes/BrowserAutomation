"""
Browser Client Library for Claude
Provides a simple interface to interact with the persistent browser server
"""

import asyncio
import aiohttp
import aiofiles
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import json
from pathlib import Path


class BrowserServerError(Exception):
    """Base exception for browser server errors"""
    pass


class SessionNotFoundError(BrowserServerError):
    """Session does not exist"""
    pass


class PageNotFoundError(BrowserServerError):
    """Page does not exist"""
    pass


class CommandError(BrowserServerError):
    """Command execution failed"""
    pass


class RemotePage:
    """Represents a page in a remote browser session"""
    
    def __init__(self, client: 'BrowserClient', session_id: str, page_id: str):
        self.client = client
        self.session_id = session_id
        self.page_id = page_id
        self._url = None
        self._title = None
    
    async def _execute_command(self, action: str, **params) -> Dict[str, Any]:
        """Execute a command on the page"""
        result = await self.client._request(
            "POST",
            f"/sessions/{self.session_id}/pages/{self.page_id}/execute",
            json={
                "action": action,
                "params": params
            }
        )
        
        if not result.get("success"):
            raise CommandError(f"Command '{action}' failed: {result.get('error')}")
        
        return result.get("data", {})
    
    # Navigation methods
    async def goto(self, url: str, wait_until: str = "load", timeout: int = 30000) -> Dict[str, Any]:
        """Navigate to a URL"""
        result = await self._execute_command("navigate", url=url, wait_until=wait_until, timeout=timeout)
        self._url = result.get("url")
        self._title = result.get("title")
        return result
    
    async def go_back(self, wait_until: str = "load", timeout: int = 30000) -> Dict[str, Any]:
        """Go back in history"""
        return await self._execute_command("go_back", wait_until=wait_until, timeout=timeout)
    
    async def go_forward(self, wait_until: str = "load", timeout: int = 30000) -> Dict[str, Any]:
        """Go forward in history"""
        return await self._execute_command("go_forward", wait_until=wait_until, timeout=timeout)
    
    async def reload(self, wait_until: str = "load", timeout: int = 30000) -> Dict[str, Any]:
        """Reload the page"""
        return await self._execute_command("reload", wait_until=wait_until, timeout=timeout)
    
    # Interaction methods
    async def click(self, selector: str, **kwargs) -> None:
        """Click an element"""
        await self._execute_command("click", selector=selector, **kwargs)
    
    async def dblclick(self, selector: str, **kwargs) -> None:
        """Double-click an element"""
        await self._execute_command("dblclick", selector=selector, **kwargs)
    
    async def fill(self, selector: str, value: str, **kwargs) -> None:
        """Fill an input field"""
        await self._execute_command("fill", selector=selector, value=value, **kwargs)
    
    async def type(self, selector: str, text: str, delay: int = 0, **kwargs) -> None:
        """Type text into an element"""
        await self._execute_command("type", selector=selector, text=text, delay=delay, **kwargs)
    
    async def press(self, selector: str, key: str, **kwargs) -> None:
        """Press a key"""
        await self._execute_command("press", selector=selector, key=key, **kwargs)
    
    async def select_option(self, selector: str, value: str, **kwargs) -> None:
        """Select an option from a dropdown"""
        await self._execute_command("select", selector=selector, value=value, **kwargs)
    
    async def check(self, selector: str, **kwargs) -> None:
        """Check a checkbox"""
        await self._execute_command("check", selector=selector, **kwargs)
    
    async def uncheck(self, selector: str, **kwargs) -> None:
        """Uncheck a checkbox"""
        await self._execute_command("uncheck", selector=selector, **kwargs)
    
    async def hover(self, selector: str, **kwargs) -> None:
        """Hover over an element"""
        await self._execute_command("hover", selector=selector, **kwargs)
    
    async def focus(self, selector: str, **kwargs) -> None:
        """Focus an element"""
        await self._execute_command("focus", selector=selector, **kwargs)
    
    # Wait methods
    async def wait_for_selector(self, selector: str, state: str = "visible", timeout: int = 30000) -> bool:
        """Wait for a selector to appear"""
        result = await self._execute_command("wait_for_selector", selector=selector, state=state, timeout=timeout)
        return result.get("found", False)
    
    async def wait_for_load_state(self, state: str = "load", timeout: int = 30000) -> None:
        """Wait for a specific load state"""
        await self._execute_command("wait_for_load_state", state=state, timeout=timeout)
    
    async def wait_for_url(self, url: str, timeout: int = 30000) -> None:
        """Wait for URL to match"""
        await self._execute_command("wait_for_url", url=url, timeout=timeout)
    
    # Content methods
    async def content(self) -> str:
        """Get the page's HTML content"""
        result = await self.client._request(
            "GET",
            f"/sessions/{self.session_id}/pages/{self.page_id}/content"
        )
        return result.get("content", "")
    
    async def title(self) -> str:
        """Get the page title"""
        if self._title is None:
            result = await self.client._request(
                "GET",
                f"/sessions/{self.session_id}/pages/{self.page_id}/content"
            )
            self._title = result.get("title", "")
        return self._title
    
    async def url(self) -> str:
        """Get the current URL"""
        if self._url is None:
            result = await self.client._request(
                "GET",
                f"/sessions/{self.session_id}/pages/{self.page_id}/content"
            )
            self._url = result.get("url", "")
        return self._url
    
    # Screenshot method
    async def screenshot(self, path: Optional[str] = None, full_page: bool = False, 
                        format: str = "png", quality: Optional[int] = None) -> Dict[str, Any]:
        """Take a screenshot of the page"""
        request_data = {
            "full_page": full_page,
            "format": format
        }
        if quality is not None:
            request_data["quality"] = quality
        
        result = await self.client._request(
            "POST",
            f"/sessions/{self.session_id}/pages/{self.page_id}/screenshot",
            json=request_data
        )
        
        # Download screenshot if path is provided
        if path:
            screenshot_url = f"{self.client.server_url}{result['path']}"
            async with self.client.session.get(screenshot_url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    Path(path).parent.mkdir(parents=True, exist_ok=True)
                    async with aiofiles.open(path, 'wb') as f:
                        await f.write(content)
                    result["downloaded_to"] = path
        
        return result
    
    # JavaScript evaluation
    async def evaluate(self, expression: str, arg: Optional[Any] = None) -> Any:
        """Evaluate JavaScript in the page context"""
        result = await self.client._request(
            "POST",
            f"/sessions/{self.session_id}/pages/{self.page_id}/evaluate",
            json={
                "expression": expression,
                "arg": arg,
                "await_promise": True
            }
        )
        
        if not result.get("success"):
            raise CommandError(f"JavaScript evaluation failed: {result.get('error')}")
        
        return result.get("result")
    
    # Viewport
    async def set_viewport_size(self, width: int, height: int) -> None:
        """Set the viewport size"""
        await self._execute_command("set_viewport_size", width=width, height=height)
    
    # Close page
    async def close(self) -> None:
        """Close this page"""
        await self.client._request(
            "DELETE",
            f"/sessions/{self.session_id}/pages/{self.page_id}"
        )


class BrowserClient:
    """Client for interacting with the persistent browser server"""
    
    def __init__(self, server_url: str = "http://localhost:8000", api_key: str = "development-key"):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.session_id: Optional[str] = None
        self.pages: Dict[str, RemotePage] = {}
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the server"""
        if not self.session:
            raise RuntimeError("Client session not initialized. Use 'async with BrowserClient() as client:'")
        
        url = f"{self.server_url}{path}"
        
        async with self.session.request(method, url, **kwargs) as resp:
            if resp.status == 404:
                if "session" in path:
                    raise SessionNotFoundError(f"Session not found: {path}")
                elif "page" in path:
                    raise PageNotFoundError(f"Page not found: {path}")
            elif resp.status >= 400:
                text = await resp.text()
                raise BrowserServerError(f"Server error {resp.status}: {text}")
            
            return await resp.json()
    
    # Session management
    async def create_session(self, browser_type: str = "chromium", headless: bool = True,
                           viewport: Optional[Dict[str, int]] = None, 
                           user_agent: Optional[str] = None,
                           extra_args: Optional[List[str]] = None,
                           locale: str = "en-US",
                           timezone: str = "America/New_York") -> 'BrowserClient':
        """Create a new browser session"""
        config = {
            "browser_type": browser_type,
            "headless": headless,
            "locale": locale,
            "timezone": timezone
        }
        
        if viewport:
            config["viewport"] = viewport
        if user_agent:
            config["user_agent"] = user_agent
        if extra_args:
            config["extra_args"] = extra_args
        
        result = await self._request("POST", "/sessions", json=config)
        self.session_id = result["session_id"]
        return self
    
    async def connect_session(self, session_id: str) -> 'BrowserClient':
        """Connect to an existing session"""
        # Verify session exists
        await self._request("GET", f"/sessions/{session_id}")
        self.session_id = session_id
        
        # Get existing pages
        pages = await self._request("GET", f"/sessions/{session_id}/pages")
        for page_info in pages:
            page = RemotePage(self, session_id, page_info["page_id"])
            page._url = page_info.get("url")
            page._title = page_info.get("title")
            self.pages[page_info["page_id"]] = page
        
        return self
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        return await self._request("GET", "/sessions")
    
    async def close_session(self) -> None:
        """Close the current session"""
        if self.session_id:
            await self._request("DELETE", f"/sessions/{self.session_id}")
            self.session_id = None
            self.pages.clear()
    
    # Page management
    async def new_page(self, url: Optional[str] = None, wait_until: str = "load") -> RemotePage:
        """Create a new page in the session"""
        if not self.session_id:
            raise RuntimeError("No active session. Call create_session() first.")
        
        request_data = {"wait_until": wait_until}
        if url:
            request_data["url"] = url
        
        result = await self._request(
            "POST",
            f"/sessions/{self.session_id}/pages",
            json=request_data
        )
        
        page = RemotePage(self, self.session_id, result["page_id"])
        page._url = result.get("url")
        page._title = result.get("title")
        self.pages[result["page_id"]] = page
        
        return page
    
    async def get_page(self, page_id: str) -> RemotePage:
        """Get an existing page by ID"""
        if page_id in self.pages:
            return self.pages[page_id]
        
        # Verify page exists
        pages = await self._request("GET", f"/sessions/{self.session_id}/pages")
        for page_info in pages:
            if page_info["page_id"] == page_id:
                page = RemotePage(self, self.session_id, page_id)
                page._url = page_info.get("url")
                page._title = page_info.get("title")
                self.pages[page_id] = page
                return page
        
        raise PageNotFoundError(f"Page {page_id} not found")
    
    async def list_pages(self) -> List[Dict[str, Any]]:
        """List all pages in the current session"""
        if not self.session_id:
            raise RuntimeError("No active session")
        
        return await self._request("GET", f"/sessions/{self.session_id}/pages")
    
    # Utility methods
    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        return await self._request("GET", "/health")


# Example usage function for Claude
async def example_usage():
    """
    Example of how to use the browser client
    """
    # Create a new session and navigate to a page
    async with BrowserClient() as client:
        await client.create_session(headless=False)
        page = await client.new_page("https://example.com")
        
        # Take a screenshot
        screenshot = await page.screenshot("example1.png", full_page=True)
        print(f"Screenshot saved: {screenshot}")
        
        # Interact with the page
        await page.click("a[href='/more']")
        await page.wait_for_load_state()
        
        # Get page info
        print(f"Current URL: {await page.url()}")
        print(f"Page title: {await page.title()}")
        
        # Save session info for later
        session_id = client.session_id
        page_id = list(client.pages.keys())[0]
        
        print(f"Session ID: {session_id}")
        print(f"Page ID: {page_id}")
    
    # Later, reconnect to the same session
    async with BrowserClient() as client:
        await client.connect_session(session_id)
        page = await client.get_page(page_id)
        
        # Continue where we left off
        content = await page.content()
        print(f"Page has {len(content)} characters of HTML")
        
        # Evaluate JavaScript
        dimensions = await page.evaluate("""
            () => ({
                width: document.documentElement.clientWidth,
                height: document.documentElement.clientHeight
            })
        """)
        print(f"Viewport dimensions: {dimensions}")
        
        # Clean up
        await client.close_session()


# Convenience function for quick screenshots
async def quick_screenshot(url: str, output_path: str, full_page: bool = False):
    """
    Quick function to take a screenshot of a URL
    """
    async with BrowserClient() as client:
        await client.create_session(headless=True)
        page = await client.new_page(url)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(output_path, full_page=full_page)
        await client.close_session()
        print(f"Screenshot saved to {output_path}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())