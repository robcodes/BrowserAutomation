# Enhanced Browser Server Quick Start Guide

## Overview
The Enhanced Browser Server (v2.0) adds console log and network capture to the persistent browser architecture, enabling powerful debugging capabilities.

## Starting the Server

```bash
# Start the enhanced server
python3 browser_server_enhanced.py > browser_server.log 2>&1 &

# Check it's running
curl http://localhost:8000/
```

## Basic Usage

```python
from browser_client_enhanced import EnhancedBrowserClient
import asyncio

async def main():
    client = EnhancedBrowserClient()
    
    # Create session and navigate
    await client.create_session(headless=False)
    await client.new_page("https://example.com")
    
    # Perform actions
    await client.fill('input[name="q"]', 'search term')
    await client.click('button[type="submit"]')
    
    # Check for errors after action
    await client.print_recent_errors()
    
    # Get all console logs
    logs = await client.get_console_logs()
    print(f"Total logs: {logs['count']}")
    
    # Clean up
    await client.close_session()

asyncio.run(main())
```

## Debugging Failed Actions

```python
from browser_client_enhanced import debug_failed_action

# When something doesn't work as expected
try:
    await client.click('button#submit')
except Exception as e:
    # Automatic debugging helper
    await debug_failed_action(client, "Submit button click")
```

## Console Log Queries

### Get Specific Log Types
```python
# Only errors and warnings
errors = await client.get_errors()

# Only specific types
info_logs = await client.get_console_logs(types=["info", "log"])
```

### Time-Based Queries
```python
from datetime import datetime, timedelta

# Logs from last 10 seconds
recent = await client.get_console_logs(
    since=datetime.now() - timedelta(seconds=10)
)

# Logs within a time range
logs = await client.get_console_logs(
    since=start_time,
    until=end_time
)
```

### Text Search
```python
# Find logs mentioning "api"
api_logs = await client.get_console_logs(text_contains="api")

# Find logs with "error" or "failed"
error_logs = await client.get_console_logs(text_contains="error")
```

## Network Monitoring

```python
# Get recent network activity
network = await client.get_network_logs()

# Find failed requests
failures = [
    log for log in network["logs"] 
    if log.get("failure") or log.get("status", 0) >= 400
]

# Check specific endpoints
api_calls = [
    log for log in network["logs"]
    if "/api/" in log["url"]
]
```

## Common Debugging Patterns

### 1. Button Click Not Working
```python
# Click attempt
try:
    await client.click('button')
except:
    # Check what prevented it
    errors = await client.get_errors()
    if errors["errors"]:
        # Likely JavaScript error preventing click
        for e in errors["errors"]:
            print(f"JS Error: {e['text']}")
```

### 2. Form Submission Failing
```python
# Before submission
before_submit = datetime.now()

# Submit form
await client.click('button[type="submit"]')
await client.wait(2000)

# Check what happened
logs = await client.get_console_logs(since=before_submit)
network = await client.get_network_logs(since=before_submit)

# Look for API errors
api_errors = [
    log for log in network["logs"]
    if log["type"] == "response" and log.get("status", 0) >= 400
]
```

### 3. Page Not Loading Correctly
```python
# Navigate
await client.goto("https://example.com")
await client.wait(3000)

# Check all issues
issues = await client.check_for_issues()
if issues:
    # Detailed analysis
    errors = await client.get_errors()
    network = await client.get_network_logs()
    
    print(f"Found {len(errors['errors'])} JS errors")
    print(f"Found {len([l for l in network['logs'] if 'failure' in l])} failed requests")
```

## API Reference

### Console Log Endpoints
- `GET /pages/{page_id}/console` - Get console logs with filters
- `GET /pages/{page_id}/errors` - Get only errors/warnings
- `GET /pages/{page_id}/network` - Get network logs

### Query Parameters
- `types`: List of log types to include
- `since`: ISO timestamp for start time
- `until`: ISO timestamp for end time  
- `text_contains`: Text to search for in logs
- `limit`: Maximum logs to return

## Tips

1. **Always check console after failures** - JavaScript errors are often the root cause
2. **Monitor network for API issues** - 401/403/500 errors explain many failures
3. **Use time-based queries** - Get logs around specific actions
4. **Save session for analysis** - Can reconnect and analyze logs later
5. **Check for patterns** - Search for specific error messages across logs

## Example: Full Debugging Session

```python
async def debug_website_interaction():
    client = EnhancedBrowserClient()
    
    try:
        # Setup
        await client.create_session(headless=False)
        await client.new_page("https://complex-site.com")
        
        # Action with debugging
        action_time = datetime.now()
        try:
            await client.fill('#username', 'testuser')
            await client.fill('#password', 'testpass')
            await client.click('#login-button')
        except Exception as e:
            print(f"Action failed: {e}")
            
            # Get all debugging info
            errors = await client.get_errors()
            logs_since_action = await client.get_console_logs(since=action_time)
            network_since_action = await client.get_network_logs(since=action_time)
            
            # Analyze
            print(f"\n🔍 Debugging Info:")
            print(f"  JS Errors: {len(errors['errors'])}")
            print(f"  Console logs since action: {len(logs_since_action['logs'])}")
            print(f"  Network requests: {len(network_since_action['logs'])}")
            
            # Find root cause
            for error in errors['errors']:
                if action_time <= datetime.fromisoformat(error['timestamp']):
                    print(f"\n❌ Error during action: {error['text']}")
            
            # Check API responses
            for log in network_since_action['logs']:
                if log['type'] == 'response' and log.get('status', 0) >= 400:
                    print(f"\n🌐 API Error: {log['method']} {log['url']} -> {log['status']}")
        
        # Screenshot for visual confirmation
        await client.screenshot("debug_result.png")
        
    finally:
        await client.close_session()

# Run it
asyncio.run(debug_website_interaction())
```