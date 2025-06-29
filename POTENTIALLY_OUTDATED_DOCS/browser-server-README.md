# Persistent Browser Server for Claude

A FastAPI-based server that maintains Playwright browser sessions between Claude's code executions, enabling persistent web automation and screenshot analysis workflows.

## Features

- **Persistent Sessions**: Browser sessions remain active between code executions
- **Multiple Browser Support**: Chromium, Firefox, and WebKit
- **Full Playwright API**: All Playwright commands available via REST API
- **Screenshot Analysis**: Take screenshots that Claude can analyze before continuing
- **Session Management**: Create, list, and manage multiple concurrent sessions
- **State Persistence**: Sessions survive server restarts (with Redis)
- **Security**: API key authentication and input validation
- **Resource Management**: Automatic cleanup of expired sessions

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the directory
2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. The server will be available at `http://localhost:8000`

### Manual Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium firefox webkit
   ```

2. Start Redis (required for session persistence):
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

3. Run the server:
   ```bash
   python browser-server-implementation.py
   ```

## Usage Examples

### Basic Usage - Create Session and Take Screenshot

```python
import asyncio
from browser_client import BrowserClient

async def main():
    # Create a browser session
    async with BrowserClient(api_key="development-key") as client:
        await client.create_session(headless=False)
        
        # Navigate to a website
        page = await client.new_page("https://example.com")
        
        # Take a screenshot for Claude to analyze
        await page.screenshot("example.png", full_page=True)
        
        # Print session info to continue later
        print(f"Session ID: {client.session_id}")
        print(f"Page ID: {list(client.pages.keys())[0]}")

asyncio.run(main())
```

### Continue Existing Session

```python
async def continue_session(session_id: str, page_id: str):
    async with BrowserClient() as client:
        # Reconnect to existing session
        await client.connect_session(session_id)
        page = await client.get_page(page_id)
        
        # Continue interacting with the page
        await page.click("button#submit")
        await page.wait_for_navigation()
        
        # Take another screenshot
        await page.screenshot("result.png")

asyncio.run(continue_session("your-session-id", "your-page-id"))
```

### Complex Automation Example

```python
async def complex_automation():
    async with BrowserClient() as client:
        await client.create_session(
            browser_type="chromium",
            headless=False,
            viewport={"width": 1920, "height": 1080}
        )
        
        # Open multiple tabs
        search_page = await client.new_page("https://google.com")
        docs_page = await client.new_page("https://docs.python.org")
        
        # Interact with search page
        await search_page.fill("input[name='q']", "Playwright Python")
        await search_page.press("input[name='q']", "Enter")
        await search_page.wait_for_navigation()
        
        # Take screenshot of search results
        await search_page.screenshot("search_results.png")
        
        # Switch to docs page and navigate
        await docs_page.click("a[href*='tutorial']")
        await docs_page.wait_for_load_state("networkidle")
        
        # Evaluate JavaScript
        toc_items = await docs_page.evaluate("""
            () => Array.from(document.querySelectorAll('.toctree-l1')).map(el => el.textContent)
        """)
        print(f"Table of contents: {toc_items}")
        
        # Get page content
        content = await docs_page.content()
        print(f"Page has {len(content)} characters")

asyncio.run(complex_automation())
```

### Form Filling and Submission

```python
async def fill_form():
    async with BrowserClient() as client:
        await client.create_session()
        page = await client.new_page("https://example-form.com")
        
        # Fill form fields
        await page.fill("#firstName", "Claude")
        await page.fill("#lastName", "Assistant")
        await page.fill("#email", "claude@example.com")
        
        # Select dropdown option
        await page.select_option("#country", "USA")
        
        # Check checkbox
        await page.check("#subscribe")
        
        # Take screenshot before submission
        await page.screenshot("form_filled.png")
        
        # Submit form
        await page.click("button[type='submit']")
        await page.wait_for_navigation()
        
        # Check for success message
        success = await page.wait_for_selector(".success-message", timeout=5000)
        if success:
            print("Form submitted successfully!")

asyncio.run(fill_form())
```

## API Endpoints

### Session Management

- `POST /sessions` - Create new session
- `GET /sessions` - List all sessions
- `GET /sessions/{session_id}` - Get session details
- `DELETE /sessions/{session_id}` - Close session

### Page Operations

- `POST /sessions/{session_id}/pages` - Create new page
- `GET /sessions/{session_id}/pages` - List pages in session
- `POST /sessions/{session_id}/pages/{page_id}/execute` - Execute command
- `POST /sessions/{session_id}/pages/{page_id}/screenshot` - Take screenshot
- `GET /sessions/{session_id}/pages/{page_id}/content` - Get page HTML
- `POST /sessions/{session_id}/pages/{page_id}/evaluate` - Evaluate JavaScript
- `DELETE /sessions/{session_id}/pages/{page_id}` - Close page

### Utility

- `GET /health` - Health check
- `GET /screenshots/{filename}` - Download screenshot

## Environment Variables

- `BROWSER_SERVER_API_KEY` - API key for authentication (default: "development-key")
- `REDIS_URL` - Redis connection URL (default: "redis://localhost:6379")
- `MAX_SESSIONS` - Maximum concurrent sessions (default: 10)
- `MAX_PAGES_PER_SESSION` - Maximum pages per session (default: 20)
- `SESSION_TIMEOUT` - Session timeout in seconds (default: 3600)
- `SCREENSHOT_DIR` - Directory for screenshots (default: "/tmp/screenshots")

## Security Considerations

1. **Authentication**: Always use a strong API key in production
2. **Network Isolation**: Run in a isolated network when possible
3. **Resource Limits**: Configure appropriate limits for your use case
4. **Input Validation**: The server validates all inputs, but always sanitize data
5. **HTTPS**: Use HTTPS in production environments

## Troubleshooting

### Browser Won't Start
- Ensure all browser dependencies are installed
- Check Docker shared memory size (increase with `shm_size`)
- Verify no conflicting browser processes

### Session Not Found
- Sessions expire after the timeout period
- Check if Redis is running and accessible
- Verify the session ID is correct

### Screenshots Not Working
- Ensure the screenshot directory exists and is writable
- Check disk space availability
- Verify the page has finished loading

### Performance Issues
- Reduce the number of concurrent sessions
- Use headless mode for better performance
- Increase server resources (CPU/Memory)

## Development

### Running Tests
```bash
pytest tests/
```

### Adding New Commands

1. Add the command handler to `CommandExecutor`:
```python
async def _new_command(self, page: Page, **kwargs):
    # Implementation
    return result
```

2. Register it in the `commands` dictionary:
```python
self.commands = {
    # ... existing commands
    "new_command": self._new_command,
}
```

3. Add client method in `RemotePage`:
```python
async def new_command(self, **kwargs):
    return await self._execute_command("new_command", **kwargs)
```

## Architecture Details

### Component Overview

1. **FastAPI Server**: Handles HTTP requests and WebSocket connections
2. **Browser Pool**: Manages browser instance lifecycle
3. **Session Manager**: Tracks active sessions and handles expiration
4. **Command Executor**: Translates API calls to Playwright commands
5. **Redis Store**: Persists session state between restarts

### Session Lifecycle

1. Client creates session → Browser and context initialized
2. Client creates pages → Pages tracked in session
3. Client executes commands → Commands run on specific pages
4. Session expires or closed → Resources cleaned up

### Error Handling

The server implements comprehensive error handling:
- Invalid commands return 400 Bad Request
- Missing sessions/pages return 404 Not Found
- Server errors return 500 with details
- All errors include descriptive messages

## Performance Optimization

1. **Browser Pooling**: Reuse browser instances when possible
2. **Lazy Loading**: Pages are created on-demand
3. **Caching**: Screenshot caching for repeated captures
4. **Connection Pooling**: Efficient Redis connection management
5. **Async Operations**: All I/O operations are asynchronous

## Monitoring

The server exposes Prometheus metrics:
- `browser_sessions_created` - Total sessions created
- `browser_sessions_active` - Currently active sessions
- `browser_command_duration_seconds` - Command execution time
- `browser_screenshot_size_bytes` - Screenshot file sizes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details