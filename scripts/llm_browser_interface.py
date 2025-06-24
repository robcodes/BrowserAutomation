#!/usr/bin/env python3
"""
LLM-friendly browser interface
Provides simple JSON-based commands for browser control
"""
import json
import sys
from playwright_agent_advanced import AdvancedPlaywrightAgent

class LLMBrowserInterface:
    """Simple interface for LLM to control browser"""
    
    def __init__(self):
        self.agent = None
        self.session_active = False
        
    def execute_command(self, command: str) -> str:
        """Execute a JSON command and return JSON response"""
        try:
            cmd = json.loads(command)
            action = cmd.get("action")
            
            if action == "start_session":
                return self._start_session(cmd.get("params", {}))
            elif action == "end_session":
                return self._end_session()
            elif action == "navigate":
                return self._navigate(cmd.get("url"))
            elif action == "click":
                return self._click(cmd.get("selector"))
            elif action == "fill":
                return self._fill(cmd.get("selector"), cmd.get("text"))
            elif action == "screenshot":
                return self._screenshot(cmd.get("full_page", False))
            elif action == "get_info":
                return self._get_info()
            elif action == "execute_actions":
                return self._execute_actions(cmd.get("actions", []))
            else:
                return json.dumps({
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [
                        "start_session", "end_session", "navigate", 
                        "click", "fill", "screenshot", "get_info", 
                        "execute_actions"
                    ]
                })
                
        except json.JSONDecodeError:
            return json.dumps({
                "success": False,
                "error": "Invalid JSON command"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    def _start_session(self, params: dict) -> str:
        """Start a new browser session"""
        if self.session_active:
            return json.dumps({
                "success": False,
                "error": "Session already active"
            })
            
        try:
            headless = params.get("headless", True)
            browser_type = params.get("browser_type", "chromium")
            
            self.agent = AdvancedPlaywrightAgent(
                headless=headless,
                browser_type=browser_type,
                stealth=params.get("stealth", True)
            )
            self.agent.start()
            self.session_active = True
            
            return json.dumps({
                "success": True,
                "message": f"Started {browser_type} session",
                "session_id": id(self.agent)
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    def _end_session(self) -> str:
        """End the current browser session"""
        if not self.session_active:
            return json.dumps({
                "success": False,
                "error": "No active session"
            })
            
        try:
            self.agent.stop()
            self.agent = None
            self.session_active = False
            
            return json.dumps({
                "success": True,
                "message": "Session ended"
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    def _navigate(self, url: str) -> str:
        """Navigate to a URL"""
        if not self.session_active:
            return json.dumps({
                "success": False,
                "error": "No active session"
            })
            
        result = self.agent.run_actions([
            {"fn": "goto", "args": [url]},
            {"fn": "wait_for_page_ready"}
        ])
        
        return json.dumps({
            "success": result["summary"]["successful_actions"] == 2,
            "url": self.agent.page.url,
            "title": self.agent.page.title()
        })
    
    def _click(self, selector: str) -> str:
        """Click an element"""
        if not self.session_active:
            return json.dumps({
                "success": False,
                "error": "No active session"
            })
            
        result = self.agent.smart_click(selector)
        return json.dumps(result)
    
    def _fill(self, selector: str, text: str) -> str:
        """Fill a form field"""
        if not self.session_active:
            return json.dumps({
                "success": False,
                "error": "No active session"
            })
            
        result = self.agent.smart_fill(selector, text)
        return json.dumps(result)
    
    def _screenshot(self, full_page: bool = False) -> str:
        """Take a screenshot"""
        if not self.session_active:
            return json.dumps({
                "success": False,
                "error": "No active session"
            })
            
        result = self.agent.execute_action({
            "fn": "screenshot",
            "kwargs": {"full_page": full_page}
        })
        
        if result.get("success"):
            return json.dumps({
                "success": True,
                "screenshot": result["result"],  # Base64 encoded
                "type": "base64"
            })
        else:
            return json.dumps(result)
    
    def _get_info(self) -> str:
        """Get current page information"""
        if not self.session_active:
            return json.dumps({
                "success": False,
                "error": "No active session"
            })
            
        info = self.agent.get_page_info()
        return json.dumps(info)
    
    def _execute_actions(self, actions: list) -> str:
        """Execute a list of actions"""
        if not self.session_active:
            return json.dumps({
                "success": False,
                "error": "No active session"
            })
            
        result = self.agent.run_actions(actions)
        return json.dumps(result)

# Example commands for LLM
EXAMPLE_COMMANDS = """
# Start a browser session
{"action": "start_session", "params": {"headless": true, "browser_type": "chromium"}}

# Navigate to a website
{"action": "navigate", "url": "https://example.com"}

# Get page information
{"action": "get_info"}

# Click an element
{"action": "click", "selector": "button.submit"}

# Fill a form field
{"action": "fill", "selector": "input[name='username']", "text": "john_doe"}

# Take a screenshot
{"action": "screenshot", "full_page": true}

# Execute multiple actions
{"action": "execute_actions", "actions": [
    {"fn": "goto", "args": ["https://google.com"]},
    {"fn": "wait_for_selector", "args": ["[name='q']"]},
    {"fn": "fill", "args": ["[name='q']", "playwright tutorial"]},
    {"fn": "press", "args": ["[name='q']", "Enter"]}
]}

# End the session
{"action": "end_session"}
"""

def main():
    """Interactive mode for testing"""
    print("LLM Browser Interface")
    print("=" * 50)
    print("Enter JSON commands (or 'help' for examples, 'quit' to exit)")
    print()
    
    interface = LLMBrowserInterface()
    
    while True:
        try:
            cmd = input("> ").strip()
            
            if cmd.lower() == "quit":
                if interface.session_active:
                    interface.execute_command('{"action": "end_session"}')
                break
            elif cmd.lower() == "help":
                print(EXAMPLE_COMMANDS)
                continue
            elif not cmd:
                continue
                
            response = interface.execute_command(cmd)
            print(json.dumps(json.loads(response), indent=2))
            
        except KeyboardInterrupt:
            print("\nExiting...")
            if interface.session_active:
                interface.execute_command('{"action": "end_session"}')
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Check for command line usage
    if len(sys.argv) > 1:
        # Single command mode
        interface = LLMBrowserInterface()
        command = ' '.join(sys.argv[1:])
        result = interface.execute_command(command)
        print(result)
        
        # Auto-cleanup if session was started
        if interface.session_active:
            interface.execute_command('{"action": "end_session"}')
    else:
        # Interactive mode
        main()