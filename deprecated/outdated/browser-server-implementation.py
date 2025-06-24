"""
Persistent Browser Server - Core Implementation
A FastAPI-based server that maintains Playwright browser sessions
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import json
import os

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl
import aiofiles
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
import redis.asyncio as redis
from loguru import logger

# Configuration
class Config:
    API_KEY = os.getenv("BROWSER_SERVER_API_KEY", "development-key")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "10"))
    MAX_PAGES_PER_SESSION = int(os.getenv("MAX_PAGES_PER_SESSION", "20"))
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", "/tmp/screenshots")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

# Ensure screenshot directory exists
os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)

# Security
security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != Config.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials

# Models
class SessionConfig(BaseModel):
    browser_type: str = Field(default="chromium", pattern="^(chromium|firefox|webkit)$")
    headless: bool = True
    viewport: Dict[str, int] = {"width": 1920, "height": 1080}
    user_agent: Optional[str] = None
    extra_args: List[str] = []
    locale: str = "en-US"
    timezone: str = "America/New_York"

class CreatePageRequest(BaseModel):
    url: Optional[HttpUrl] = None
    wait_until: str = Field(default="load", pattern="^(load|domcontentloaded|networkidle)$")

class CommandRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}
    timeout: int = 30000

class ScreenshotRequest(BaseModel):
    full_page: bool = False
    format: str = Field(default="png", pattern="^(png|jpeg)$")
    quality: Optional[int] = Field(None, ge=0, le=100)

class EvaluateRequest(BaseModel):
    expression: str
    arg: Optional[Any] = None
    await_promise: bool = True

# Browser Session Management
class BrowserSession:
    def __init__(self, session_id: str, config: SessionConfig):
        self.id = session_id
        self.config = config
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.pages: Dict[str, Page] = {}
        self.is_active = True
        
    def to_dict(self):
        return {
            "session_id": self.id,
            "browser_type": self.config.browser_type,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "pages": list(self.pages.keys()),
            "is_active": self.is_active
        }
    
    def update_accessed(self):
        self.last_accessed = datetime.utcnow()

class BrowserPool:
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browsers: Dict[str, Browser] = {}
        self.lock = asyncio.Lock()
        
    async def initialize(self):
        self.playwright = await async_playwright().start()
        
    async def get_browser(self, browser_type: str, **kwargs) -> Browser:
        async with self.lock:
            browser_key = f"{browser_type}_{hash(frozenset(kwargs.items()))}"
            
            if browser_key not in self.browsers:
                logger.info(f"Creating new {browser_type} browser instance")
                
                if browser_type == "chromium":
                    browser = await self.playwright.chromium.launch(**kwargs)
                elif browser_type == "firefox":
                    browser = await self.playwright.firefox.launch(**kwargs)
                elif browser_type == "webkit":
                    browser = await self.playwright.webkit.launch(**kwargs)
                else:
                    raise ValueError(f"Unsupported browser type: {browser_type}")
                    
                self.browsers[browser_key] = browser
                
            return self.browsers[browser_key]
    
    async def cleanup(self):
        for browser in self.browsers.values():
            await browser.close()
        if self.playwright:
            await self.playwright.stop()

class SessionManager:
    def __init__(self, browser_pool: BrowserPool, redis_client: redis.Redis):
        self.browser_pool = browser_pool
        self.redis = redis_client
        self.sessions: Dict[str, BrowserSession] = {}
        self.lock = asyncio.Lock()
        
    async def create_session(self, config: SessionConfig) -> BrowserSession:
        async with self.lock:
            if len(self.sessions) >= Config.MAX_SESSIONS:
                raise HTTPException(status_code=429, detail="Maximum sessions reached")
            
            session_id = str(uuid.uuid4())
            session = BrowserSession(session_id, config)
            
            # Get browser from pool
            browser_args = {
                "headless": config.headless,
                "args": config.extra_args
            }
            browser = await self.browser_pool.get_browser(config.browser_type, **browser_args)
            session.browser = browser
            
            # Create context with configuration
            context_args = {
                "viewport": config.viewport,
                "locale": config.locale,
                "timezone_id": config.timezone
            }
            if config.user_agent:
                context_args["user_agent"] = config.user_agent
                
            session.context = await browser.new_context(**context_args)
            
            # Store session
            self.sessions[session_id] = session
            await self._save_session_to_redis(session)
            
            logger.info(f"Created session {session_id}")
            return session
    
    async def get_session(self, session_id: str) -> BrowserSession:
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.update_accessed()
        return session
    
    async def delete_session(self, session_id: str):
        async with self.lock:
            session = self.sessions.get(session_id)
            if session:
                # Close all pages
                for page in session.pages.values():
                    await page.close()
                
                # Close context
                if session.context:
                    await session.context.close()
                
                # Mark as inactive
                session.is_active = False
                
                # Remove from memory
                del self.sessions[session_id]
                
                # Remove from Redis
                await self.redis.delete(f"session:{session_id}")
                
                logger.info(f"Deleted session {session_id}")
    
    async def _save_session_to_redis(self, session: BrowserSession):
        key = f"session:{session.id}"
        data = json.dumps(session.to_dict())
        await self.redis.setex(key, Config.SESSION_TIMEOUT, data)
    
    async def cleanup_expired_sessions(self):
        """Background task to clean up expired sessions"""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_sessions = []
                
                for session_id, session in self.sessions.items():
                    age = (current_time - session.last_accessed).total_seconds()
                    if age > Config.SESSION_TIMEOUT:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    logger.info(f"Cleaning up expired session {session_id}")
                    await self.delete_session(session_id)
                    
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                
            await asyncio.sleep(300)  # Check every 5 minutes

# Command Executor
class CommandExecutor:
    def __init__(self):
        self.commands = {
            "navigate": self._navigate,
            "click": self._click,
            "fill": self._fill,
            "select": self._select,
            "check": self._check,
            "uncheck": self._uncheck,
            "hover": self._hover,
            "focus": self._focus,
            "press": self._press,
            "type": self._type,
            "wait_for_selector": self._wait_for_selector,
            "wait_for_load_state": self._wait_for_load_state,
            "wait_for_url": self._wait_for_url,
            "go_back": self._go_back,
            "go_forward": self._go_forward,
            "reload": self._reload,
            "set_viewport_size": self._set_viewport_size,
        }
    
    async def execute(self, page: Page, command: CommandRequest) -> Dict[str, Any]:
        handler = self.commands.get(command.action)
        if not handler:
            raise HTTPException(status_code=400, detail=f"Unknown command: {command.action}")
        
        try:
            result = await handler(page, **command.params)
            return {
                "success": True,
                "data": result,
                "error": None
            }
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }
    
    # Command implementations
    async def _navigate(self, page: Page, url: str, wait_until: str = "load", **kwargs):
        response = await page.goto(url, wait_until=wait_until, **kwargs)
        return {
            "url": page.url,
            "title": await page.title(),
            "status": response.status if response else None
        }
    
    async def _click(self, page: Page, selector: str, **kwargs):
        await page.click(selector, **kwargs)
        return {"clicked": True}
    
    async def _fill(self, page: Page, selector: str, value: str, **kwargs):
        await page.fill(selector, value, **kwargs)
        return {"filled": True}
    
    async def _select(self, page: Page, selector: str, value: str, **kwargs):
        await page.select_option(selector, value, **kwargs)
        return {"selected": True}
    
    async def _check(self, page: Page, selector: str, **kwargs):
        await page.check(selector, **kwargs)
        return {"checked": True}
    
    async def _uncheck(self, page: Page, selector: str, **kwargs):
        await page.uncheck(selector, **kwargs)
        return {"unchecked": True}
    
    async def _hover(self, page: Page, selector: str, **kwargs):
        await page.hover(selector, **kwargs)
        return {"hovered": True}
    
    async def _focus(self, page: Page, selector: str, **kwargs):
        await page.focus(selector, **kwargs)
        return {"focused": True}
    
    async def _press(self, page: Page, selector: str, key: str, **kwargs):
        await page.press(selector, key, **kwargs)
        return {"pressed": True}
    
    async def _type(self, page: Page, selector: str, text: str, **kwargs):
        await page.type(selector, text, **kwargs)
        return {"typed": True}
    
    async def _wait_for_selector(self, page: Page, selector: str, **kwargs):
        element = await page.wait_for_selector(selector, **kwargs)
        return {"found": element is not None}
    
    async def _wait_for_load_state(self, page: Page, state: str = "load", **kwargs):
        await page.wait_for_load_state(state, **kwargs)
        return {"loaded": True}
    
    async def _wait_for_url(self, page: Page, url: str, **kwargs):
        await page.wait_for_url(url, **kwargs)
        return {"url_matched": True}
    
    async def _go_back(self, page: Page, **kwargs):
        response = await page.go_back(**kwargs)
        return {
            "url": page.url,
            "status": response.status if response else None
        }
    
    async def _go_forward(self, page: Page, **kwargs):
        response = await page.go_forward(**kwargs)
        return {
            "url": page.url,
            "status": response.status if response else None
        }
    
    async def _reload(self, page: Page, **kwargs):
        response = await page.reload(**kwargs)
        return {
            "url": page.url,
            "status": response.status if response else None
        }
    
    async def _set_viewport_size(self, page: Page, width: int, height: int):
        await page.set_viewport_size(width=width, height=height)
        return {"width": width, "height": height}

# Screenshot Service
class ScreenshotService:
    @staticmethod
    async def capture(page: Page, request: ScreenshotRequest) -> Dict[str, Any]:
        screenshot_id = str(uuid.uuid4())
        filename = f"{screenshot_id}.{request.format}"
        filepath = os.path.join(Config.SCREENSHOT_DIR, filename)
        
        screenshot_args = {
            "path": filepath,
            "full_page": request.full_page,
            "type": request.format
        }
        
        if request.quality and request.format == "jpeg":
            screenshot_args["quality"] = request.quality
        
        await page.screenshot(**screenshot_args)
        
        # Get file size
        stat = os.stat(filepath)
        
        return {
            "screenshot_id": screenshot_id,
            "path": f"/screenshots/{filename}",
            "size": stat.st_size,
            "format": request.format,
            "created_at": datetime.utcnow().isoformat()
        }

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting browser server...")
    
    # Initialize Redis
    app.state.redis = await redis.from_url(Config.REDIS_URL)
    
    # Initialize browser pool
    app.state.browser_pool = BrowserPool()
    await app.state.browser_pool.initialize()
    
    # Initialize session manager
    app.state.session_manager = SessionManager(app.state.browser_pool, app.state.redis)
    
    # Initialize command executor
    app.state.command_executor = CommandExecutor()
    
    # Start cleanup task
    cleanup_task = asyncio.create_task(app.state.session_manager.cleanup_expired_sessions())
    
    logger.info("Browser server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down browser server...")
    
    # Cancel cleanup task
    cleanup_task.cancel()
    
    # Close all sessions
    for session_id in list(app.state.session_manager.sessions.keys()):
        await app.state.session_manager.delete_session(session_id)
    
    # Cleanup browser pool
    await app.state.browser_pool.cleanup()
    
    # Close Redis
    await app.state.redis.close()
    
    logger.info("Browser server shut down")

# Create FastAPI app
app = FastAPI(
    title="Persistent Browser Server",
    description="A server that maintains Playwright browser sessions between code executions",
    version="1.0.0",
    lifespan=lifespan
)

# Session endpoints
@app.post("/sessions", dependencies=[Depends(verify_api_key)])
async def create_session(config: SessionConfig):
    """Create a new browser session"""
    session = await app.state.session_manager.create_session(config)
    return session.to_dict()

@app.get("/sessions", dependencies=[Depends(verify_api_key)])
async def list_sessions():
    """List all active sessions"""
    return [session.to_dict() for session in app.state.session_manager.sessions.values()]

@app.get("/sessions/{session_id}", dependencies=[Depends(verify_api_key)])
async def get_session(session_id: str):
    """Get session details"""
    session = await app.state.session_manager.get_session(session_id)
    return session.to_dict()

@app.delete("/sessions/{session_id}", dependencies=[Depends(verify_api_key)])
async def delete_session(session_id: str):
    """Close a session"""
    await app.state.session_manager.delete_session(session_id)
    return {"message": "Session deleted"}

# Page endpoints
@app.post("/sessions/{session_id}/pages", dependencies=[Depends(verify_api_key)])
async def create_page(session_id: str, request: CreatePageRequest):
    """Create a new page in the session"""
    session = await app.state.session_manager.get_session(session_id)
    
    if len(session.pages) >= Config.MAX_PAGES_PER_SESSION:
        raise HTTPException(status_code=429, detail="Maximum pages per session reached")
    
    page_id = str(uuid.uuid4())
    page = await session.context.new_page()
    session.pages[page_id] = page
    
    result = {
        "page_id": page_id,
        "created": True
    }
    
    if request.url:
        response = await page.goto(str(request.url), wait_until=request.wait_until)
        result.update({
            "url": page.url,
            "title": await page.title(),
            "status": response.status if response else None
        })
    
    return result

@app.get("/sessions/{session_id}/pages", dependencies=[Depends(verify_api_key)])
async def list_pages(session_id: str):
    """List all pages in a session"""
    session = await app.state.session_manager.get_session(session_id)
    
    pages = []
    for page_id, page in session.pages.items():
        pages.append({
            "page_id": page_id,
            "url": page.url,
            "title": await page.title()
        })
    
    return pages

@app.post("/sessions/{session_id}/pages/{page_id}/execute", dependencies=[Depends(verify_api_key)])
async def execute_command(session_id: str, page_id: str, command: CommandRequest):
    """Execute a command on a page"""
    session = await app.state.session_manager.get_session(session_id)
    
    if page_id not in session.pages:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page = session.pages[page_id]
    result = await app.state.command_executor.execute(page, command)
    
    return result

@app.post("/sessions/{session_id}/pages/{page_id}/screenshot", dependencies=[Depends(verify_api_key)])
async def take_screenshot(session_id: str, page_id: str, request: ScreenshotRequest):
    """Take a screenshot of the page"""
    session = await app.state.session_manager.get_session(session_id)
    
    if page_id not in session.pages:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page = session.pages[page_id]
    result = await ScreenshotService.capture(page, request)
    
    return result

@app.get("/sessions/{session_id}/pages/{page_id}/content", dependencies=[Depends(verify_api_key)])
async def get_page_content(session_id: str, page_id: str):
    """Get the HTML content of the page"""
    session = await app.state.session_manager.get_session(session_id)
    
    if page_id not in session.pages:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page = session.pages[page_id]
    content = await page.content()
    
    return {
        "url": page.url,
        "title": await page.title(),
        "content": content
    }

@app.post("/sessions/{session_id}/pages/{page_id}/evaluate", dependencies=[Depends(verify_api_key)])
async def evaluate_javascript(session_id: str, page_id: str, request: EvaluateRequest):
    """Evaluate JavaScript in the page context"""
    session = await app.state.session_manager.get_session(session_id)
    
    if page_id not in session.pages:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page = session.pages[page_id]
    
    try:
        result = await page.evaluate(request.expression, request.arg)
        return {
            "success": True,
            "result": result,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": str(e)
        }

@app.delete("/sessions/{session_id}/pages/{page_id}", dependencies=[Depends(verify_api_key)])
async def close_page(session_id: str, page_id: str):
    """Close a specific page"""
    session = await app.state.session_manager.get_session(session_id)
    
    if page_id not in session.pages:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page = session.pages[page_id]
    await page.close()
    del session.pages[page_id]
    
    return {"message": "Page closed"}

# Screenshot serving
@app.get("/screenshots/{filename}")
async def get_screenshot(filename: str):
    """Serve screenshot files"""
    filepath = os.path.join(Config.SCREENSHOT_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    return FileResponse(filepath)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(app.state.session_manager.sessions),
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)