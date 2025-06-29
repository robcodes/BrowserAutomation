# Persistent Browser Server System Design

## Executive Summary

This document outlines the design for a persistent browser server that maintains Playwright browser sessions between Claude's code executions. The system enables Claude to interact with browsers asynchronously, take screenshots for analysis, and continue sessions without losing state.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐     HTTP/WebSocket      ┌──────────────────┐
│                 │ ◄──────────────────────► │                  │
│  Claude Client  │                          │  Browser Server  │
│  (Python Code)  │                          │   (FastAPI +     │
│                 │                          │   Playwright)    │
└─────────────────┘                          └──────────────────┘
                                                      │
                                                      ▼
                                             ┌──────────────────┐
                                             │  Browser Pool    │
                                             │  - Chrome        │
                                             │  - Firefox       │
                                             │  - WebKit        │
                                             └──────────────────┘
```

### Component Overview

1. **Browser Server**: FastAPI-based server managing Playwright browser instances
2. **Session Manager**: Handles browser session lifecycle and state persistence
3. **Command Processor**: Executes Playwright commands and returns results
4. **Screenshot Service**: Captures and stores screenshots for Claude's analysis
5. **State Store**: Persists session data and browser state between restarts

## API Design

### RESTful API Endpoints

#### Session Management

```python
# Create new browser session
POST /sessions
{
    "browser_type": "chromium",  # chromium, firefox, webkit
    "headless": true,
    "viewport": {"width": 1920, "height": 1080},
    "user_agent": "...",
    "extra_args": ["--disable-blink-features=AutomationControlled"]
}
Response: {
    "session_id": "uuid-v4",
    "status": "active",
    "created_at": "2025-01-23T10:00:00Z"
}

# List all sessions
GET /sessions
Response: [
    {
        "session_id": "uuid-v4",
        "browser_type": "chromium",
        "status": "active",
        "pages": 2,
        "created_at": "2025-01-23T10:00:00Z"
    }
]

# Get session details
GET /sessions/{session_id}

# Close session
DELETE /sessions/{session_id}
```

#### Page Operations

```python
# Create new page
POST /sessions/{session_id}/pages
{
    "url": "https://example.com",
    "wait_until": "networkidle"
}
Response: {
    "page_id": "page-uuid",
    "url": "https://example.com",
    "title": "Example Domain"
}

# Execute command on page
POST /sessions/{session_id}/pages/{page_id}/execute
{
    "command": "click",
    "selector": "button#submit",
    "options": {"timeout": 30000}
}

# Take screenshot
POST /sessions/{session_id}/pages/{page_id}/screenshot
{
    "full_page": true,
    "format": "png"
}
Response: {
    "screenshot_id": "screenshot-uuid",
    "path": "/screenshots/screenshot-uuid.png",
    "size": {"width": 1920, "height": 3000}
}

# Get page content
GET /sessions/{session_id}/pages/{page_id}/content

# Evaluate JavaScript
POST /sessions/{session_id}/pages/{page_id}/evaluate
{
    "expression": "document.title",
    "await": true
}
```

### WebSocket API for Real-time Updates

```python
# WebSocket endpoint for live updates
WS /sessions/{session_id}/ws

# Message format
{
    "type": "command",
    "id": "msg-uuid",
    "payload": {
        "action": "navigate",
        "url": "https://example.com"
    }
}

# Response format
{
    "type": "response",
    "id": "msg-uuid",
    "status": "success",
    "data": {...}
}

# Event notifications
{
    "type": "event",
    "event": "page_loaded",
    "data": {
        "page_id": "page-uuid",
        "url": "https://example.com"
    }
}
```

## Implementation Architecture

### Server Structure

```python
browser-server/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── models/
│   ├── __init__.py
│   ├── session.py         # Session data models
│   ├── page.py           # Page data models
│   └── command.py        # Command/response models
├── services/
│   ├── __init__.py
│   ├── browser_pool.py   # Browser instance management
│   ├── session_manager.py # Session lifecycle management
│   ├── command_executor.py # Command execution engine
│   └── screenshot_service.py # Screenshot handling
├── api/
│   ├── __init__.py
│   ├── sessions.py       # Session endpoints
│   ├── pages.py         # Page operation endpoints
│   └── websocket.py     # WebSocket handlers
├── storage/
│   ├── __init__.py
│   ├── redis_store.py   # Redis-based state storage
│   └── file_store.py    # File-based fallback storage
└── utils/
    ├── __init__.py
    ├── playwright_helpers.py # Playwright utility functions
    └── error_handlers.py    # Error handling utilities
```

### Core Components

#### 1. Browser Pool Manager

```python
class BrowserPool:
    def __init__(self, max_browsers: int = 10):
        self.browsers: Dict[str, Browser] = {}
        self.playwright: Playwright = None
        self.max_browsers = max_browsers
        self.lock = asyncio.Lock()
    
    async def get_browser(self, browser_type: str, **kwargs) -> Browser:
        """Get or create a browser instance"""
        browser_key = f"{browser_type}_{hash(frozenset(kwargs.items()))}"
        
        async with self.lock:
            if browser_key not in self.browsers:
                if len(self.browsers) >= self.max_browsers:
                    # Evict least recently used browser
                    await self._evict_lru_browser()
                
                browser = await self._create_browser(browser_type, **kwargs)
                self.browsers[browser_key] = browser
            
            return self.browsers[browser_key]
```

#### 2. Session Manager

```python
class SessionManager:
    def __init__(self, storage: StateStorage):
        self.sessions: Dict[str, BrowserSession] = {}
        self.storage = storage
        self.cleanup_interval = 3600  # 1 hour
    
    async def create_session(self, config: SessionConfig) -> BrowserSession:
        """Create a new browser session"""
        session = BrowserSession(
            id=str(uuid.uuid4()),
            browser_type=config.browser_type,
            config=config
        )
        
        # Initialize browser
        browser = await self.browser_pool.get_browser(
            config.browser_type,
            **config.browser_args
        )
        session.browser = browser
        
        # Create initial context
        context = await browser.new_context(**config.context_args)
        session.context = context
        
        # Store session
        self.sessions[session.id] = session
        await self.storage.save_session(session)
        
        return session
```

#### 3. Command Executor

```python
class CommandExecutor:
    def __init__(self):
        self.command_registry = {
            "navigate": self._navigate,
            "click": self._click,
            "fill": self._fill,
            "select": self._select,
            "wait_for_selector": self._wait_for_selector,
            "evaluate": self._evaluate,
            # ... more commands
        }
    
    async def execute(self, page: Page, command: Command) -> CommandResult:
        """Execute a Playwright command on a page"""
        handler = self.command_registry.get(command.action)
        if not handler:
            raise ValueError(f"Unknown command: {command.action}")
        
        try:
            result = await handler(page, **command.params)
            return CommandResult(
                success=True,
                data=result,
                error=None
            )
        except Exception as e:
            return CommandResult(
                success=False,
                data=None,
                error=str(e)
            )
```

## Client Library Design

### Python Client for Claude

```python
class BrowserClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.session = None
    
    async def create_session(self, browser_type: str = "chromium", **kwargs):
        """Create a new browser session"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.server_url}/sessions",
                json={"browser_type": browser_type, **kwargs}
            ) as resp:
                data = await resp.json()
                self.session_id = data["session_id"]
                return self
    
    async def new_page(self, url: str = None):
        """Create a new page in the session"""
        page = RemotePage(self.server_url, self.session_id)
        await page.initialize(url)
        return page

class RemotePage:
    def __init__(self, server_url: str, session_id: str):
        self.server_url = server_url
        self.session_id = session_id
        self.page_id = None
    
    async def goto(self, url: str, **kwargs):
        """Navigate to URL"""
        return await self._execute_command("navigate", url=url, **kwargs)
    
    async def click(self, selector: str, **kwargs):
        """Click element"""
        return await self._execute_command("click", selector=selector, **kwargs)
    
    async def screenshot(self, path: str = None, full_page: bool = False):
        """Take screenshot"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.server_url}/sessions/{self.session_id}/pages/{self.page_id}/screenshot",
                json={"full_page": full_page}
            ) as resp:
                data = await resp.json()
                
                # Download screenshot
                if path:
                    async with session.get(f"{self.server_url}{data['path']}") as img_resp:
                        with open(path, 'wb') as f:
                            f.write(await img_resp.read())
                
                return data
```

## Usage Examples

### Basic Usage Pattern

```python
# Claude's code execution 1: Start a session and navigate
async with BrowserClient() as client:
    await client.create_session(headless=False)
    page = await client.new_page()
    await page.goto("https://example.com")
    
    # Take screenshot for analysis
    screenshot = await page.screenshot("example.png")
    print(f"Session ID: {client.session_id}")
    print(f"Page ID: {page.page_id}")

# Claude analyzes screenshot...

# Claude's code execution 2: Continue with the same session
async with BrowserClient() as client:
    # Reconnect to existing session
    await client.connect_session(session_id)
    page = await client.get_page(page_id)
    
    # Continue interaction
    await page.click("button#submit")
    await page.wait_for_navigation()
    
    # Take another screenshot
    await page.screenshot("result.png")
```

### Advanced Patterns

```python
# Multiple concurrent pages
async with BrowserClient() as client:
    await client.create_session()
    
    # Open multiple tabs
    pages = []
    for url in ["https://google.com", "https://github.com", "https://stackoverflow.com"]:
        page = await client.new_page(url)
        pages.append(page)
    
    # Interact with all pages
    for i, page in enumerate(pages):
        await page.screenshot(f"tab_{i}.png")

# WebSocket for real-time updates
async with BrowserClient() as client:
    await client.create_session()
    
    # Connect WebSocket
    async with client.websocket() as ws:
        # Send command
        await ws.send_command("navigate", url="https://example.com")
        
        # Listen for events
        async for event in ws.events():
            if event.type == "page_loaded":
                print(f"Page loaded: {event.data['url']}")
```

## State Persistence

### Session State Storage

```python
# Redis schema
{
    "session:{session_id}": {
        "id": "uuid",
        "browser_type": "chromium",
        "created_at": "2025-01-23T10:00:00Z",
        "last_accessed": "2025-01-23T10:30:00Z",
        "config": {...},
        "pages": ["page_id1", "page_id2"]
    },
    "page:{page_id}": {
        "id": "page_id",
        "session_id": "session_id",
        "url": "https://example.com",
        "title": "Example",
        "viewport": {"width": 1920, "height": 1080}
    }
}
```

### Recovery Mechanism

```python
class StateRecovery:
    async def restore_sessions(self):
        """Restore sessions after server restart"""
        stored_sessions = await self.storage.get_all_sessions()
        
        for session_data in stored_sessions:
            try:
                # Recreate browser and context
                browser = await self.browser_pool.get_browser(
                    session_data["browser_type"],
                    **session_data["config"]
                )
                
                context = await browser.new_context()
                
                # Restore pages
                for page_data in session_data["pages"]:
                    page = await context.new_page()
                    await page.goto(page_data["url"])
                    
                    # Restore viewport
                    await page.set_viewport_size(**page_data["viewport"])
                
            except Exception as e:
                logger.error(f"Failed to restore session {session_data['id']}: {e}")
```

## Error Handling

### Error Types and Recovery

```python
class BrowserServerError(Exception):
    """Base exception for browser server errors"""
    pass

class SessionNotFoundError(BrowserServerError):
    """Session does not exist"""
    pass

class BrowserCrashError(BrowserServerError):
    """Browser process crashed"""
    pass

class CommandTimeoutError(BrowserServerError):
    """Command execution timed out"""
    pass

# Error recovery strategies
async def with_retry(func, max_retries=3, backoff=1.0):
    """Retry failed operations with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return await func()
        except BrowserCrashError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(backoff * (2 ** attempt))
            # Recreate browser
            await recreate_browser()
```

## Security Considerations

### 1. Authentication & Authorization

```python
# API key authentication
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials
```

### 2. Input Validation

```python
from pydantic import BaseModel, validator, HttpUrl

class NavigateRequest(BaseModel):
    url: HttpUrl
    wait_until: Literal["load", "domcontentloaded", "networkidle"] = "load"
    
    @validator('url')
    def validate_url(cls, v):
        # Prevent navigation to internal/private IPs
        if any(blocked in str(v) for blocked in ["localhost", "127.0.0.1", "0.0.0.0"]):
            raise ValueError("Navigation to internal addresses not allowed")
        return v
```

### 3. Resource Limits

```python
class ResourceLimits:
    MAX_SESSIONS_PER_CLIENT = 10
    MAX_PAGES_PER_SESSION = 20
    MAX_SCREENSHOT_SIZE = 10 * 1024 * 1024  # 10MB
    SESSION_TIMEOUT = 3600  # 1 hour
    COMMAND_TIMEOUT = 30000  # 30 seconds
```

### 4. Sandboxing

```python
# Browser sandboxing options
BROWSER_ARGS = [
    "--no-sandbox",  # Required in Docker
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--no-first-run",
    "--no-zygote",
    "--single-process",  # For containers
    "--disable-gpu"
]
```

## Performance Optimizations

### 1. Connection Pooling

```python
class ConnectionPool:
    def __init__(self, min_size=2, max_size=10):
        self.min_size = min_size
        self.max_size = max_size
        self.pool = []
        self.in_use = set()
    
    async def acquire(self):
        """Get a connection from the pool"""
        if not self.pool and len(self.in_use) < self.max_size:
            conn = await self._create_connection()
            self.in_use.add(conn)
            return conn
        
        while not self.pool:
            await asyncio.sleep(0.1)
        
        conn = self.pool.pop()
        self.in_use.add(conn)
        return conn
```

### 2. Caching

```python
from functools import lru_cache
import hashlib

class ScreenshotCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
    
    def get_cache_key(self, url: str, viewport: dict, full_page: bool) -> str:
        """Generate cache key for screenshot"""
        data = f"{url}:{viewport}:{full_page}"
        return hashlib.md5(data.encode()).hexdigest()
    
    async def get_or_capture(self, page, full_page=False):
        """Get screenshot from cache or capture new one"""
        cache_key = self.get_cache_key(
            await page.url(),
            await page.viewport_size(),
            full_page
        )
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        screenshot = await page.screenshot(full_page=full_page)
        self.cache[cache_key] = screenshot
        
        # Evict old entries if cache is full
        if len(self.cache) > self.max_size:
            oldest = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest]
        
        return screenshot
```

## Monitoring and Observability

### 1. Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
session_created = Counter('browser_sessions_created', 'Total sessions created')
session_active = Gauge('browser_sessions_active', 'Currently active sessions')
command_duration = Histogram('browser_command_duration_seconds', 'Command execution time')
screenshot_size = Histogram('browser_screenshot_size_bytes', 'Screenshot file sizes')

# Usage
@command_duration.time()
async def execute_command(command):
    # Command execution
    pass
```

### 2. Logging

```python
import structlog

logger = structlog.get_logger()

# Structured logging
logger.info(
    "session_created",
    session_id=session.id,
    browser_type=session.browser_type,
    client_ip=request.client.host
)
```

## Deployment Considerations

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install browser dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium firefox webkit

# Copy application
COPY . /app
WORKDIR /app

# Run server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: browser-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: browser-server
  template:
    metadata:
      labels:
        app: browser-server
    spec:
      containers:
      - name: browser-server
        image: browser-server:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        env:
        - name: MAX_BROWSERS
          value: "5"
        - name: REDIS_URL
          value: "redis://redis:6379"
---
apiVersion: v1
kind: Service
metadata:
  name: browser-server
spec:
  selector:
    app: browser-server
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Challenges and Solutions

### 1. Memory Management

**Challenge**: Browser instances consume significant memory
**Solution**: 
- Implement aggressive garbage collection
- Set memory limits per browser
- Auto-close idle sessions
- Use headless mode by default

### 2. Concurrent Access

**Challenge**: Multiple clients accessing same session
**Solution**:
- Implement session locking mechanism
- Queue commands per session
- Use WebSocket for real-time coordination

### 3. Browser Crashes

**Challenge**: Browser processes can crash unexpectedly
**Solution**:
- Health check monitoring
- Automatic browser restart
- Session state recovery
- Circuit breaker pattern

### 4. Network Reliability

**Challenge**: Network interruptions between client and server
**Solution**:
- Implement retry logic with exponential backoff
- Command idempotency
- Response caching
- WebSocket reconnection logic

## Future Enhancements

1. **Multi-region deployment** for global availability
2. **Browser recording** for session replay
3. **AI-powered element detection** for resilient selectors
4. **Plugin system** for custom commands
5. **GraphQL API** for more flexible queries
6. **Browser extension support**
7. **Mobile browser emulation**
8. **Performance profiling tools**

## Conclusion

This persistent browser server design provides Claude with a robust system for maintaining browser sessions across code executions. The architecture balances flexibility, performance, and reliability while maintaining full Playwright capabilities. The modular design allows for easy extension and adaptation to specific use cases.