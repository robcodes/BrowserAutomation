#!/usr/bin/env python3
"""
Test examples for Playwright agents
Demonstrates various browser automation scenarios
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from playwright_agent import PlaywrightAgent, run_agent
from playwright_agent_advanced import AdvancedPlaywrightAgent, create_browser_session
import json

def test_basic_navigation():
    """Test basic navigation and screenshot"""
    print("\n=== Test 1: Basic Navigation ===")
    
    actions = [
        {"fn": "goto", "args": ["https://example.com"]},
        {"fn": "wait_for_load_state", "args": ["networkidle"]},
        {"fn": "screenshot", "kwargs": {"path": "example_screenshot.png"}}
    ]
    
    results = run_agent(actions, headless=True)
    
    for i, result in enumerate(results):
        print(f"Action {i+1}: {'✓' if result.get('success') else '✗'}")
        if not result.get('success'):
            print(f"  Error: {result.get('error')}")
    
    print("Screenshot saved as example_screenshot.png")

def test_search_interaction():
    """Test form filling and interaction"""
    print("\n=== Test 2: Search Interaction ===")
    
    agent = AdvancedPlaywrightAgent(headless=True)
    agent.start()
    
    try:
        # Navigate to DuckDuckGo (lighter than Google)
        result = agent.run_actions([
            {"fn": "goto", "args": ["https://duckduckgo.com"]},
            {"fn": "wait_for_page_ready"}
        ])
        print(f"Navigation: {'✓' if result['summary']['successful_actions'] == 2 else '✗'}")
        
        # Perform search
        result = agent.run_actions([
            {"fn": "smart_fill", "args": ["#search_form_input_homepage", "playwright python"]},
            {"fn": "press", "args": ["#search_form_input_homepage", "Enter"]},
            {"fn": "wait_for_page_ready"}
        ])
        print(f"Search: {'✓' if result['summary']['successful_actions'] == 3 else '✗'}")
        
        # Get page info
        info = agent.get_page_info()
        print(f"Results page title: {info.get('title', 'N/A')}")
        print(f"Number of links found: {len(info.get('links', []))}")
        
    finally:
        agent.stop()

def test_multiple_pages():
    """Test handling multiple pages/tabs"""
    print("\n=== Test 3: Multiple Pages ===")
    
    agent = PlaywrightAgent(headless=True)
    agent.start()
    
    try:
        # Navigate to first page
        agent.execute_action({"fn": "goto", "args": ["https://example.com"]})
        title1 = agent.execute_action({"fn": "title"})
        print(f"Page 1 title: {title1.get('result')}")
        
        # Create new page
        page2 = agent.context.new_page()
        page2.goto("https://example.org")
        title2 = page2.title()
        print(f"Page 2 title: {title2}")
        
        # Switch back to original page
        agent.page.bring_to_front()
        
        # Both pages are still active
        print(f"Total pages open: {len(agent.context.pages)}")
        
        # Close page 2
        page2.close()
        
    finally:
        agent.stop()

def test_element_detection():
    """Test smart element detection"""
    print("\n=== Test 4: Element Detection ===")
    
    agent = AdvancedPlaywrightAgent(headless=True)
    agent.start()
    
    try:
        # Navigate to a page with forms
        agent.run_actions([
            {"fn": "goto", "args": ["https://httpbin.org/forms/post"]}
        ])
        
        # Get page info to see what elements are available
        info = agent.get_page_info()
        
        print(f"Page URL: {info.get('url')}")
        print(f"Inputs found: {len(info.get('inputs', []))}")
        
        for inp in info.get('inputs', [])[:5]:  # Show first 5
            print(f"  - {inp['type']}: {inp['name']} (placeholder: '{inp['placeholder']}')")
        
        print(f"Buttons found: {len(info.get('buttons', []))}")
        for btn in info.get('buttons', [])[:3]:  # Show first 3
            print(f"  - {btn['text']}")
            
    finally:
        agent.stop()

def test_stealth_mode():
    """Test stealth mode capabilities"""
    print("\n=== Test 5: Stealth Mode ===")
    
    # Regular mode
    agent1 = PlaywrightAgent(headless=True)
    agent1.start()
    
    try:
        agent1.page.goto("https://bot.sannysoft.com/")
        agent1.page.wait_for_timeout(2000)
        regular_screenshot = agent1.page.screenshot()
        print("Regular mode: Screenshot taken")
    finally:
        agent1.stop()
    
    # Stealth mode
    agent2 = AdvancedPlaywrightAgent(headless=True, stealth=True)
    agent2.start()
    
    try:
        agent2.page.goto("https://bot.sannysoft.com/")
        agent2.page.wait_for_timeout(2000)
        stealth_screenshot = agent2.page.screenshot()
        print("Stealth mode: Screenshot taken")
        print("Note: Stealth mode includes anti-detection measures")
    finally:
        agent2.stop()

def run_all_tests():
    """Run all test examples"""
    print("Starting Playwright Agent Tests")
    print("=" * 50)
    
    tests = [
        test_basic_navigation,
        test_search_interaction,
        test_multiple_pages,
        test_element_detection,
        test_stealth_mode
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\nTest failed with error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    # Check if virtual display is needed
    import os
    if not os.environ.get('DISPLAY'):
        print("No display found. Setting up virtual display...")
        os.environ['DISPLAY'] = ':99'
        print("Please ensure Xvfb is running: Xvfb :99 -screen 0 1920x1080x24 &")
    
    # Run specific test or all tests
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "basic":
            test_basic_navigation()
        elif test_name == "search":
            test_search_interaction()
        elif test_name == "multiple":
            test_multiple_pages()
        elif test_name == "elements":
            test_element_detection()
        elif test_name == "stealth":
            test_stealth_mode()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: basic, search, multiple, elements, stealth")
    else:
        run_all_tests()