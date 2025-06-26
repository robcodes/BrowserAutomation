#!/usr/bin/env python3
"""
Test the crosshair matcher by finding and clicking the X close button in the modal
"""
import asyncio
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from common import (
    BrowserClient, load_session_info, save_session_info,
    take_screenshot_and_check, wait_and_check,
    print_step_header, print_step_result,
    WAIT_SHORT, WAIT_MEDIUM
)
from gemini_crosshair_matcher import click_element_with_crosshairs

# Gemini API key (from documentation)
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"


async def test_crosshair_close():
    """Test closing the modal using crosshair matching"""
    print_step_header("TEST", "Crosshair Matcher - Close Modal")
    
    # Load session
    session_info = await load_session_info()
    if not session_info:
        print("❌ No session info found. Run steps 1-4 first.")
        return False
    
    # Connect to existing session
    client = BrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    print("\n1. Taking initial screenshot to verify modal is open...")
    await take_screenshot_and_check(client, "crosshair_test_before.png", 
                                   "Modal should be visible with X button in top-right")
    
    # Check if modal is actually present - try multiple selectors
    modal_check = await client.evaluate("""
        (() => {
            // Try various modal selectors
            const modalSelectors = [
                '.Modal', '.modal', '[role="dialog"]', 
                '.MuiModal-root', '.MuiDialog-root',
                'div[class*="modal" i]'  // case insensitive
            ];
            
            let modal = null;
            let modalSelector = null;
            
            for (const sel of modalSelectors) {
                modal = document.querySelector(sel);
                if (modal) {
                    modalSelector = sel;
                    break;
                }
            }
            
            // Also check for any div with position fixed that might be a modal
            if (!modal) {
                const fixedDivs = document.querySelectorAll('div[style*="position: fixed"]');
                for (const div of fixedDivs) {
                    const rect = div.getBoundingClientRect();
                    // Check if it's centered and reasonably sized
                    if (rect.width > 300 && rect.height > 200 && 
                        rect.left > 50 && rect.top > 50) {
                        modal = div;
                        modalSelector = 'fixed positioned div';
                        break;
                    }
                }
            }
            
            return {
                modalExists: modal !== null,
                modalSelector: modalSelector,
                modalVisible: modal ? window.getComputedStyle(modal).display !== 'none' : false
            };
        })()
    """)
    
    print(f"\n   Modal state: {modal_check}")
    
    if not modal_check['modalExists']:
        print("❌ Modal not found. Make sure to run steps 1-4 first.")
        print("   Let's continue anyway to see if we can find the X button...")
        # Don't return False - continue to try finding the X button
    
    print("\n2. Using crosshair matcher to find and click the X button...")
    
    # Try multiple descriptions to find the X button
    descriptions_to_try = [
        "X close button in the top right corner of the modal dialog",
        "X button in the modal header",
        "close button (X) in the upper right of the modal",
        "modal close X icon in the top right"
    ]
    
    success = False
    for description in descriptions_to_try:
        print(f"\n   Trying: '{description}'")
        
        try:
            clicked = await click_element_with_crosshairs(
                client, 
                description, 
                GEMINI_API_KEY,
                f"crosshair_attempt_{descriptions_to_try.index(description)}.png"
            )
            
            if clicked:
                print("   ✓ Click executed")
                await wait_and_check(client, WAIT_MEDIUM, "Waiting for modal to close")
                
                # Check if modal is closed
                modal_closed = await client.evaluate("""
                    (() => {
                        // Check all possible modal selectors
                        const modalSelectors = [
                            '.Modal', '.modal', '[role="dialog"]', 
                            '.MuiModal-root', '.MuiDialog-root',
                            'div[class*="modal" i]'
                        ];
                        
                        let anyModalFound = false;
                        let anyModalVisible = false;
                        
                        for (const sel of modalSelectors) {
                            const modal = document.querySelector(sel);
                            if (modal) {
                                anyModalFound = true;
                                if (window.getComputedStyle(modal).display !== 'none') {
                                    anyModalVisible = true;
                                }
                            }
                        }
                        
                        // Also check fixed divs
                        const fixedDivs = document.querySelectorAll('div[style*="position: fixed"]');
                        let largeDivCount = 0;
                        for (const div of fixedDivs) {
                            const rect = div.getBoundingClientRect();
                            if (rect.width > 300 && rect.height > 200 && 
                                rect.left > 50 && rect.top > 50) {
                                largeDivCount++;
                            }
                        }
                        
                        return {
                            modalGone: !anyModalFound,
                            modalHidden: !anyModalVisible,
                            largeDivCount: largeDivCount
                        };
                    })()
                """)
                
                print(f"   Modal state after click: {modal_closed}")
                
                if modal_closed['modalGone'] or modal_closed['modalHidden']:
                    success = True
                    break
                else:
                    print("   ⚠️  Modal still visible, trying next description...")
            else:
                print("   ❌ Could not find element with this description")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Take final screenshot
    await wait_and_check(client, WAIT_SHORT, "Taking final screenshot")
    await take_screenshot_and_check(client, "crosshair_test_after.png", 
                                   "Modal should be closed if successful")
    
    # Final verification
    if success:
        print_step_result(True, "Successfully closed modal using crosshair matcher!")
        
        # Save session for next steps
        await save_session_info(session_info['session_id'], session_info['page_id'], "crosshair_test")
    else:
        print_step_result(False, "Could not close modal with crosshair matcher")
        
        # Let's also save the crosshair images for debugging
        print("\n📸 Check the crosshair images in /home/ubuntu/browser_automation/screenshots/")
        print("   Look for files ending with '_crosshairs.png' to see what Gemini detected")
    
    return success


async def main():
    """Run the test"""
    try:
        success = await test_crosshair_close()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)