#!/usr/bin/env python3
"""
Click the user profile icon we found
"""
import asyncio
import json
from browser_client_enhanced import EnhancedBrowserClient

async def click_profile_icon():
    """Click the user profile icon"""
    print("=== Clicking User Profile Icon ===\n")
    
    # Load session
    with open("fuzzycode_exploration_session.json", "r") as f:
        session_data = json.load(f)
    
    client = EnhancedBrowserClient()
    await client.connect_session(session_data["session_id"])
    await client.set_page(session_data["page_id"])
    
    print("✓ Reconnected to session")
    
    # Take screenshot before clicking
    await client.screenshot("fuzzy_explore_09_before_profile_click.png")
    print("✓ Screenshot: fuzzy_explore_09_before_profile_click.png")
    
    # Step 22: Click the user-profile-icon
    print("\n→ Step 22: Clicking user-profile-icon...")
    
    profile_click = await client.evaluate("""
        () => {
            const profileIcon = document.querySelector('.user-profile-icon');
            
            if (profileIcon) {
                const rect = profileIcon.getBoundingClientRect();
                console.log('Found profile icon at:', rect);
                
                // Click it
                profileIcon.click();
                
                return {
                    success: true,
                    position: {
                        top: Math.round(rect.top),
                        left: Math.round(rect.left),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }
                };
            }
            
            return { success: false, message: 'Profile icon not found' };
        }
    """)
    
    print(f"  Click result: {profile_click}")
    
    if profile_click['success']:
        print(f"  ✓ Clicked profile icon at ({profile_click['position']['left']}, {profile_click['position']['top']})")
        
        # Wait for any animation/modal
        await client.wait(2000)
        
        # Take screenshot
        await client.screenshot("fuzzy_explore_10_after_profile_click.png")
        print("  ✓ Screenshot: fuzzy_explore_10_after_profile_click.png")
        
        # Check what appeared
        after_click_state = await client.evaluate("""
            () => {
                // Check for iframes
                const iframes = Array.from(document.querySelectorAll('iframe'));
                const visibleIframe = iframes.find(f => f.offsetParent !== null);
                
                // Check for modals
                const modals = Array.from(document.querySelectorAll('[role="dialog"], .modal, [class*="modal"], [class*="popup"]'));
                const visibleModal = modals.find(m => m.offsetParent !== null);
                
                // Check for any new overlays
                const overlays = Array.from(document.querySelectorAll('[class*="overlay"], [class*="backdrop"]'));
                const visibleOverlay = overlays.find(o => o.offsetParent !== null);
                
                return {
                    hasIframe: visibleIframe !== undefined,
                    iframeSrc: visibleIframe?.src,
                    hasModal: visibleModal !== undefined,
                    modalContent: visibleModal ? visibleModal.textContent.substring(0, 100) : null,
                    hasOverlay: visibleOverlay !== undefined
                };
            }
        """)
        
        print("\n  After clicking profile icon:")
        print(f"    Has iframe: {after_click_state['hasIframe']}")
        if after_click_state['iframeSrc']:
            print(f"    Iframe URL: {after_click_state['iframeSrc']}")
        print(f"    Has modal: {after_click_state['hasModal']}")
        if after_click_state['modalContent']:
            print(f"    Modal content preview: {after_click_state['modalContent']}...")
        print(f"    Has overlay: {after_click_state['hasOverlay']}")
        
        # If we have an iframe, check if it's the login form
        if after_click_state['hasIframe'] and 'user_login' in (after_click_state['iframeSrc'] or ''):
            print("\n  ✅ Login iframe opened successfully!")
            
            # Update steps file
            with open("FUZZY_CODE_STEPS.md", "a") as f:
                f.write("\n## Finding Login\n")
                f.write("11. Searched for profile elements - found user-profile-icon class at (49, 375)\n")
                f.write("12. Clicked user-profile-icon which opened login iframe\n")

if __name__ == "__main__":
    asyncio.run(click_profile_icon())