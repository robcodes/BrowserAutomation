# Playwright on Replit Setup Guide

This guide provides a complete, step-by-step process to get Playwright working with browsers on Replit. Follow these instructions exactly to avoid common pitfalls.

## Overview

Replit uses Nix package management and has restrictions that make standard Playwright installation challenging:
- No sudo access
- Missing system dependencies for browsers
- Special filesystem structure
- Pre-configured Nix environment

## Prerequisites

- A Replit account with a Python or Node.js repl
- Basic understanding of Python/Node.js

## Step-by-Step Setup

### 1. Install Playwright Python Package

```bash
pip install playwright
```

### 2. Create replit.nix Configuration

Create a `replit.nix` file in your project root with the following content:

```nix
{ pkgs }: {
  deps = [
    pkgs.nodejs_20
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.playwright-driver.browsers
    pkgs.chromium
  ];
  env = {
    PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright-driver.browsers}";
    PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = "true";
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1";
  };
}
```

### 3. Install Browser via Playwright

Run this command to download Chromium (this will fail partially but still downloads the browser):

```bash
npx playwright install chromium
```

You'll see warnings about missing system dependencies - this is expected.

### 4. Locate the Nix Chromium Path

After running the install command, check your environment variable:

```bash
echo $PLAYWRIGHT_BROWSERS_PATH
```

This will show something like: `/nix/store/hvv3n9pvjfq0x8wjw8f3igsyvlaz1ngr-playwright-browsers-chromium`

The actual Chromium executable will be at:
```
/nix/store/[hash]-playwright-browsers-chromium/chromium-[version]/chrome-linux/chrome
```

### 5. Create Test Script

Create `test_playwright_browser.py`:

```python
#!/usr/bin/env python3
"""Test script to verify Playwright can launch a browser on Replit."""

import asyncio
from playwright.async_api import async_playwright
import os

# Set environment variables to skip host validation
os.environ['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = '1'

async def test_browser():
    """Test if we can launch a browser with Playwright."""
    print("Starting Playwright browser test...")
    
    # Show environment variables
    print("\nEnvironment variables:")
    for key in ['PLAYWRIGHT_BROWSERS_PATH', 'PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS']:
        print(f"  {key}: {os.environ.get(key, 'Not set')}")
    
    # Check for nix store browsers
    browsers_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '')
    if browsers_path:
        # Find chromium directory
        import glob
        chromium_paths = glob.glob(f"{browsers_path}/chromium-*/chrome-linux/chrome")
        if chromium_paths:
            nix_chromium_path = chromium_paths[0]
            print(f"\n✓ Found Chromium in nix store: {nix_chromium_path}")
        else:
            nix_chromium_path = None
    else:
        nix_chromium_path = None
    
    try:
        async with async_playwright() as p:
            # Try using the chromium from nix store
            print("\nTrying to launch Chromium...")
            
            browser = await p.chromium.launch(
                executable_path=nix_chromium_path,
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-extensions',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            print("✓ Browser launched successfully!")
            
            # Create a new page
            page = await browser.new_page()
            
            # Navigate to a simple page
            await page.goto('https://example.com')
            title = await page.title()
            print(f"✓ Successfully navigated to page. Title: {title}")
            
            # Take a screenshot
            await page.screenshot(path='test_screenshot.png')
            print("✓ Screenshot saved as test_screenshot.png")
            
            await browser.close()
            print("\n✅ All tests passed! Playwright can run browsers on this Replit instance.")
            
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure replit.nix is loaded (restart the Repl if needed)")
        print("2. Check PLAYWRIGHT_BROWSERS_PATH environment variable")
        print("3. Verify the chromium binary exists in the nix store")

if __name__ == "__main__":
    asyncio.run(test_browser())
```

### 6. Run the Test

```bash
python test_playwright_browser.py
```

## Critical Configuration Details

### Required Browser Launch Arguments

Always use these arguments when launching Chromium on Replit:

```python
args=[
    '--no-sandbox',              # Required: Replit doesn't support sandboxing
    '--disable-setuid-sandbox',  # Required: No setuid in Replit
    '--disable-dev-shm-usage',   # Required: Limited shared memory
    '--disable-gpu',             # Recommended: No GPU in Replit
    '--no-first-run',           # Recommended: Skip first run dialogs
    '--no-zygote',              # Recommended: Single process mode
    '--disable-extensions'       # Recommended: No extensions needed
]
```

### Environment Variables

Always set these before launching browsers:

```python
os.environ['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = '1'
```

Or in your shell:
```bash
export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
```

## Working Example Code

Here's a minimal working example for web scraping:

```python
import asyncio
from playwright.async_api import async_playwright
import os

os.environ['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = '1'

async def scrape_website(url):
    # Get browser path from environment
    browsers_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH', '')
    chromium_path = None
    
    if browsers_path:
        import glob
        paths = glob.glob(f"{browsers_path}/chromium-*/chrome-linux/chrome")
        if paths:
            chromium_path = paths[0]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=chromium_path,
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        
        page = await browser.new_page()
        await page.goto(url)
        content = await page.content()
        await browser.close()
        
        return content

# Usage
content = asyncio.run(scrape_website('https://example.com'))
print(f"Page length: {len(content)} characters")
```

## Common Issues and Solutions

### Issue 1: "Host system is missing dependencies"
**Solution**: Set `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1`

### Issue 2: "Executable doesn't exist"
**Solution**: Use the chromium from nix store, not Playwright's default

### Issue 3: Browser crashes immediately
**Solution**: Ensure all required launch arguments are included, especially `--no-sandbox`

### Issue 4: "error while loading shared libraries"
**Solution**: The browser is trying to use system libraries. Make sure you're using the nix-provided chromium.

## Alternative: Firefox

If Chromium doesn't work, you can try Firefox:

1. Install Firefox from Replit packages
2. Use this code:

```python
browser = await p.firefox.launch(
    executable_path='/path/to/firefox',  # Get with: which firefox
    headless=True,
    firefox_user_prefs={
        'security.sandbox.content.level': 0,
    }
)
```

## Notes for LLMs

When helping users set up Playwright on Replit:

1. **Never suggest `sudo` commands** - Replit doesn't allow sudo
2. **Always use the nix store browsers** - Don't rely on Playwright's auto-download
3. **Environment variables are critical** - Especially `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS`
4. **Browser arguments are mandatory** - Particularly `--no-sandbox` and `--disable-setuid-sandbox`
5. **Check the PLAYWRIGHT_BROWSERS_PATH** - This is set by replit.nix and points to working browsers
6. **Use glob to find the exact chromium path** - The version number in the path changes

## Verification

To verify your setup is working:
1. Run the test script
2. Check that `test_screenshot.png` was created
3. No errors about missing libraries or dependencies

Once verified, you can use Playwright normally for web automation, testing, and scraping tasks on Replit!