#!/usr/bin/env python3
"""
Step 4: Submit Login Form (Direct approach with Gemini fallback)
- Clicks the Sign In button
- Uses multiple strategies to find the button
- Waits for login to complete
"""
from common import *
import sys
sys.path.append('/home/ubuntu/browser_automation')
from scripts.gemini_click_helper_enhanced import EnhancedGeminiClickHelper

async def step04_submit_login():
    """Submit the login form by clicking Sign In button"""
    print_step_header(4, "Submit Login Form (Direct)")
    
    # Load session from previous step
    session_info = await load_session_info()
    if not session_info or session_info['last_step'] < 3:
        print("❌ Previous steps not completed. Run step03 first!")
        return False
    
    client = BrowserClient()  # Use crosshair client
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        print("\n1. Taking pre-submit screenshot...")
        screenshot_path = await take_screenshot_and_check(
            client,
            "step04_pre_submit.png",
            "Should show filled login form ready to submit"
        )
        
        print("\n2. Looking for Sign In button...")
        
        # Strategy 1: Try direct CSS selector on the page
        button_check = await client.evaluate("""
            (() => {
                // Look for button on main page
                const buttons = Array.from(document.querySelectorAll('button'));
                const signInBtn = buttons.find(btn => 
                    btn.textContent.trim().toLowerCase() === 'sign in' ||
                    btn.textContent.trim().toLowerCase() === 'login'
                );
                
                if (signInBtn) {
                    const rect = signInBtn.getBoundingClientRect();
                    return {
                        found: true,
                        location: 'main',
                        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                        text: signInBtn.textContent
                    };
                }
                
                // Check in all iframes
                const iframes = Array.from(document.querySelectorAll('iframe'));
                for (let i = 0; i < iframes.length; i++) {
                    try {
                        const iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                        const iframeButtons = Array.from(iframeDoc.querySelectorAll('button'));
                        const iframeSignIn = iframeButtons.find(btn => 
                            btn.textContent.trim().toLowerCase() === 'sign in' ||
                            btn.textContent.trim().toLowerCase() === 'login'
                        );
                        
                        if (iframeSignIn) {
                            const iframeRect = iframes[i].getBoundingClientRect();
                            const btnRect = iframeSignIn.getBoundingClientRect();
                            return {
                                found: true,
                                location: 'iframe',
                                iframeIndex: i,
                                rect: { 
                                    x: iframeRect.x + btnRect.x, 
                                    y: iframeRect.y + btnRect.y, 
                                    width: btnRect.width, 
                                    height: btnRect.height 
                                },
                                text: iframeSignIn.textContent
                            };
                        }
                    } catch (e) {
                        // Cross-origin access error
                    }
                }
                
                return { found: false };
            })()
        """)
        
        print(f"   Button search result: {button_check}")
        
        clicked = False
        
        if button_check['found']:
            print(f"\n3. Found '{button_check['text']}' button in {button_check['location']}")
            
            if button_check['location'] == 'iframe':
                # Click inside iframe
                print(f"   Clicking button in iframe {button_check['iframeIndex']}...")
                click_result = await client.evaluate(f"""
                    (() => {{
                        const iframe = document.querySelectorAll('iframe')[{button_check['iframeIndex']}];
                        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                        const buttons = Array.from(iframeDoc.querySelectorAll('button'));
                        const signInBtn = buttons.find(btn => 
                            btn.textContent.trim().toLowerCase() === 'sign in' ||
                            btn.textContent.trim().toLowerCase() === 'login'
                        );
                        
                        if (signInBtn) {{
                            signInBtn.click();
                            return {{ success: true }};
                        }}
                        return {{ success: false }};
                    }})()
                """)
                clicked = click_result.get('success', False)
            else:
                # Click on main page using coordinates
                rect = button_check['rect']
                x = rect['x'] + rect['width'] / 2
                y = rect['y'] + rect['height'] / 2
                print(f"   Clicking at coordinates ({x}, {y})...")
                await client.click_with_crosshair(x=x, y=y, label='sign_in_button')
                clicked = True
        
        # If not found or click failed, use Gemini as fallback
        if not clicked:
            print("\n3. Using Gemini Vision to find Sign In button...")
            GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"
            helper = EnhancedGeminiClickHelper(client, GEMINI_API_KEY)
            
            # Find all clickable elements
            result = await helper.find_all_elements(
                session_info['session_id'],
                session_info['page_id'],
                prompt="Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for all buttons, clickable elements, icons, svgs, links, etc"
            )
            
            if result and 'coordinates' in result:
                print(f"   Found {len(result['coordinates'])} clickable elements")
                
                # Look for Sign In button by position (usually center of modal)
                for i, coords in enumerate(result['coordinates']):
                    ymin, xmin, ymax, xmax = coords
                    # Sign In button is typically in the center horizontally
                    if 400 < xmin < 600 and 400 < ymin < 500:
                        print(f"   Found potential Sign In button at position {i}")
                        await helper.click_at_coordinates(
                            session_info['session_id'],
                            session_info['page_id'],
                            coords,
                            label='sign_in_button_gemini'
                        )
                        clicked = True
                        break
        
        if not clicked:
            print("   ❌ Could not find or click Sign In button")
            return False
        
        print("\n4. Waiting for login to process...")
        await wait_and_check(client, 2000, "Initial wait")
        
        # Take progress screenshots
        await take_screenshot_and_check(
            client,
            "step04_progress_1.png",
            "Login progress - 2 seconds"
        )
        
        await wait_and_check(client, 3000, "Waiting for login response")
        
        await take_screenshot_and_check(
            client,
            "step04_progress_2.png",
            "Login progress - 5 seconds"
        )
        
        await wait_and_check(client, 5000, "Waiting for modal to close")
        
        print("\n5. Taking final screenshot...")
        await take_screenshot_and_check(
            client,
            "step04_final_state.png",
            "Should show either closed modal or error message"
        )
        
        # Update session info
        await save_session_info(session_info['session_id'], session_info['page_id'], 4)
        
        print_step_result(True, "Login submitted - check screenshots for result")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        await take_screenshot_and_check(client, "step04_error.png", "Error state")
        return False

if __name__ == "__main__":
    result = asyncio.run(step04_submit_login())
    import sys
    sys.exit(0 if result else 1)