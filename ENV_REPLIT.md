# Replit Environment Configuration

This document contains Replit-specific instructions and configurations for the browser automation project.

## Environment Detection
You are running in Replit if:
- Environment variables contain "REPL" or "REPLIT" (e.g., `REPLIT_CLUSTER`, `REPL_ID`)
- Working directory is `/home/runner/workspace`
- User is `runner`

## Replit-Specific Setup

### Package Management
Replit uses Nix for package management. Dependencies are configured in `replit.nix`.

### Browser Setup (Playwright)
See `PLAYWRIGHT_ON_REPLIT_SETUP_GUIDE.md` for detailed instructions on setting up Playwright with browsers.

Key points:
- Use the nix-provided Chromium from `PLAYWRIGHT_BROWSERS_PATH`
- Set `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1`
- Browser launch args must include `--no-sandbox`, `--disable-setuid-sandbox`

### Python Dependencies
Install via pip:
```bash
pip install -r config/requirements.txt
pip install pillow  # Often needed but not in requirements
```

### Server Configuration
The browser server binds to `0.0.0.0:8000` by default. Access through:
- Replit's preview pane
- The provided Replit URL (shown in the webview)

### File Paths
- Working directory: `/home/runner/workspace`
- Nix store browsers: `/nix/store/*/playwright-browsers-chromium/`
- Python packages: `~/.pythonlibs/`

### Limitations
- No sudo access
- Limited system libraries
- Must use nix packages for system dependencies
- Shared memory constraints (use `--disable-dev-shm-usage`)

### Running the Server
```bash
python server/browser_server_enhanced.py
```

The server will be accessible through Replit's web preview.

### Environment Variables
Key Replit environment variables:
- `REPLIT_CLUSTER` - Replit cluster identifier
- `REPL_ID` - Unique repl identifier
- `REPL_OWNER` - Owner of the repl
- `PLAYWRIGHT_BROWSERS_PATH` - Set by replit.nix for browser location

### Troubleshooting
1. **Browser won't launch**: Check `PLAYWRIGHT_BROWSERS_PATH` and use the test script
2. **Missing system libraries**: Add to `replit.nix` deps section
3. **Server not accessible**: Use the Replit-provided URL, not localhost
4. **Import errors**: Install missing packages with pip

### Best Practices
1. Always use `replit.nix` for system dependencies
2. Test browser functionality with `test_playwright_browser.py`
3. Use environment variables for configuration
4. Monitor the Shell tab for server output