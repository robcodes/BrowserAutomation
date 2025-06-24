#!/usr/bin/env python3
"""
Step 5: Close the welcome modal after login (Fixed Version)
The modal shows "Welcome, [email]!" inside a "User Login" modal with an X button.
"""
from common import *

async def close_modal():
    print_step_header(5, "Close Welcome Modal")
    
    # Load session info
    session_info = await load_session_info()
    if not session_info:
        print("❌ No session info found! Run previous steps first.")
        return False
    
    print(f"📋 Session ID: {session_info['session_id']}")
    print(f"📋 Page ID: {session_info['page_id']}")
    
    # Connect to existing session
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        # Take initial screenshot
        await take_screenshot_and_check(client, "step05_01_modal_visible.png", 
                                      "Welcome modal should be visible")
        
        # Check if modal is present
        print("\n1. Checking for welcome modal...")
        modal_check = await client.evaluate("""
            (() => {
                // Check for any visible modal
                let modal = document.querySelector('.modal.show');
                if (!modal) modal = document.querySelector('.modal[style*="display: block"]');
                if (!modal) modal = document.querySelector('.modal[style*="display:block"]');
                if (!modal) modal = document.querySelector('[role="dialog"]');
                
                // Check for close button
                let closeButton = null;
                if (modal) {
                    // Look for X button in modal header
                    closeButton = modal.querySelector('.modal-header button.close, .modal-header .close, button[aria-label="Close"], .btn-close');
                    if (!closeButton) {
                        // Try broader search
                        closeButton = modal.querySelector('button.close, .close, [data-dismiss="modal"], [data-bs-dismiss="modal"]');
                    }
                }
                
                // Also check for welcome text
                const hasWelcomeText = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
                
                return {
                    modalFound: modal !== null,
                    modalDisplay: modal ? window.getComputedStyle(modal).display : null,
                    hasWelcomeText: hasWelcomeText,
                    modalClass: modal ? modal.className : null,
                    closeButtonFound: closeButton !== null,
                    closeButtonText: closeButton ? closeButton.textContent.trim() : null,
                    closeButtonClass: closeButton ? closeButton.className : null
                };
            })()
        """)
        
        print(f"   Modal found: {modal_check['modalFound']}")
        print(f"   Has welcome text: {modal_check['hasWelcomeText']}")
        print(f"   Close button found: {modal_check['closeButtonFound']}")
        if modal_check['closeButtonFound']:
            print(f"   Close button text: '{modal_check['closeButtonText']}'")
            print(f"   Close button class: {modal_check['closeButtonClass']}")
        
        if not modal_check['modalFound'] and not modal_check['hasWelcomeText']:
            print("   ✓ Modal is already closed!")
            await save_session_info(session_info['session_id'], session_info['page_id'], 5)
            print_step_result(True, "Modal was already closed")
            return True
        
        # Try clicking the X close button first
        if modal_check['closeButtonFound']:
            print("\n2. Clicking the X close button...")
            try:
                # Try multiple selectors for the close button
                close_selectors = [
                    '.modal.show .modal-header button.close',
                    '.modal.show .modal-header .close',
                    '.modal.show button[aria-label="Close"]',
                    '.modal.show .btn-close',
                    '.modal .modal-header button.close',
                    '.modal button[aria-label="Close"]',
                    'button.close:visible'
                ]
                
                clicked = False
                for selector in close_selectors:
                    try:
                        # Check if element exists before clicking
                        exists = await client.evaluate(f'document.querySelector("{selector}") !== null')
                        if exists:
                            print(f"   Trying selector: {selector}")
                            await client.click(selector)
                            clicked = True
                            break
                    except:
                        continue
                
                if clicked:
                    await wait_and_check(client, WAIT_MEDIUM, "Waiting for modal to close")
                    
                    # Check if it worked
                    close_check = await client.evaluate("""
                        (() => {
                            let modal = document.querySelector('.modal.show');
                            if (!modal) modal = document.querySelector('.modal[style*="display: block"]');
                            const hasWelcomeText = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
                            
                            return {
                                modalStillVisible: modal !== null && window.getComputedStyle(modal).display !== 'none',
                                hasWelcomeText: hasWelcomeText
                            };
                        })()
                    """)
                    
                    if not close_check['modalStillVisible'] and not close_check['hasWelcomeText']:
                        print("   ✓ X button successfully closed the modal!")
                        await take_screenshot_and_check(client, "step05_02_modal_closed.png", 
                                                      "Modal should be closed")
                        await save_session_info(session_info['session_id'], session_info['page_id'], 5)
                        print_step_result(True, "Modal closed with X button")
                        return True
            except Exception as e:
                print(f"   Could not click close button: {e}")
        
        # Try ESC key as second option
        print("\n3. Attempting to close modal with ESC key...")
        await client.evaluate("""
            (() => {
                // Dispatch ESC key event at document level
                const event = new KeyboardEvent('keydown', {
                    key: 'Escape',
                    code: 'Escape',
                    keyCode: 27,
                    which: 27,
                    bubbles: true,
                    cancelable: true
                });
                document.dispatchEvent(event);
                
                // Also try on the modal itself
                let modal = document.querySelector('.modal.show');
                if (!modal) modal = document.querySelector('.modal[style*="display: block"]');
                if (modal) {
                    modal.dispatchEvent(event);
                }
            })()
        """)
        
        await wait_and_check(client, WAIT_SHORT, "Waiting for modal to close")
        
        # Check if ESC worked
        esc_check = await client.evaluate("""
            (() => {
                let modal = document.querySelector('.modal.show');
                if (!modal) modal = document.querySelector('.modal[style*="display: block"]');
                const hasWelcomeText = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
                
                return {
                    modalStillVisible: modal !== null && window.getComputedStyle(modal).display !== 'none',
                    hasWelcomeText: hasWelcomeText
                };
            })()
        """)
        
        if not esc_check['modalStillVisible'] and not esc_check['hasWelcomeText']:
            print("   ✓ ESC key successfully closed the modal!")
            await take_screenshot_and_check(client, "step05_03_modal_closed_esc.png", 
                                          "Modal should be closed")
            await save_session_info(session_info['session_id'], session_info['page_id'], 5)
            print_step_result(True, "Modal closed with ESC key")
            return True
        
        # If nothing else worked, try direct removal
        print("\n4. Other methods didn't work, attempting direct removal...")
        await client.evaluate("""
            (() => {
                // Find and remove modal
                let modal = document.querySelector('.modal.show');
                if (!modal) modal = document.querySelector('.modal[style*="display: block"]');
                if (!modal) modal = document.querySelector('[role="dialog"]');
                
                if (modal) {
                    // Remove show class
                    modal.classList.remove('show');
                    
                    // Hide with style
                    modal.style.display = 'none';
                }
                
                // Remove backdrop
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
                
                // Remove modal-open class from body
                document.body.classList.remove('modal-open');
                
                // Restore body overflow
                document.body.style.overflow = '';
                document.documentElement.style.overflow = '';
            })()
        """)
        
        await wait_and_check(client, WAIT_SHORT, "Waiting for direct removal to take effect")
        
        # Final verification
        final_check = await client.evaluate("""
            (() => {
                let modal = document.querySelector('.modal');
                const hasWelcomeText = document.body.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!');
                const backdrop = document.querySelector('.modal-backdrop');
                
                return {
                    modalGone: !modal || window.getComputedStyle(modal).display === 'none',
                    welcomeTextGone: !hasWelcomeText,
                    backdropGone: !backdrop
                };
            })()
        """)
        
        if final_check['modalGone'] and final_check['welcomeTextGone'] and final_check['backdropGone']:
            print("   ✓ Modal successfully removed via direct DOM manipulation!")
            await take_screenshot_and_check(client, "step05_04_modal_removed.png", 
                                          "Page after modal removal")
            await save_session_info(session_info['session_id'], session_info['page_id'], 5)
            print_step_result(True, "Modal closed via direct removal")
            return True
        else:
            print("   ❌ Failed to close modal")
            print(f"   Modal gone: {final_check['modalGone']}")
            print(f"   Welcome text gone: {final_check['welcomeTextGone']}")
            print(f"   Backdrop gone: {final_check['backdropGone']}")
            print_step_result(False, "Could not close modal")
            return False
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print_step_result(False, f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(close_modal())