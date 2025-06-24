# Browser Automation Architecture

## 🚨 Script Organization: Step-by-Step Pattern

**ALL browser automation MUST use the step-by-step modular pattern.**
See `/scripts/fuzzycode_steps/` for the reference implementation.

## The Breakthrough
Claude's limitation: Can't maintain state between code executions.
Solution: External FastAPI server maintains browser state.

## Key Components

### 1. Enhanced Server (browser_server_enhanced.py)
- Persistent browser instances with UUID-based sessions
- Console log capture (all JavaScript errors/warnings/logs)
- Network request/response monitoring
- Deque-based log storage with configurable limits
- REST API for browser control

### 2. Enhanced Client (browser_client_enhanced.py)
- Async HTTP client for server communication
- Debugging helpers: `print_recent_errors()`, `debug_failed_action()`
- Time-based and pattern-based log queries
- Session reconnection capabilities

### 3. Session Management
- UUID-based session identification
- Multiple concurrent browser sessions
- Page management within sessions
- Persistent state across Claude executions

## Critical Patterns Discovered

### Form Handling
- Direct array access pattern: `inputs[0]`, `inputs[1]`
- More reliable than complex CSS selectors
- Handles dynamic form generation

### Console Logging
- Revealed hidden failures (401 authentication errors)
- JavaScript errors that don't show visually
- API call failures and responses

### Modal/Overlay Management
- Page reload can reset UI while maintaining session
- Backdrop clicking sometimes works
- X button detection can be unreliable

### Iframe Access
- Same-origin iframes ARE accessible via contentDocument
- Cross-origin iframes completely blocked
- Check accessibility before attempting manipulation

## Architecture Diagram

```
┌─────────────────┐     HTTP/REST      ┌──────────────────┐
│                 │ ◄─────────────────► │                  │
│  Claude Code    │                     │ Browser Server   │
│  (Client)       │                     │ (FastAPI)        │
└─────────────────┘                     └──────────────────┘
        │                                        │
        │                                        │
        ▼                                        ▼
┌─────────────────┐                     ┌──────────────────┐
│ Session Files   │                     │ Playwright       │
│ (.json)         │                     │ Browser Instance │
└─────────────────┘                     └──────────────────┘
```

## Why This Architecture?

1. **Persistence**: Browser state survives between Claude executions
2. **Debugging**: Console and network logs reveal hidden issues
3. **Flexibility**: Multiple sessions, pages, and browsers
4. **Reliability**: REST API more stable than direct Playwright control