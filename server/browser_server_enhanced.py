#!/usr/bin/env python3
"""
Enhanced Persistent Browser Server with Console Log Capture
Maintains browser sessions across requests and captures console logs
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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
import io
from PIL import Image

# Import the modular tools
from screenshot_to_gemini_bb_json import detect_bounding_boxes
from bbox_visualizer import visualize

app = FastAPI(title="Enhanced Browser Server", version="2.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage
browsers: Dict[str, Browser] = {}
sessions: Dict[str, BrowserContext] = {}
pages: Dict[str, Page] = {}
console_logs: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))  # Max 1000 logs per page
network_logs: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))   # Max 500 network logs per page
session_metadata: Dict[str, Dict] = {}  # Store metadata about sessions

# Request/Response models
class CreateSessionRequest(BaseModel):
    browser_type: str = "chromium"
    headless: bool = True

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

class NavigateRequest(BaseModel):
    session_id: str
    page_id: str
    url: str

class SimpleCommandRequest(BaseModel):
    session_id: str
    page_id: str
    command: str

class BoundingBoxRequest(BaseModel):
    screenshot: str  # Base64 encoded image or file path
    api_key: str
    prompt: Optional[str] = None

class VisualizeRequest(BaseModel):
    screenshot: str  # Base64 encoded image
    bounding_boxes: List[List[int]]  # Array of [ymin, xmin, ymax, xmax]
    mode: Literal['bbox', 'crosshair'] = 'bbox'

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
async def create_session(request: CreateSessionRequest):
    """Create a new browser session"""
    session_id = str(uuid.uuid4())[:8]
    
    # Launch browser
    if request.browser_type == "chromium":
        browser = await playwright_instance.chromium.launch(headless=request.headless)
    elif request.browser_type == "firefox":
        browser = await playwright_instance.firefox.launch(headless=request.headless)
    elif request.browser_type == "webkit":
        browser = await playwright_instance.webkit.launch(headless=request.headless)
    else:
        raise HTTPException(400, f"Unknown browser type: {request.browser_type}")
    
    # Create context
    context = await browser.new_context()
    
    # Store
    browsers[session_id] = browser
    sessions[session_id] = context
    session_metadata[session_id] = {
        "created_at": datetime.now().isoformat(),
        "browser_type": request.browser_type,
        "headless": request.headless
    }
    
    print(f"✓ Created session: {session_id} (headless={request.headless})")
    return {"session_id": session_id, "status": "created", "headless": request.headless}

@app.get("/sessions")
async def list_sessions():
    """List all active sessions with detailed information"""
    detailed_sessions = []
    
    for session_id, context in sessions.items():
        session_info = {
            "session_id": session_id,
            "created_at": session_metadata.get(session_id, {}).get("created_at", "Unknown"),
            "headless": session_metadata.get(session_id, {}).get("headless", True),
            "browser_type": session_metadata.get(session_id, {}).get("browser_type", "chromium"),
            "pages": []
        }
        
        # Get pages for this session
        for page_id, page in pages.items():
            if page.context == context:
                try:
                    page_info = {
                        "page_id": page_id,
                        "url": page.url,
                        "title": await page.title() if not page.is_closed() else "Closed"
                    }
                    session_info["pages"].append(page_info)
                except:
                    # Page might be closed or inaccessible
                    page_info = {
                        "page_id": page_id,
                        "url": "Unknown",
                        "title": "Error accessing page"
                    }
                    session_info["pages"].append(page_info)
        
        detailed_sessions.append(session_info)
    
    return {
        "sessions": detailed_sessions,
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
    if session_id in session_metadata:
        del session_metadata[session_id]
    
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
            # Check if this is a position-based click
            if not args and "position" in kwargs:
                # Extract x, y from position dict
                position = kwargs["position"]
                x = position.get("x", position.get("X"))
                y = position.get("y", position.get("Y"))
                if x is not None and y is not None:
                    # Use page.mouse.click for position-based clicks
                    await page.mouse.click(float(x), float(y))
                    return {"status": "success", "message": f"Clicked at position ({x}, {y})"}
            # Regular selector-based click
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

@app.post("/command")
async def execute_simple_command(request: SimpleCommandRequest):
    """Execute a Playwright command with session and page IDs in the request body"""
    if request.session_id not in sessions:
        raise HTTPException(404, f"Session not found: {request.session_id}")
    if request.page_id not in pages:
        raise HTTPException(404, f"Page not found: {request.page_id}")
    
    page = pages[request.page_id]
    command = request.command.strip()
    
    try:
        # Parse and execute Playwright commands directly
        # Remove 'await' prefix if present
        if command.startswith('await '):
            command = command[6:]
        
        # Handle common Playwright commands
        if command.startswith('page.click('):
            # Extract the argument from page.click(...)
            arg_str = command[11:-1]  # Remove 'page.click(' and ')'
            
            # Check if it's a position-based click
            if '{position:' in arg_str:
                # Parse position coordinates (supports float values and different formats)
                import re
                # More flexible regex to handle decimals and different spacing
                match = re.search(r'x:\s*([\d.]+).*?y:\s*([\d.]+)', arg_str, re.IGNORECASE)
                if match:
                    x = float(match.group(1))
                    y = float(match.group(2))
                    # Use page.mouse.click for position-based clicks
                    await page.mouse.click(x, y)
                    return {"status": "success", "message": f"Clicked at position ({x}, {y})"}
            else:
                # It's a selector-based click
                selector = arg_str.strip().strip('"\'')
                await page.click(selector)
                return {"status": "success", "message": f"Clicked selector: {selector}"}
        
        elif command.startswith('page.type('):
            # Extract arguments - could be just text or selector + text
            arg_str = command[10:-1]  # Remove 'page.type(' and ')'
            
            # Check if there's a comma (indicating selector + text)
            if ',' in arg_str:
                parts = arg_str.split(',', 1)
                selector = parts[0].strip().strip('"\'')
                text = parts[1].strip().strip('"\'')
                await page.type(selector, text)
                return {"status": "success", "message": f"Typed '{text}' into {selector}"}
            else:
                # Just text, type into currently focused element
                text = arg_str.strip().strip('"\'')
                await page.keyboard.type(text)
                return {"status": "success", "message": f"Typed: {text}"}
        
        elif command.startswith('page.fill('):
            # Extract selector and value
            arg_str = command[10:-1]  # Remove 'page.fill(' and ')'
            parts = arg_str.split(',', 1)
            if len(parts) == 2:
                selector = parts[0].strip().strip('"\'')
                value = parts[1].strip().strip('"\'')
                await page.fill(selector, value)
                return {"status": "success", "message": f"Filled {selector} with {value}"}
        
        elif command.startswith('page.goto('):
            # Extract URL
            arg_str = command[10:-1]  # Remove 'page.goto(' and ')'
            url = arg_str.strip().strip('"\'')
            await page.goto(url)
            return {"status": "success", "message": f"Navigated to {url}", "url": page.url}
        
        elif command.startswith('page.screenshot('):
            # Take screenshot
            screenshot_data = await page.screenshot()
            return {
                "status": "success",
                "message": "Screenshot taken",
                "screenshot": base64.b64encode(screenshot_data).decode()
            }
        
        elif command.startswith('page.press('):
            # Extract key to press
            arg_str = command[11:-1]  # Remove 'page.press(' and ')'
            key = arg_str.strip().strip('"\'')
            await page.press(key)
            return {"status": "success", "message": f"Pressed key: {key}"}
        
        elif command.startswith('page.select_option('):
            # Extract selector and value
            arg_str = command[19:-1]  # Remove 'page.select_option(' and ')'
            parts = arg_str.split(',', 1)
            if len(parts) == 2:
                selector = parts[0].strip().strip('"\'')
                value = parts[1].strip().strip('"\'')
                await page.select_option(selector, value)
                return {"status": "success", "message": f"Selected {value} in {selector}"}
        
        elif command.startswith('page.wait_for_selector('):
            # Extract selector
            arg_str = command[23:-1]  # Remove 'page.wait_for_selector(' and ')'
            selector = arg_str.strip().strip('"\'')
            await page.wait_for_selector(selector)
            return {"status": "success", "message": f"Found selector: {selector}"}
        
        elif command.startswith('page.wait_for_timeout('):
            # Extract timeout
            arg_str = command[22:-1]  # Remove 'page.wait_for_timeout(' and ')'
            timeout = int(arg_str.strip())
            await page.wait_for_timeout(timeout)
            return {"status": "success", "message": f"Waited {timeout}ms"}
        
        elif command.startswith('page.mouse.click('):
            # Direct mouse click command
            arg_str = command[17:-1]  # Remove 'page.mouse.click(' and ')'
            parts = arg_str.split(',')
            if len(parts) >= 2:
                x = float(parts[0].strip())
                y = float(parts[1].strip())
                await page.mouse.click(x, y)
                return {"status": "success", "message": f"Mouse clicked at position ({x}, {y})"}
        
        elif command == 'page.reload()':
            await page.reload()
            return {"status": "success", "message": "Page reloaded"}
        
        elif command == 'page.go_back()':
            await page.go_back()
            return {"status": "success", "message": "Navigated back"}
        
        elif command == 'page.go_forward()':
            await page.go_forward()
            return {"status": "success", "message": "Navigated forward"}
        
        else:
            # Fallback: try to evaluate as JavaScript (for backward compatibility)
            # Wrap in async function to support await
            wrapped_command = f"(async () => {{ return {command} }})()"
            result = await page.evaluate(wrapped_command)
            return {
                "status": "success",
                "result": result,
                "message": "Executed as JavaScript"
            }
    
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "sessions": len(sessions),
        "pages": len(pages),
        "version": "2.0"
    }

@app.get("/get_screenshot/{session_id}/{page_id}")
async def get_screenshot(session_id: str, page_id: str):
    """Get screenshot for a session/page"""
    if session_id not in sessions:
        raise HTTPException(404, f"Session not found: {session_id}")
    if page_id not in pages:
        raise HTTPException(404, f"Page not found: {page_id}")
    
    try:
        page = pages[page_id]
        screenshot_data = await page.screenshot()
        
        # Return base64 encoded image
        return {
            "status": "success",
            "screenshot": base64.b64encode(screenshot_data).decode(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to take screenshot: {str(e)}")

@app.post("/navigate_to")
async def navigate_to(request: NavigateRequest):
    """Navigate to a URL"""
    if request.session_id not in sessions:
        raise HTTPException(404, f"Session not found: {request.session_id}")
    if request.page_id not in pages:
        raise HTTPException(404, f"Page not found: {request.page_id}")
    
    try:
        page = pages[request.page_id]
        await page.goto(request.url)
        
        return {
            "status": "success",
            "url": page.url,
            "title": await page.title()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to navigate: {str(e)}")

@app.get("/sessions/{session_id}/pages/{page_id}/url")
async def get_page_url(session_id: str, page_id: str):
    """Get the current URL of a page"""
    if session_id not in sessions:
        raise HTTPException(404, f"Session not found: {session_id}")
    if page_id not in pages:
        raise HTTPException(404, f"Page not found: {page_id}")
    
    try:
        page = pages[page_id]
        return {
            "url": page.url,
            "title": await page.title() if page.url else None
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get URL: {str(e)}")

@app.post("/screenshot_to_bounding_boxes")
async def screenshot_to_bounding_boxes(request: BoundingBoxRequest):
    """Send screenshot to Gemini Vision API and extract bounding boxes"""
    try:
        # Handle base64 encoded screenshot
        if request.screenshot.startswith('data:image'):
            # Extract base64 data from data URL
            base64_data = request.screenshot.split(',')[1]
        else:
            base64_data = request.screenshot
        
        # Decode and save temporarily
        screenshot_data = base64.b64decode(base64_data)
        temp_path = Path("/tmp") / f"temp_screenshot_{uuid.uuid4().hex}.png"
        
        with open(temp_path, 'wb') as f:
            f.write(screenshot_data)
        
        try:
            # Use the imported function
            result = await detect_bounding_boxes(
                str(temp_path),
                request.api_key,
                save_json=False,
                prompt=request.prompt
            )
            
            return {
                "status": "success",
                "raw_response": result['raw_response'],
                "coordinates": result['coordinates'],
                "count": len(result['coordinates'])
            }
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
                
    except Exception as e:
        raise HTTPException(500, f"Failed to detect bounding boxes: {str(e)}")

@app.post("/visualize_bounding_boxes")
async def visualize_bounding_boxes(request: VisualizeRequest):
    """Visualize bounding boxes on a screenshot"""
    try:
        # Decode base64 screenshot
        if request.screenshot.startswith('data:image'):
            base64_data = request.screenshot.split(',')[1]
        else:
            base64_data = request.screenshot
            
        screenshot_data = base64.b64decode(base64_data)
        temp_screenshot = Path("/tmp") / f"temp_screenshot_{uuid.uuid4().hex}.png"
        
        with open(temp_screenshot, 'wb') as f:
            f.write(screenshot_data)
        
        try:
            # Prepare JSON data for visualization
            json_data = {
                "coordinates": request.bounding_boxes
            }
            
            # Create visualization
            output_path = visualize(
                str(temp_screenshot),
                json_data=json_data,
                mode=request.mode,
                output_path=None
            )
            
            # Read the result and encode as base64
            with open(output_path, 'rb') as f:
                result_data = f.read()
            
            result_base64 = base64.b64encode(result_data).decode()
            
            # Clean up output file
            Path(output_path).unlink()
            
            return {
                "status": "success",
                "visualized_image": f"data:image/png;base64,{result_base64}",
                "mode": request.mode
            }
            
        finally:
            # Clean up temp file
            if temp_screenshot.exists():
                temp_screenshot.unlink()
                
    except Exception as e:
        raise HTTPException(500, f"Failed to visualize: {str(e)}")

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Add route for the UI
@app.get("/ui")
async def ui():
    """Serve the UI"""
    ui_file = static_dir / "index.html"
    if not ui_file.exists():
        raise HTTPException(404, "UI not found. Please create /static/index.html")
    return FileResponse(str(ui_file))

@app.get("/ui-enhanced")
async def ui_enhanced():
    """Serve the enhanced UI"""
    ui_file = static_dir / "index_enhanced.html"
    if not ui_file.exists():
        raise HTTPException(404, "Enhanced UI not found. Please create /static/index_enhanced.html")
    return FileResponse(str(ui_file))

if __name__ == "__main__":
    import uvicorn
    print("Starting Enhanced Browser Server with Console Capture...")
    print("Server will run at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Browser UI at: http://localhost:8000/ui")
    uvicorn.run(app, host="0.0.0.0", port=8000)