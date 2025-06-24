#!/usr/bin/env python3
"""
Advanced Playwright Agent with extended capabilities
Includes element detection, waiting strategies, and LLM-friendly interfaces
"""
from playwright.sync_api import sync_playwright, Page, ElementHandle
import json
import base64
from typing import List, Dict, Any, Optional, Union
import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedPlaywrightAgent:
    """Advanced agent with smart element detection and action execution"""
    
    def __init__(self, headless: bool = True, browser_type: str = "chromium", 
                 stealth: bool = True, timeout: int = 30000):
        self.headless = headless
        self.browser_type = browser_type
        self.stealth = stealth
        self.timeout = timeout
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        self.action_history = []
        
    def start(self):
        """Initialize browser with stealth options"""
        self.playwright = sync_playwright().start()
        
        # Select browser type
        browser_launchers = {
            "chromium": self.playwright.chromium,
            "firefox": self.playwright.firefox,
            "webkit": self.playwright.webkit
        }
        browser_launcher = browser_launchers.get(self.browser_type)
        if not browser_launcher:
            raise ValueError(f"Unknown browser type: {self.browser_type}")
            
        # Launch arguments for stealth mode
        launch_args = ['--no-sandbox', '--disable-setuid-sandbox']
        if self.stealth and self.browser_type == "chromium":
            launch_args.extend([
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials'
            ])
            
        # Launch browser
        self.browser = browser_launcher.launch(
            headless=self.headless,
            args=launch_args
        )
        
        # Create context with stealth settings
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'locale': 'en-US',
            'timezone_id': 'America/New_York'
        }
        
        if self.stealth:
            context_options.update({
                'ignore_https_errors': True,
                'java_script_enabled': True
            })
        
        self.context = self.browser.new_context(**context_options)
        
        # Add stealth scripts
        if self.stealth:
            self.context.add_init_script("""
                // Override the navigator.webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override plugins length
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
        
        # Create page
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        
        logger.info(f"Started {self.browser_type} browser (headless={self.headless}, stealth={self.stealth})")
        
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
        
    def wait_for_page_ready(self, timeout: int = 5000):
        """Wait for page to be fully ready"""
        try:
            # Wait for basic load
            self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
            
            # Wait for network to be idle
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            
            # Wait for any animations to complete
            self.page.wait_for_timeout(500)
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def smart_click(self, selector: str, force: bool = False, wait: bool = True):
        """Click with smart waiting and retry logic"""
        try:
            if wait:
                self.page.wait_for_selector(selector, state="visible", timeout=self.timeout)
            
            element = self.page.locator(selector)
            
            # Scroll element into view
            element.scroll_into_view_if_needed()
            
            # Wait a bit for any animations
            self.page.wait_for_timeout(200)
            
            # Try to click
            if force:
                element.click(force=True)
            else:
                element.click()
                
            return {"success": True, "selector": selector}
        except Exception as e:
            logger.error(f"Failed to click {selector}: {str(e)}")
            return {"success": False, "error": str(e), "selector": selector}
    
    def smart_fill(self, selector: str, text: str, clear_first: bool = True):
        """Fill input with smart clearing and validation"""
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=self.timeout)
            
            if clear_first:
                self.page.locator(selector).clear()
                
            self.page.locator(selector).fill(text)
            
            # Verify the text was entered
            actual_value = self.page.locator(selector).input_value()
            if actual_value != text:
                logger.warning(f"Fill verification failed. Expected: {text}, Got: {actual_value}")
                
            return {"success": True, "selector": selector, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}
    
    def get_page_info(self) -> Dict[str, Any]:
        """Get comprehensive page information"""
        try:
            # Get all text content
            text_content = self.page.locator("body").inner_text()
            
            # Get all links
            links = []
            link_elements = self.page.locator("a").all()
            for link in link_elements[:20]:  # Limit to first 20
                href = link.get_attribute("href")
                text = link.inner_text()
                if href:
                    links.append({"href": href, "text": text.strip()})
            
            # Get all buttons
            buttons = []
            button_elements = self.page.locator("button, input[type='submit'], input[type='button']").all()
            for button in button_elements[:20]:  # Limit to first 20
                text = button.inner_text() or button.get_attribute("value") or ""
                buttons.append({"text": text.strip(), "selector": button})
            
            # Get all inputs
            inputs = []
            input_elements = self.page.locator("input[type='text'], input[type='email'], input[type='password'], textarea").all()
            for inp in input_elements[:20]:  # Limit to first 20
                name = inp.get_attribute("name") or ""
                placeholder = inp.get_attribute("placeholder") or ""
                input_type = inp.get_attribute("type") or "text"
                inputs.append({
                    "name": name,
                    "placeholder": placeholder,
                    "type": input_type
                })
            
            return {
                "success": True,
                "url": self.page.url,
                "title": self.page.title(),
                "text_preview": text_content[:1000],  # First 1000 chars
                "links": links,
                "buttons": buttons,
                "inputs": inputs
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single browser action with enhanced error handling"""
        fn_name = action.get("fn")
        args = action.get("args", [])
        kwargs = action.get("kwargs", {})
        
        # Record action
        self.action_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action
        })
        
        # Handle custom smart functions
        if fn_name == "smart_click":
            return self.smart_click(*args, **kwargs)
        elif fn_name == "smart_fill":
            return self.smart_fill(*args, **kwargs)
        elif fn_name == "wait_for_page_ready":
            return self.wait_for_page_ready(*args, **kwargs)
        elif fn_name == "get_page_info":
            return self.get_page_info()
        
        # Handle standard Playwright functions
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
                elif fn_name in ["inner_text", "text_content", "get_attribute", "title", "url"]:
                    return {
                        "success": True,
                        "result": result,
                        "type": "text"
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
                    "error": str(e),
                    "fn": fn_name
                }
        else:
            return {
                "success": False,
                "error": f"Unknown function: {fn_name}",
                "available_functions": [
                    "goto", "click", "fill", "press", "screenshot",
                    "wait_for_selector", "wait_for_load_state",
                    "inner_text", "get_attribute", "smart_click",
                    "smart_fill", "get_page_info", "wait_for_page_ready"
                ]
            }
    
    def run_actions(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a sequence of browser actions with summary"""
        results = []
        start_time = time.time()
        
        for i, action in enumerate(actions):
            logger.info(f"Executing action {i+1}/{len(actions)}: {action.get('fn')}")
            result = self.execute_action(action)
            results.append(result)
            
            # Stop on error unless explicitly told to continue
            if not result.get("success") and not action.get("continue_on_error"):
                break
                
        end_time = time.time()
        
        # Create summary
        successful_actions = sum(1 for r in results if r.get("success"))
        failed_actions = len(results) - successful_actions
        
        return {
            "results": results,
            "summary": {
                "total_actions": len(actions),
                "executed_actions": len(results),
                "successful_actions": successful_actions,
                "failed_actions": failed_actions,
                "execution_time": f"{end_time - start_time:.2f}s",
                "final_url": self.page.url if self.page else None,
                "final_title": self.page.title() if self.page else None
            }
        }

# LLM-friendly wrapper functions
def create_browser_session(headless: bool = True, browser_type: str = "chromium") -> AdvancedPlaywrightAgent:
    """Create a new browser session"""
    agent = AdvancedPlaywrightAgent(headless=headless, browser_type=browser_type)
    agent.start()
    return agent

def navigate_to(agent: AdvancedPlaywrightAgent, url: str) -> Dict[str, Any]:
    """Navigate to a URL and wait for it to load"""
    actions = [
        {"fn": "goto", "args": [url]},
        {"fn": "wait_for_page_ready"}
    ]
    return agent.run_actions(actions)

def search_google(agent: AdvancedPlaywrightAgent, query: str) -> Dict[str, Any]:
    """Perform a Google search"""
    actions = [
        {"fn": "goto", "args": ["https://www.google.com"]},
        {"fn": "wait_for_page_ready"},
        {"fn": "smart_fill", "args": ["[name='q']", query]},
        {"fn": "press", "args": ["[name='q']", "Enter"]},
        {"fn": "wait_for_page_ready"},
        {"fn": "get_page_info"}
    ]
    return agent.run_actions(actions)

def fill_form(agent: AdvancedPlaywrightAgent, form_data: Dict[str, str]) -> Dict[str, Any]:
    """Fill a form with provided data"""
    actions = []
    for selector, value in form_data.items():
        actions.append({"fn": "smart_fill", "args": [selector, value]})
    return agent.run_actions(actions)

# Example usage
if __name__ == "__main__":
    # Example: Create session and navigate
    print("Creating browser session...")
    agent = create_browser_session(headless=True)
    
    try:
        # Navigate to example.com
        print("\nNavigating to example.com...")
        result = navigate_to(agent, "https://example.com")
        print(f"Navigation result: {json.dumps(result['summary'], indent=2)}")
        
        # Get page information
        print("\nGetting page info...")
        info = agent.get_page_info()
        print(f"Page title: {info.get('title')}")
        print(f"Page URL: {info.get('url')}")
        print(f"Number of links: {len(info.get('links', []))}")
        
        # Take screenshot
        print("\nTaking screenshot...")
        screenshot_result = agent.execute_action({
            "fn": "screenshot",
            "kwargs": {"full_page": True}
        })
        if screenshot_result.get("success"):
            print("Screenshot captured successfully")
            
    finally:
        agent.stop()
        print("\nBrowser session closed")