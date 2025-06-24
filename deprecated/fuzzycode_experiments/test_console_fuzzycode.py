#!/usr/bin/env python3
"""
Test Console Capture with FuzzyCode.dev
Uses the enhanced browser server to capture and analyze console logs
"""
import asyncio
from browser_client_enhanced import EnhancedBrowserClient, debug_failed_action
from datetime import datetime, timedelta

async def test_fuzzycode_with_console():
    """Test fuzzycode.dev and capture all console output"""
    print("=== Testing FuzzyCode with Console Capture ===\n")
    
    client = EnhancedBrowserClient()
    
    try:
        # Create session
        session_id = await client.create_session(headless=False)
        print(f"✓ Created session: {session_id}")
        
        # Navigate to fuzzycode
        page_id = await client.new_page("https://fuzzycode.dev")
        print(f"✓ Created page: {page_id}")
        
        # Wait for initial load
        await client.wait(3000)
        
        # Check initial console logs
        print("\n📋 Initial Console Logs:")
        logs = await client.get_console_logs()
        print(f"  Total logs captured: {logs['count']}")
        
        # Print any errors
        await client.print_recent_errors()
        
        # Take initial screenshot
        await client.screenshot("fuzzycode_console_1_initial.png")
        
        # Try to interact with the page
        print("\n→ Attempting to fill prompt...")
        prompt_text = "Create a Python function to calculate factorial"
        
        # Check console before action
        before_time = datetime.now()
        
        try:
            await client.fill('textarea', prompt_text)
            print("✓ Filled textarea")
        except Exception as e:
            print(f"✗ Failed to fill textarea: {e}")
            await debug_failed_action(client, "Fill textarea")
            
            # Try alternative selector
            try:
                await client.fill('input[type="text"]', prompt_text)
                print("✓ Filled input field (alternative)")
            except:
                pass
        
        # Check for new console logs since our action
        new_logs = await client.get_console_logs(since=before_time)
        if new_logs["logs"]:
            print(f"\n📋 New logs after fill action: {len(new_logs['logs'])}")
            for log in new_logs["logs"]:
                print(f"  [{log['type']}] {log['text'][:100]}...")
        
        # Screenshot after fill
        await client.screenshot("fuzzycode_console_2_filled.png")
        
        # Try to click generate button
        print("\n→ Attempting to click 'Fuzzy Code It!' button...")
        before_click = datetime.now()
        
        try:
            await client.click('button:has-text("Fuzzy Code It!")')
            print("✓ Clicked generate button")
        except Exception as e:
            print(f"✗ Failed to click button: {e}")
            await debug_failed_action(client, "Click generate button")
            
            # Check what buttons are available
            buttons = await client.evaluate("""
                Array.from(document.querySelectorAll('button')).map(b => ({
                    text: b.textContent,
                    visible: b.offsetParent !== null,
                    disabled: b.disabled
                }))
            """)
            print("\n🔘 Available buttons:")
            for btn in buttons:
                if btn.get('visible'):
                    print(f"  - '{btn['text']}' (disabled: {btn.get('disabled', False)})")
        
        # Wait for any generation
        print("\n⏳ Waiting for code generation...")
        await client.wait(5000)
        
        # Check console logs during generation
        gen_logs = await client.get_console_logs(since=before_click)
        if gen_logs["logs"]:
            print(f"\n📋 Logs during generation: {len(gen_logs['logs'])}")
            for log in gen_logs["logs"][:10]:  # First 10
                print(f"  [{log['type']}] {log['text'][:100]}...")
        
        # Check network activity
        print("\n🌐 Recent Network Activity:")
        network = await client.get_network_logs(since=before_click, limit=10)
        for log in network["logs"]:
            status = f" -> {log.get('status', '')}" if log['type'] == 'response' else ""
            print(f"  {log['type']}: {log['method']} {log['url'][:60]}...{status}")
        
        # Final screenshot
        await client.screenshot("fuzzycode_console_3_after_gen.png")
        
        # Summary of all errors encountered
        print("\n📊 Session Summary:")
        all_errors = await client.get_errors()
        all_logs = await client.get_console_logs()
        print(f"  Total console logs: {all_logs['count']}")
        print(f"  Total errors/warnings: {len(all_errors['errors'])}")
        
        if all_errors["errors"]:
            print("\n🚨 All Errors/Warnings in session:")
            for error in all_errors["errors"]:
                print(f"  [{error['type']}] {error['text']}")
        
        # Search for specific patterns in logs
        print("\n🔍 Searching for specific patterns:")
        
        # Look for API-related logs
        api_logs = await client.get_console_logs(text_contains="api")
        if api_logs["logs"]:
            print(f"  Found {len(api_logs['logs'])} logs mentioning 'api'")
        
        # Look for error-related logs
        error_logs = await client.get_console_logs(types=["error", "warning"])
        if error_logs["logs"]:
            print(f"  Found {len(error_logs['logs'])} error/warning logs")
        
        # Save session info for continuation
        with open("fuzzycode_console_session.json", "w") as f:
            import json
            json.dump({
                "session_id": session_id,
                "page_id": page_id,
                "timestamp": datetime.now().isoformat(),
                "total_logs": all_logs["count"],
                "total_errors": len(all_errors["errors"])
            }, f, indent=2)
        
        print(f"\n💾 Session saved for continuation: {session_id}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def analyze_saved_session():
    """Analyze logs from a saved session"""
    print("\n=== Analyzing Saved Session ===\n")
    
    import json
    with open("fuzzycode_console_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print(f"✓ Connected to session: {session_data['session_id']}")
    print(f"  Session started: {session_data['timestamp']}")
    print(f"  Total logs captured: {session_data['total_logs']}")
    print(f"  Total errors: {session_data['total_errors']}")
    
    # Get all logs and analyze patterns
    all_logs = await client.get_console_logs(limit=1000)
    
    # Categorize logs
    log_types = {}
    for log in all_logs["logs"]:
        log_type = log["type"]
        log_types[log_type] = log_types.get(log_type, 0) + 1
    
    print("\n📊 Log Type Distribution:")
    for log_type, count in sorted(log_types.items()):
        print(f"  {log_type}: {count}")
    
    # Find interesting patterns
    patterns = {
        "Loading": "load",
        "API calls": "api",
        "Errors": "error",
        "Warnings": "warning",
        "React": "react",
        "Network": "fetch"
    }
    
    print("\n🔍 Pattern Analysis:")
    for pattern_name, search_term in patterns.items():
        matching = await client.get_console_logs(text_contains=search_term)
        if matching["logs"]:
            print(f"\n  {pattern_name} ({len(matching['logs'])} logs):")
            for log in matching["logs"][:3]:  # First 3
                print(f"    [{log['type']}] {log['text'][:80]}...")


if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1 and sys.argv[1] == "analyze":
            await analyze_saved_session()
        else:
            await test_fuzzycode_with_console()
    
    asyncio.run(main())