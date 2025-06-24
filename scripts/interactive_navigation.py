#!/usr/bin/env python3
"""
Interactive navigation that takes screenshots at each step for analysis
"""
from playwright_agent_advanced import create_browser_session
import os
import json
from datetime import datetime

class InteractiveNavigator:
    def __init__(self, headless=True):
        self.agent = None
        self.step_count = 0
        self.navigation_log = []
        
    def start_session(self, url):
        """Start a browser session and navigate to URL"""
        os.environ['DISPLAY'] = ':99'
        self.agent = create_browser_session(headless=True)
        
        print(f"Starting navigation of {url}")
        self.agent.page.goto(url)
        self.agent.page.wait_for_load_state('networkidle')
        self.agent.page.wait_for_timeout(2000)
        
        # Take initial screenshot
        self.take_screenshot("initial")
        
        # Log the action
        self.log_action("navigate", {"url": url})
        
        return self.analyze_current_state()
    
    def take_screenshot(self, action_name):
        """Take a screenshot with descriptive filename"""
        self.step_count += 1
        timestamp = datetime.now().strftime('%H%M%S')
        filename = f'/home/ubuntu/screenshots/nav_step{self.step_count:02d}_{action_name}_{timestamp}.png'
        self.agent.page.screenshot(path=filename, full_page=True)
        print(f"Screenshot saved: {filename}")
        return filename
    
    def analyze_current_state(self):
        """Analyze the current page state"""
        state = {
            "url": self.agent.page.url,
            "title": self.agent.page.title(),
            "elements": {}
        }
        
        # Count different types of elements
        try:
            state["elements"]["buttons"] = len(self.agent.page.locator('button').all())
            state["elements"]["links"] = len(self.agent.page.locator('a[href]').all())
            state["elements"]["inputs"] = len(self.agent.page.locator('input, textarea').all())
            state["elements"]["forms"] = len(self.agent.page.locator('form').all())
            
            # Get visible text from buttons
            buttons = self.agent.page.locator('button').all()
            state["button_texts"] = []
            for btn in buttons[:10]:  # First 10
                try:
                    text = btn.inner_text().strip()
                    if text:
                        state["button_texts"].append(text)
                except:
                    pass
            
            # Get visible links
            links = self.agent.page.locator('a[href]').all()
            state["link_texts"] = []
            for link in links[:10]:  # First 10
                try:
                    text = link.inner_text().strip()
                    href = link.get_attribute('href')
                    if text:
                        state["link_texts"].append({"text": text, "href": href})
                except:
                    pass
                    
        except Exception as e:
            state["error"] = str(e)
        
        return state
    
    def log_action(self, action_type, details):
        """Log an action for later review"""
        self.navigation_log.append({
            "step": self.step_count,
            "action": action_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def click_element(self, selector, description=""):
        """Click an element and take screenshot"""
        try:
            element = self.agent.page.locator(selector).first
            element.click()
            self.agent.page.wait_for_timeout(2000)
            
            # Take screenshot after action
            self.take_screenshot(f"after_click_{description}")
            
            # Log the action
            self.log_action("click", {"selector": selector, "description": description})
            
            return True, self.analyze_current_state()
        except Exception as e:
            return False, {"error": str(e)}
    
    def fill_input(self, selector, text, description=""):
        """Fill an input field and take screenshot"""
        try:
            element = self.agent.page.locator(selector).first
            element.fill(text)
            self.agent.page.wait_for_timeout(1000)
            
            # Take screenshot after action
            self.take_screenshot(f"after_fill_{description}")
            
            # Log the action
            self.log_action("fill", {"selector": selector, "text": text, "description": description})
            
            return True, self.analyze_current_state()
        except Exception as e:
            return False, {"error": str(e)}
    
    def wait_and_screenshot(self, seconds, description=""):
        """Wait and take a screenshot"""
        self.agent.page.wait_for_timeout(seconds * 1000)
        self.take_screenshot(f"after_wait_{description}")
        return self.analyze_current_state()
    
    def save_navigation_log(self):
        """Save the navigation log to a file"""
        filename = f'/home/ubuntu/navigation_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(self.navigation_log, f, indent=2)
        print(f"Navigation log saved to: {filename}")
    
    def close(self):
        """Close the browser session"""
        if self.agent:
            self.agent.stop()
            self.save_navigation_log()

# Step-by-step navigation function
def navigate_step_by_step(url):
    """Navigate a website step by step with screenshot analysis"""
    nav = InteractiveNavigator()
    
    try:
        # Step 1: Initial navigation
        print("\n=== STEP 1: Initial Navigation ===")
        state = nav.start_session(url)
        print(f"Current state: {json.dumps(state, indent=2)}")
        
        # Based on the state, we can make decisions
        # This is where I would analyze the screenshot if I could see it in real-time
        
        # Step 2: Try to find and fill the main input
        if state["elements"]["inputs"] > 0:
            print("\n=== STEP 2: Fill Input Field ===")
            success, new_state = nav.fill_input(
                'textarea, input[type="text"]',
                "Create a simple calculator",
                "prompt"
            )
            if success:
                print("Successfully filled input field")
            
        # Step 3: Look for the main action button
        if "Fuzzy Code It!" in str(state.get("button_texts", [])):
            print("\n=== STEP 3: Click Generate Button ===")
            success, new_state = nav.click_element(
                'button:has-text("Fuzzy Code It!")',
                "generate"
            )
            if success:
                print("Clicked generate button")
                
                # Step 4: Wait for results
                print("\n=== STEP 4: Wait for Generation ===")
                nav.wait_and_screenshot(5, "generation_complete")
        
        # Step 5: Try navigation link
        if state["elements"]["links"] > 0:
            print("\n=== STEP 5: Explore Links ===")
            # Find Play Now link
            for link in state.get("link_texts", []):
                if "play" in link.get("text", "").lower():
                    print(f"Found link: {link}")
                    # We could click it here
        
        print("\n=== Navigation Complete ===")
        print(f"Total steps taken: {nav.step_count}")
        
    finally:
        nav.close()

# Alternative: Checkpoint-based navigation
def checkpoint_navigation():
    """Navigate with checkpoints where we can review screenshots"""
    nav = InteractiveNavigator()
    
    # CHECKPOINT 1: Initial page load
    print("\n=== CHECKPOINT 1: Initial Load ===")
    state = nav.start_session("https://fuzzycode.dev")
    
    # Save checkpoint data
    checkpoint_file = '/home/ubuntu/checkpoint1.json'
    with open(checkpoint_file, 'w') as f:
        json.dump({
            "state": state,
            "screenshot": f"nav_step{nav.step_count:02d}_initial_*.png",
            "next_actions": [
                "Fill the prompt input with a coding request",
                "Click the 'Fuzzy Code It!' button",
                "Explore the 'Play Now' link"
            ]
        }, f, indent=2)
    
    print(f"Checkpoint saved to: {checkpoint_file}")
    print("Review the screenshot and checkpoint data to decide next action")
    
    nav.close()
    return checkpoint_file

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "checkpoint":
        # Run checkpoint mode
        checkpoint_navigation()
    else:
        # Run full navigation
        navigate_step_by_step("https://fuzzycode.dev")