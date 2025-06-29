# Browser Automation Best Practices Guide

## 🎯 Core Principles

### 1. **Act Like a Human User**
- Take screenshots at EVERY step
- Verify each action worked before proceeding
- If something looks wrong, STOP - don't blindly continue
- Check form states match expectations

### 2. **Session Persistence**
- Use external FastAPI server to maintain browser sessions
- Store session IDs for reconnection between executions
- Browser state survives between Claude code blocks

## 🔍 Element Discovery Strategy

### Finding Elements (in order of reliability)
1. **Specific IDs/Names**: `#userInput`, `input[name="email"]`
2. **Unique attributes**: `[placeholder*="Enter"]`, `[type="submit"]`
3. **Text content**: `button:contains('Sign In')`
4. **Bounding box**: Elements at specific positions
5. **Multiple selectors**: Try several approaches

### Hidden Element Traps
- **Shadow DOM**: Elements inside web components are invisible to normal queries
- **Iframes**: Must switch context - check if same-origin first
- **Off-screen**: Use `offsetParent !== null` to verify visibility
- **Dynamic loading**: Elements may appear after delays

## 📝 Form Filling Protocol

### 1. Analyze First
```javascript
// Get ALL inputs including hidden ones
const inputs = form.querySelectorAll('input');
inputs.forEach(input => {
    console.log({
        type: input.type,
        required: input.required,
        value: input.value,
        valid: input.checkValidity()
    });
});
```

### 2. Fill Properly
```javascript
// Clear → Type → Dispatch events
input.focus();
input.value = '';
input.value = 'new value';
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
input.blur();
```

### 3. Validate Before Submit
- Check `form.checkValidity()` returns true
- Verify button is NOT disabled
- Look for validation error messages
- Take screenshot to confirm

## 🚨 Debugging Tools

### 1. Console Logs
- Capture all console messages with timestamps
- Errors often reveal root causes (401 auth errors, etc.)
- Add to server: `page.on('console', msg => ...)`

### 2. Network Monitoring
- Track API calls and responses
- Look for failed requests (4xx, 5xx status codes)
- Monitor authentication endpoints

### 3. Visual Verification
- Screenshot before/after EVERY action
- Save to organized folders with descriptive names
- Compare expected vs actual states

## 🏗️ Architecture Pattern

### Server (browser_server_enhanced.py)
```python
# Persistent browser management
sessions = {}  # Long-lived browser instances
console_logs = defaultdict(deque)  # Debugging data
network_logs = defaultdict(deque)  # API monitoring
```

### Client Usage
```python
# 1. Connect to session
client = EnhancedBrowserClient()
await client.connect_session(session_id)

# 2. Take screenshot first
await client.screenshot("step1_before.png")

# 3. Perform action
result = await client.evaluate("...")

# 4. Verify it worked
if not result['success']:
    print("❌ Action failed, stopping")
    return

# 5. Screenshot after
await client.screenshot("step2_after.png")
```

## ⚡ Quick Fixes for Common Issues

| Problem | Solution |
|---------|----------|
| Can't find element | Check iframes, shadow DOM, wait for load |
| Form won't submit | Find ALL required fields, check validation |
| Button stays disabled | Fill all fields, trigger proper events |
| Cross-origin iframe | Can't access - need different approach |
| Lost session | Store session IDs in JSON for reconnection |

## 🔐 Authentication Flows

1. **Find login trigger** (profile icon, login button)
2. **Handle modals/iframes** (check same-origin)
3. **Fill ALL fields** (username AND password)
4. **Validate before submit** (form.checkValidity())
5. **Wait for redirect** (check URL change, welcome message)
6. **Close modals properly** (X button, backdrop click)

## 📋 Pre-Flight Checklist

Before starting automation:
- [ ] Install tools: `playwright`, `httpx`, `fastapi`
- [ ] Start browser server
- [ ] Create screenshots folder
- [ ] Enable console/network logging
- [ ] Plan step-by-step approach
- [ ] Prepare validation checks

## 🎭 Playwright-Specific Tips

- Use `page.wait_for_load_state()` after navigation
- `page.frame()` for iframe access (same-origin only)
- `page.evaluate()` for complex DOM operations
- Headless mode may behave differently than headed

## 🚀 Workflow Template

```python
# 1. Setup
client = EnhancedBrowserClient()
session_id = await client.create_session()

# 2. Navigate
await client.goto("https://example.com")
await client.screenshot("01_loaded.png")

# 3. Find elements
elements = await client.evaluate("""
    () => ({
        form: document.querySelector('form') !== null,
        inputs: Array.from(document.querySelectorAll('input')).length
    })
""")

# 4. Fill forms with validation
if not elements['form']:
    print("❌ No form found")
    return

# 5. Submit and verify
# ... continue pattern
```

## 🔑 Key Takeaways

1. **Screenshot everything** - Visual proof prevents confusion
2. **Validate constantly** - Don't assume actions succeeded
3. **Debug systematically** - Console → Network → DOM inspection
4. **Handle failures gracefully** - Stop when things go wrong
5. **Document patterns** - Save working code for reuse