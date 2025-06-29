#!/usr/bin/env python3
"""
Example of how to use the deep click implementation with CrosshairBrowserClient
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from clients.browser_client_crosshair import CrosshairBrowserClient
from CLAUDE_TMP.deep_click_implementation import DeepClickMixin

class DeepCrosshairBrowserClient(DeepClickMixin, CrosshairBrowserClient):
    """Browser client with both crosshair visualization and deep element detection"""
    
    async def click_at(self, x: float, y: float, label: str = "click_at") -> Dict[str, Any]:
        """Override click_at to use deep detection with crosshair visualization"""
        # Perform deep click detection
        result = await self.click_at_deep(x, y, label)
        
        # Log summary
        if result['success']:
            print(f"\n✅ Click successful at ({x}, {y})")
            if result.get('target_element'):
                elem = result['target_element']
                print(f"   Clicked: {elem['tagName']}#{elem['id']} - {elem['text'][:30]}...")
        else:
            print(f"\n❌ Click failed at ({x}, {y})")
            
        return result

async def demo_deep_click():
    """Demonstrate deep click functionality"""
    client = DeepCrosshairBrowserClient()
    
    # Example 1: Create a test page with an iframe
    print("Creating test page with iframe...")
    session = await client.create_session()
    
    # Create a page with an iframe containing a button
    await client.evaluate("""
        document.body.innerHTML = `
            <h1>Deep Click Test Page</h1>
            <button id="main-button" style="margin: 20px;">Main Page Button</button>
            <iframe id="test-iframe" style="width: 400px; height: 300px; border: 2px solid blue;" srcdoc="
                <html>
                <body style='padding: 20px;'>
                    <h2>Inside iframe</h2>
                    <button id='iframe-button' style='padding: 10px; background: green; color: white;'>
                        Click me (inside iframe)
                    </button>
                </body>
                </html>
            "></iframe>
        `;
    """)
    
    await asyncio.sleep(1)  # Wait for iframe to load
    
    # Example 2: Click on the main page button
    print("\n" + "="*60)
    print("TEST 1: Clicking main page button")
    print("="*60)
    
    main_button_info = await client.evaluate("""
        (() => {
            const btn = document.getElementById('main-button');
            const rect = btn.getBoundingClientRect();
            return {
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2
            };
        })()
    """)
    
    result1 = await client.click_at(
        main_button_info['x'], 
        main_button_info['y'], 
        "main_page_button"
    )
    
    # Example 3: Click on the iframe button
    print("\n" + "="*60)
    print("TEST 2: Clicking button inside iframe")
    print("="*60)
    
    iframe_button_info = await client.evaluate("""
        (() => {
            const iframe = document.getElementById('test-iframe');
            const iframeDoc = iframe.contentDocument;
            const btn = iframeDoc.getElementById('iframe-button');
            
            const btnRect = btn.getBoundingClientRect();
            const iframeRect = iframe.getBoundingClientRect();
            
            return {
                x: iframeRect.left + btnRect.left + btnRect.width / 2,
                y: iframeRect.top + btnRect.top + btnRect.height / 2
            };
        })()
    """)
    
    result2 = await client.click_at(
        iframe_button_info['x'], 
        iframe_button_info['y'], 
        "iframe_button"
    )
    
    # Example 4: Click on empty space
    print("\n" + "="*60)
    print("TEST 3: Clicking on empty space")
    print("="*60)
    
    result3 = await client.click_at(10, 10, "empty_space")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Main button click: {'✅ Success' if result1['success'] else '❌ Failed'}")
    print(f"Iframe button click: {'✅ Success' if result2['success'] else '❌ Failed'}")
    print(f"Empty space click: {'✅ Success' if result3['success'] else '❌ Failed'}")

if __name__ == "__main__":
    asyncio.run(demo_deep_click())