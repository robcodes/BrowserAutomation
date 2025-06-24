# Persistent Browser Server Design

## Overview
A FastAPI-based server that maintains Playwright browser sessions between Claude's code executions, solving the limitation where sessions must close when code blocks end.

## Architecture

### Core Components

```
┌─────────────────┐     HTTP/REST      ┌──────────────────┐
│                 │ ◄─────────────────► │                  │
│  Claude Client  │                     │  Browser Server  │
│  (Python lib)   │                     │    (FastAPI)     │
└─────────────────┘                     └────────┬─────────┘
                                                  │
                                                  │ Controls
                                                  ▼
                                        ┌──────────────────┐
                                        │                  │
                                        │  Playwright      │
                                        │  Browser Pool    │
                                        └──────────────────┘
```

### API Design

#### Session Management
```
POST   /sessions              # Create new browser session
GET    /sessions              # List active sessions
GET    /sessions/{id}         # Get session info
DELETE /sessions/{id}         # Close session
```

#### Page Operations
```
POST   /sessions/{id}/pages   # Create new page/tab
GET    /sessions/{id}/pages   # List pages
POST   /pages/{id}/command    # Execute command on page
GET    /pages/{id}/screenshot # Take screenshot
DELETE /pages/{id}            # Close page
```

### Command Protocol

```json
{
  "action": "click|fill|goto|evaluate|wait|...",
  "params": {
    "selector": "button.submit",
    "value": "text to fill",
    "options": {}
  }
}
```

## Implementation Plan

### 1. Server Implementation (`browser_server.py`)

```python
from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright
import uuid
import asyncio
from typing import Dict, Any

app = FastAPI()

# Global browser context manager
class BrowserManager:
    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        self.pages: Dict[str, Any] = {}
        self.playwright = None
        
    async def create_session(self, browser_type="chromium"):
        session_id = str(uuid.uuid4())
        browser = await self.browsers[browser_type].launch(headless=True)
        self.sessions[session_id] = {
            "browser": browser,
            "created_at": datetime.now(),
            "pages": []
        }
        return session_id
```

### 2. Client Library (`browser_client.py`)

```python
import httpx
import asyncio

class PersistentBrowser:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.session_id = None
        self.current_page_id = None
        
    async def create_session(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.server_url}/sessions")
            data = response.json()
            self.session_id = data["session_id"]
            return self.session_id
    
    async def screenshot(self, filename=None):
        """Take screenshot and save locally"""
        # Get screenshot from server
        # Save to file
        # Return path for Claude to analyze
```

### 3. Usage Pattern for Claude

```python
# Execution 1: Start session and explore
async def first_execution():
    browser = PersistentBrowser()
    await browser.create_session()
    
    # Navigate and take screenshot
    await browser.goto("https://example.com")
    screenshot_path = await browser.screenshot("initial.png")
    
    # Save session info for later
    print(f"Session ID: {browser.session_id}")
    print(f"Screenshot saved to: {screenshot_path}")
    # Browser stays alive on server!

# Claude analyzes screenshot...

# Execution 2: Continue same session
async def second_execution(session_id):
    browser = PersistentBrowser()
    browser.session_id = session_id  # Reconnect!
    
    # Continue where we left off
    await browser.click("button.submit")
    await browser.screenshot("after_click.png")
```

## Key Features

### 1. Session Persistence
- Sessions survive between Claude's executions
- Configurable timeout (e.g., 30 minutes)
- Session state saved to Redis for server restarts

### 2. Screenshot Workflow
```python
# Claude's workflow:
screenshot = await browser.screenshot()  # Returns path
# Execution ends, Claude sees screenshot
# Next execution: same browser still open!
```

### 3. Full Playwright API
- All Playwright methods exposed via REST
- Async operations handled server-side
- Return promises converted to synchronous results

### 4. Error Handling
- Automatic retry for flaky operations
- Session recovery after server restart
- Graceful degradation if server unavailable

## Security Considerations

1. **Authentication**: API key required
2. **Resource Limits**: Max sessions per client
3. **Timeouts**: Auto-close idle sessions
4. **Validation**: Sanitize all inputs
5. **Isolation**: Separate browser contexts

## Advanced Features

### Browser Pool
```python
class BrowserPool:
    def __init__(self, size=5):
        self.pool = []
        self.available = asyncio.Queue()
        
    async def acquire(self):
        # Get browser from pool
        
    async def release(self, browser):
        # Return browser to pool
```

### State Persistence
```python
# Save to Redis
await redis.set(f"session:{session_id}", json.dumps({
    "created_at": session.created_at,
    "last_activity": session.last_activity,
    "page_urls": [page.url for page in pages]
}))
```

### Monitoring
- Prometheus metrics endpoint
- Health check endpoint
- Session activity logging

## Deployment

### Docker Compose
```yaml
services:
  browser-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## Benefits

1. **True Persistence**: Browser sessions survive between executions
2. **Natural Workflow**: Take screenshot → Analyze → Continue same session
3. **Full Control**: All Playwright features available
4. **Scalable**: Can handle multiple concurrent sessions
5. **Reliable**: State persistence, error recovery

## Next Steps

1. Implement core server with basic commands
2. Create client library with Playwright-like API
3. Add screenshot management
4. Implement session persistence
5. Add monitoring and health checks
6. Create Docker deployment
7. Write comprehensive tests

This design solves Claude's limitation by moving the browser lifecycle management to a persistent server, allowing true continuation of browser sessions across multiple code executions.