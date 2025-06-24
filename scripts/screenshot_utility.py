#!/usr/bin/env python3
"""
Simple utility for taking screenshots of websites
"""
from playwright_agent import run_agent, navigate_and_screenshot
from playwright_agent_advanced import create_browser_session
import os
import sys
from datetime import datetime

def take_screenshot(url, filename=None, full_page=True, headless=True):
    """
    Take a screenshot of a URL and save it to the screenshots folder
    
    Args:
        url: The URL to screenshot
        filename: Optional filename (defaults to domain_timestamp.png)
        full_page: Whether to capture full page (default True)
        headless: Whether to run browser in headless mode (default True)
    """
    # Create screenshots directory if it doesn't exist
    os.makedirs('/home/ubuntu/screenshots', exist_ok=True)
    
    # Generate filename if not provided
    if not filename:
        domain = url.replace('https://', '').replace('http://', '').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{domain}_{timestamp}.png"
    
    filepath = os.path.join('/home/ubuntu/screenshots', filename)
    
    # Take screenshot using the basic agent
    results = navigate_and_screenshot(url, filepath, headless=headless)
    
    if results[-1].get('success'):
        print(f"Screenshot saved to: {filepath}")
        return filepath
    else:
        print(f"Failed to take screenshot: {results}")
        return None

def take_screenshot_advanced(url, filename=None, wait_time=2000):
    """
    Take a screenshot with advanced options (waits for dynamic content)
    """
    os.makedirs('/home/ubuntu/screenshots', exist_ok=True)
    
    if not filename:
        domain = url.replace('https://', '').replace('http://', '').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{domain}_{timestamp}_advanced.png"
    
    filepath = os.path.join('/home/ubuntu/screenshots', filename)
    
    # Use advanced agent for more control
    agent = create_browser_session(headless=True)
    try:
        # Navigate to URL
        agent.page.goto(url)
        
        # Wait for network idle and additional time for dynamic content
        agent.page.wait_for_load_state('networkidle')
        agent.page.wait_for_timeout(wait_time)
        
        # Take screenshot
        agent.page.screenshot(path=filepath, full_page=True)
        print(f"Advanced screenshot saved to: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None
    finally:
        agent.stop()

if __name__ == "__main__":
    # Command line usage
    if len(sys.argv) < 2:
        print("Usage: python screenshot_utility.py <URL> [filename]")
        print("Example: python screenshot_utility.py https://example.com")
        print("         python screenshot_utility.py https://google.com google.png")
        sys.exit(1)
    
    url = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Ensure virtual display is set
    if not os.environ.get('DISPLAY'):
        os.environ['DISPLAY'] = ':99'
    
    take_screenshot(url, filename)