#!/usr/bin/env python3
"""
Proof of Concept: Persistent Browser Server
A simple implementation to demonstrate the concept
"""
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from playwright.async_api import async_playwright
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, Any
import uvicorn

# Models
class CommandRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}

class SessionInfo(BaseModel):
    session_id: str
    browser_type: str
    created_at: str
    pages: list

# Global browser manager
class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.sessions: Dict[str, Dict] = {}
        self.pages: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize playwright"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            print("✓ Playwright initialized")
    
    async def create_session(self, browser_type: str = "chromium") -> str:
        """Create a new browser session"""
        async with self._lock:
            await self.initialize()
            
            session_id = str(uuid.uuid4())[:8]  # Short ID for demo
            
            # Launch browser
            if browser_type == "chromium":
                browser = await self.playwright.chromium.launch(headless=True)
            elif browser_type == "firefox":
                browser = await self.playwright.firefox.launch(headless=True)
            else:
                browser = await self.playwright.webkit.launch(headless=True)
            
            self.sessions[session_id] = {
                "browser": browser,
                "browser_type": browser_type,
                "created_at": datetime.now().isoformat(),
                "pages": []
            }
            
            print(f"✓ Created session: {session_id}")
            return session_id
    
    async def create_page(self, session_id: str, url: Optional[str] = None) -> str:
        """Create a new page in a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        async with self._lock:
            page_id = str(uuid.uuid4())[:8]
            browser = self.sessions[session_id]["browser"]
            
            # Create new page
            page = await browser.new_page()
            if url:
                await page.goto(url)
                await page.wait_for_load_state('networkidle')
            
            self.pages[page_id] = {
                "page": page,
                "session_id": session_id,
                "created_at": datetime.now().isoformat()
            }
            
            self.sessions[session_id]["pages"].append(page_id)
            print(f"✓ Created page: {page_id} in session: {session_id}")
            return page_id
    
    async def execute_command(self, page_id: str, command: CommandRequest) -> Dict:
        """Execute a command on a page"""
        if page_id not in self.pages:
            raise ValueError(f"Page {page_id} not found")
        
        page = self.pages[page_id]["page"]
        action = command.action
        params = command.params
        
        print(f"→ Executing: {action} on page {page_id}")
        
        try:
            if action == "goto":
                await page.goto(params["url"])
                await page.wait_for_load_state('networkidle')
                return {"status": "success", "url": page.url}
            
            elif action == "click":
                await page.click(params["selector"])
                return {"status": "success"}
            
            elif action == "fill":
                await page.fill(params["selector"], params["value"])
                return {"status": "success"}
            
            elif action == "screenshot":
                filename = params.get("filename", f"screenshot_{page_id}.png")
                path = f"/home/ubuntu/screenshots/{filename}"
                await page.screenshot(path=path)
                return {"status": "success", "path": path}
            
            elif action == "evaluate":
                result = await page.evaluate(params["script"])
                return {"status": "success", "result": result}
            
            elif action == "wait":
                await page.wait_for_timeout(params.get("timeout", 1000))
                return {"status": "success"}
            
            elif action == "get_info":
                info = {
                    "url": page.url,
                    "title": await page.title(),
                    "viewport": page.viewport_size
                }
                return {"status": "success", "info": info}
            
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def close_session(self, session_id: str):
        """Close a browser session"""
        if session_id in self.sessions:
            async with self._lock:
                # Close all pages
                for page_id in self.sessions[session_id]["pages"]:
                    if page_id in self.pages:
                        await self.pages[page_id]["page"].close()
                        del self.pages[page_id]
                
                # Close browser
                await self.sessions[session_id]["browser"].close()
                del self.sessions[session_id]
                
                print(f"✓ Closed session: {session_id}")

# Create FastAPI app
app = FastAPI(title="Persistent Browser Server")
manager = BrowserManager()

# Ensure screenshots directory exists
Path("/home/ubuntu/screenshots").mkdir(exist_ok=True)

# Routes
@app.get("/")
async def root():
    return {
        "message": "Persistent Browser Server",
        "endpoints": {
            "POST /sessions": "Create new browser session",
            "GET /sessions": "List active sessions",
            "POST /sessions/{session_id}/pages": "Create new page",
            "POST /pages/{page_id}/command": "Execute command on page",
            "DELETE /sessions/{session_id}": "Close session"
        }
    }

@app.post("/sessions")
async def create_session(browser_type: str = "chromium"):
    """Create a new browser session"""
    try:
        session_id = await manager.create_session(browser_type)
        return {"session_id": session_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    sessions = []
    for sid, info in manager.sessions.items():
        sessions.append({
            "session_id": sid,
            "browser_type": info["browser_type"],
            "created_at": info["created_at"],
            "page_count": len(info["pages"])
        })
    return {"sessions": sessions}

@app.post("/sessions/{session_id}/pages")
async def create_page(session_id: str, url: Optional[str] = None):
    """Create a new page in a session"""
    try:
        page_id = await manager.create_page(session_id, url)
        return {"page_id": page_id, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pages/{page_id}/command")
async def execute_command(page_id: str, command: CommandRequest):
    """Execute a command on a page"""
    try:
        result = await manager.execute_command(page_id, command)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    """Close a browser session"""
    try:
        await manager.close_session(session_id)
        return {"status": "closed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    for session_id in list(manager.sessions.keys()):
        await manager.close_session(session_id)
    if manager.playwright:
        await manager.playwright.stop()

if __name__ == "__main__":
    print("Starting Persistent Browser Server...")
    print("Server will run at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    
    # Set display for headless mode
    os.environ['DISPLAY'] = ':99'
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000)