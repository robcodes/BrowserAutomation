#!/usr/bin/env python3
"""
Basic Playwright Agent - Direct browser control without MCP abstraction
"""
from playwright.sync_api import sync_playwright
import json
import base64
from typing import List, Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaywrightAgent:
    """Simple agent that executes browser actions from structured commands"""
    
    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        self.headless = headless
        self.browser_type = browser_type
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        
    def start(self):
        """Initialize browser and page"""
        self.playwright = sync_playwright().start()
        
        # Select browser type
        if self.browser_type == "chromium":
            browser_launcher = self.playwright.chromium
        elif self.browser_type == "firefox":
            browser_launcher = self.playwright.firefox
        elif self.browser_type == "webkit":
            browser_launcher = self.playwright.webkit
        else:
            raise ValueError(f"Unknown browser type: {self.browser_type}")
            
        # Launch browser
        self.browser = browser_launcher.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']  # For Docker
        )
        
        # Create context with viewport
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        )
        
        # Create page
        self.page = self.context.new_page()
        logger.info(f"Started {self.browser_type} browser (headless={self.headless})")
        
    def stop(self):
        """Close browser and cleanup"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")
        
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single browser action"""
        fn_name = action.get("fn")
        args = action.get("args", [])
        kwargs = action.get("kwargs", {})
        
        # Get the function from page object
        if hasattr(self.page, fn_name):
            fn = getattr(self.page, fn_name)
            try:
                result = fn(*args, **kwargs)
                
                # Handle different return types
                if fn_name == "screenshot":
                    # Return base64 encoded screenshot
                    if isinstance(result, bytes):
                        return {
                            "success": True,
                            "result": base64.b64encode(result).decode('utf-8'),
                            "type": "screenshot"
                        }
                elif fn_name in ["inner_text", "text_content", "get_attribute"]:
                    return {
                        "success": True,
                        "result": result,
                        "type": "text"
                    }
                elif fn_name == "title":
                    return {
                        "success": True,
                        "result": result,
                        "type": "title"
                    }
                else:
                    return {
                        "success": True,
                        "result": str(result) if result is not None else None
                    }
                    
            except Exception as e:
                logger.error(f"Error executing {fn_name}: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
        else:
            return {
                "success": False,
                "error": f"Unknown function: {fn_name}"
            }
    
    def run_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a sequence of browser actions"""
        results = []
        for i, action in enumerate(actions):
            logger.info(f"Executing action {i+1}/{len(actions)}: {action.get('fn')}")
            result = self.execute_action(action)
            results.append(result)
            
            # Stop on error unless explicitly told to continue
            if not result.get("success") and not action.get("continue_on_error"):
                break
                
        return results

# Convenience functions for common tasks
def run_agent(actions: List[Dict[str, Any]], headless: bool = True, browser_type: str = "chromium") -> List[Dict[str, Any]]:
    """Simple function to run a list of actions"""
    agent = PlaywrightAgent(headless=headless, browser_type=browser_type)
    try:
        agent.start()
        return agent.run_actions(actions)
    finally:
        agent.stop()

def navigate_and_screenshot(url: str, output_path: str = None, headless: bool = True):
    """Navigate to URL and take screenshot"""
    actions = [
        {"fn": "goto", "args": [url]},
        {"fn": "wait_for_load_state", "args": ["networkidle"]},
        {"fn": "screenshot", "kwargs": {"full_page": True}}
    ]
    
    results = run_agent(actions, headless=headless)
    
    if results[-1].get("success") and output_path:
        # Save screenshot to file
        screenshot_data = base64.b64decode(results[-1]["result"])
        with open(output_path, "wb") as f:
            f.write(screenshot_data)
        logger.info(f"Screenshot saved to {output_path}")
    
    return results

def extract_text(url: str, selector: str = "body", headless: bool = True) -> str:
    """Navigate to URL and extract text from selector"""
    actions = [
        {"fn": "goto", "args": [url]},
        {"fn": "wait_for_load_state", "args": ["domcontentloaded"]},
        {"fn": "inner_text", "args": [selector]}
    ]
    
    results = run_agent(actions, headless=headless)
    
    if results[-1].get("success"):
        return results[-1]["result"]
    else:
        return None

# Example usage
if __name__ == "__main__":
    # Example 1: Simple navigation and screenshot
    print("Example 1: Navigate and screenshot")
    actions = [
        {"fn": "goto", "args": ["https://example.com"]},
        {"fn": "screenshot", "kwargs": {"full_page": True}}
    ]
    results = run_agent(actions)
    print(f"Results: {json.dumps(results, indent=2)}")
    
    # Example 2: More complex interaction
    print("\nExample 2: Search on a website")
    search_actions = [
        {"fn": "goto", "args": ["https://www.google.com"]},
        {"fn": "wait_for_selector", "args": ["[name='q']"]},
        {"fn": "fill", "args": ["[name='q']", "playwright python"]},
        {"fn": "press", "args": ["[name='q']", "Enter"]},
        {"fn": "wait_for_load_state", "args": ["networkidle"]},
        {"fn": "screenshot"}
    ]
    # Uncomment to run:
    # results = run_agent(search_actions)
    # print(f"Search results: {json.dumps(results, indent=2)}")