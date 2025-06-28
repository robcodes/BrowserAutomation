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
    nix_chromium_path = "/nix/store/hvv3n9pvjfq0x8wjw8f3igsyvlaz1ngr-playwright-browsers-chromium/chromium-1091/chrome-linux/chrome"
    if os.path.exists(nix_chromium_path):
        print(f"\n✓ Found Chromium in nix store: {nix_chromium_path}")
    
    try:
        async with async_playwright() as p:
            # Try using the chromium from nix store
            print("\nTrying to launch Chromium from nix store...")
            
            browser = await p.chromium.launch(
                executable_path=nix_chromium_path if os.path.exists(nix_chromium_path) else None,
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
        print("\nTrying alternative approaches...")
        
        # Try with the downloaded Playwright chromium
        try:
            async with async_playwright() as p:
                print("\nTrying with Playwright's downloaded Chromium...")
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--no-first-run',
                        '--disable-extensions'
                    ]
                )
                
                print("✓ Browser launched successfully with downloaded Chromium!")
                page = await browser.new_page()
                await page.goto('https://example.com')
                title = await page.title()
                print(f"✓ Successfully navigated to page. Title: {title}")
                await page.screenshot(path='test_screenshot.png')
                print("✓ Screenshot saved as test_screenshot.png")
                await browser.close()
                print("\n✅ Playwright is working with downloaded Chromium!")
                
        except Exception as e2:
            print(f"\n❌ All attempts failed. Last error: {e2}")
            print("\nDebug information:")
            print("- Check if required libraries are available: ldd $(which chromium)")
            print("- Try installing missing dependencies in replit.nix")
            print("- Consider using a remote browser service like browserless")

if __name__ == "__main__":
    asyncio.run(test_browser())