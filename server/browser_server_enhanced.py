#!/usr/bin/env python3
"""
Enhanced Persistent Browser Server with Console Log Capture
Maintains browser sessions across requests and captures console logs
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
import asyncio
import uuid
import base64
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import json
from collections import defaultdict, deque

app = FastAPI(title="Enhanced Browser Server", version="2.0")

# Global storage
browsers: Dict[str, Browser] = {}
sessions: Dict[str, BrowserContext] = {}
pages: Dict[str, Page] = {}
console_logs: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))  # Max 1000 logs per page
network_logs: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))   # Max 500 network logs per page

# Request/Response models
class CommandRequest(BaseModel):
    command: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}

class ConsoleLog(BaseModel):
    timestamp: datetime
    type: str  # log, info, warning, error, debug, trace
    text: str
    location: Optional[str] = None
    args: List[Any] = []

class NetworkLog(BaseModel):
    timestamp: datetime
    method: str
    url: str
    status: Optional[int] = None
    type: str  # request or response
    failure: Optional[str] = None

class LogQueryRequest(BaseModel):
    types: Optional[List[str]] = None  # Filter by log types
    since: Optional[datetime] = None   # Logs since this time
    until: Optional[datetime] = None   # Logs until this time
    limit: Optional[int] = 100         # Max number of logs to return
    text_contains: Optional[str] = None # Filter logs containing this text

@app.on_event("startup")
async def startup():
    """Initialize Playwright on startup"""
    global playwright_instance
    playwright_instance = await async_playwright().start()
    print("✓ Playwright initialized")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    # Close all pages
    for page in pages.values():
        await page.close()
    
    # Close all sessions
    for session in sessions.values():
        await session.close()
    
    # Close all browsers
    for browser in browsers.values():
        await browser.close()
    
    # Stop Playwright
    await playwright_instance.stop()

async def setup_page_listeners(page_id: str, page: Page):
    """Set up console and network listeners for a page"""
    
    # Console log listener
    async def on_console(msg):
        log_entry = {
            "timestamp": datetime.now(),
            "type": msg.type,
            "text": msg.text,
            "location": msg.location if hasattr(msg, 'location') else None,
            "args": []
        }
        
        # Try to get arguments
        try:
            args = []
            for arg in msg.args:
                try:
                    args.append(await arg.json_value())
                except:
                    args.append(str(arg))
            log_entry["args"] = args
        except:
            pass
        
        console_logs[page_id].append(log_entry)
        
        # Also print to server console for debugging
        print(f"[{msg.type}] {msg.text}")
    
    # Network request listener
    async def on_request(request):
        log_entry = {
            "timestamp": datetime.now(),
            "method": request.method,
            "url": request.url,
            "type": "request"
        }
        network_logs[page_id].append(log_entry)
    
    # Network response listener
    async def on_response(response):
        log_entry = {
            "timestamp": datetime.now(),
            "method": response.request.method,
            "url": response.url,
            "status": response.status,
            "type": "response"
        }
        network_logs[page_id].append(log_entry)
    
    # Network failure listener
    async def on_request_failed(request):
        log_entry = {
            "timestamp": datetime.now(),
            "method": request.method,
            "url": request.url,
            "type": "request",
            "failure": request.failure
        }
        network_logs[page_id].append(log_entry)
    
    # Attach listeners
    page.on("console", on_console)
    page.on("request", on_request)
    page.on("response", on_response)
    page.on("requestfailed", on_request_failed)

@app.post("/sessions")
async def create_session(browser_type: str = "chromium", headless: bool = True):
    """Create a new browser session"""
    session_id = str(uuid.uuid4())[:8]
    
    # Launch browser
    if browser_type == "chromium":
        browser = await playwright_instance.chromium.launch(headless=headless)
    elif browser_type == "firefox":
        browser = await playwright_instance.firefox.launch(headless=headless)
    elif browser_type == "webkit":
        browser = await playwright_instance.webkit.launch(headless=headless)
    else:
        raise HTTPException(400, f"Unknown browser type: {browser_type}")
    
    # Create context
    context = await browser.new_context()
    
    # Store
    browsers[session_id] = browser
    sessions[session_id] = context
    
    print(f"✓ Created session: {session_id}")
    return {"session_id": session_id, "status": "created"}

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "sessions": list(sessions.keys()),
        "count": len(sessions)
    }

@app.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    """Close a browser session"""
    if session_id not in sessions:
        raise HTTPException(404, f"Session not found: {session_id}")
    
    # Close all pages in this session
    pages_to_close = [pid for pid, page in pages.items() if page.context == sessions[session_id]]
    for page_id in pages_to_close:
        await pages[page_id].close()
        del pages[page_id]
        if page_id in console_logs:
            del console_logs[page_id]
        if page_id in network_logs:
            del network_logs[page_id]
    
    # Close context and browser
    await sessions[session_id].close()
    await browsers[session_id].close()
    
    del sessions[session_id]
    del browsers[session_id]
    
    return {"status": "closed"}

@app.post("/sessions/{session_id}/pages")
async def create_page(session_id: str, url: Optional[str] = None):
    """Create a new page in a session"""
    if session_id not in sessions:
        raise HTTPException(404, f"Session not found: {session_id}")
    
    page_id = str(uuid.uuid4())[:8]
    page = await sessions[session_id].new_page()
    pages[page_id] = page
    
    # Set up listeners
    await setup_page_listeners(page_id, page)
    
    # Navigate if URL provided
    if url:
        await page.goto(url)
    
    print(f"✓ Created page: {page_id} in session: {session_id}")
    return {"page_id": page_id, "session_id": session_id}

@app.get("/pages/{page_id}/console")
async def get_console_logs(page_id: str, query: LogQueryRequest = LogQueryRequest()):
    """Get console logs for a page with filtering"""
    if page_id not in pages:
        raise HTTPException(404, f"Page not found: {page_id}")
    
    logs = list(console_logs[page_id])
    
    # Apply filters
    if query.types:
        logs = [log for log in logs if log["type"] in query.types]
    
    if query.since:
        logs = [log for log in logs if log["timestamp"] >= query.since]
    
    if query.until:
        logs = [log for log in logs if log["timestamp"] <= query.until]
    
    if query.text_contains:
        logs = [log for log in logs if query.text_contains.lower() in log["text"].lower()]
    
    # Apply limit
    if query.limit and len(logs) > query.limit:
        logs = logs[-query.limit:]  # Get most recent
    
    # Convert timestamps to ISO format
    for log in logs:
        if isinstance(log["timestamp"], datetime):
            log["timestamp"] = log["timestamp"].isoformat()
    
    return {
        "page_id": page_id,
        "logs": logs,
        "count": len(logs),
        "total_captured": len(console_logs[page_id])
    }

@app.get("/pages/{page_id}/network")
async def get_network_logs(page_id: str, since: Optional[datetime] = None, limit: int = 100):
    """Get network logs for a page"""
    if page_id not in pages:
        raise HTTPException(404, f"Page not found: {page_id}")
    
    logs = list(network_logs[page_id])
    
    # Apply time filter
    if since:
        logs = [log for log in logs if log["timestamp"] >= since]
    
    # Apply limit
    if len(logs) > limit:
        logs = logs[-limit:]
    
    # Convert timestamps to ISO format
    for log in logs:
        if isinstance(log["timestamp"], datetime):
            log["timestamp"] = log["timestamp"].isoformat()
    
    return {
        "page_id": page_id,
        "logs": logs,
        "count": len(logs)
    }

@app.get("/pages/{page_id}/errors")
async def get_error_logs(page_id: str, limit: int = 50):
    """Get only error-level console logs"""
    if page_id not in pages:
        raise HTTPException(404, f"Page not found: {page_id}")
    
    # Filter for errors
    error_logs = [
        log for log in console_logs[page_id] 
        if log["type"] in ["error", "warning"]
    ]
    
    # Apply limit
    if len(error_logs) > limit:
        error_logs = error_logs[-limit:]
    
    # Convert timestamps
    for log in error_logs:
        if isinstance(log["timestamp"], datetime):
            log["timestamp"] = log["timestamp"].isoformat()
    
    return {
        "page_id": page_id,
        "errors": error_logs,
        "count": len(error_logs)
    }

@app.post("/pages/{page_id}/command")
async def execute_command(page_id: str, request: CommandRequest):
    """Execute a command on a page"""
    if page_id not in pages:
        raise HTTPException(404, f"Page not found: {page_id}")
    
    page = pages[page_id]
    command = request.command
    args = request.args
    kwargs = request.kwargs
    
    print(f"→ Executing: {command} on page {page_id}")
    
    try:
        # Handle different commands
        if command == "goto":
            result = await page.goto(*args, **kwargs)
            return {"status": "success", "url": page.url}
        
        elif command == "click":
            await page.click(*args, **kwargs)
            return {"status": "success"}
        
        elif command == "fill":
            await page.fill(*args, **kwargs)
            return {"status": "success"}
        
        elif command == "screenshot":
            screenshot_data = await page.screenshot(**kwargs)
            # Save to file if path provided
            if "path" in kwargs:
                return {"status": "success", "path": kwargs["path"]}
            else:
                # Return base64 encoded
                return {
                    "status": "success",
                    "data": base64.b64encode(screenshot_data).decode()
                }
        
        elif command == "evaluate":
            result = await page.evaluate(*args, **kwargs)
            return {"status": "success", "result": result}
        
        elif command == "wait":
            if args and isinstance(args[0], (int, float)):
                await page.wait_for_timeout(args[0])
            else:
                await page.wait_for_load_state(*args, **kwargs)
            return {"status": "success"}
        
        elif command == "get_info":
            info = {
                "url": page.url,
                "title": await page.title(),
                "viewport": page.viewport_size,
            }
            return {"status": "success", "info": info}
        
        elif command == "wait_for_selector":
            await page.wait_for_selector(*args, **kwargs)
            return {"status": "success"}
        
        elif command == "select_option":
            await page.select_option(*args, **kwargs)
            return {"status": "success"}
        
        elif command == "press":
            await page.press(*args, **kwargs)
            return {"status": "success"}
        
        elif command == "type":
            await page.type(*args, **kwargs)
            return {"status": "success"}
        
        else:
            # Generic command execution
            method = getattr(page, command, None)
            if method:
                result = await method(*args, **kwargs)
                return {"status": "success", "result": str(result) if result else None}
            else:
                raise HTTPException(400, f"Unknown command: {command}")
    
    except Exception as e:
        print(f"✗ Error executing {command}: {e}")
        raise HTTPException(500, f"Command failed: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "sessions": len(sessions),
        "pages": len(pages),
        "version": "2.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Enhanced Browser Server with Console Capture...")
    print("Server will run at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)