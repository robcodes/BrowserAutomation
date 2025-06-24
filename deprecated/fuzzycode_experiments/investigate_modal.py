#!/usr/bin/env python3
"""
Investigate the welcome modal structure to find how to close it
"""
from common import *

async def investigate_modal():
    print_step_header("INVESTIGATE", "Modal Structure Investigation")
    
    # Load session info
    session_info = await load_session_info()
    if not session_info:
        print("❌ No session info found!")
        return False
    
    print(f"📋 Session ID: {session_info['session_id']}")
    print(f"📋 Page ID: {session_info['page_id']}")
    
    # Connect to existing session
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    try:
        # Take initial screenshot
        await take_screenshot_and_check(client, "modal_investigation_01_initial.png", 
                                      "Current state with modal visible")
        
        # 1. Get comprehensive modal structure
        print("\n1. Analyzing modal structure...")
        modal_info = await client.evaluate("""
            (() => {
                // Try different ways to find the modal
                let modal = document.querySelector('.modal.show');
                if (!modal) modal = document.querySelector('.modal[style*="display: block"]');
                if (!modal) modal = document.querySelector('.modal[style*="display:block"]');
                if (!modal) modal = document.querySelector('[role="dialog"]');
                if (!modal) {
                    // Look for any element with modal-like content
                    const welcomeElements = Array.from(document.querySelectorAll('*')).filter(el => 
                        el.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!') &&
                        !el.querySelector('*:not(script):not(style)') // leaf elements
                    );
                    if (welcomeElements.length > 0) {
                        // Find the modal container
                        let current = welcomeElements[0];
                        while (current && current.parentElement) {
                            if (current.className && (current.className.includes('modal') || 
                                current.getAttribute('role') === 'dialog' ||
                                current.className.includes('overlay') ||
                                current.className.includes('popup'))) {
                                modal = current;
                                break;
                            }
                            current = current.parentElement;
                        }
                    }
                }
                
                if (!modal) return { found: false, searchMethod: 'none found' };
                
                // Get all interactive elements
                const buttons = Array.from(modal.querySelectorAll('button')).map(btn => ({
                    text: btn.textContent.trim(),
                    class: btn.className,
                    onclick: btn.onclick ? 'has onclick' : 'no onclick',
                    disabled: btn.disabled,
                    type: btn.type,
                    ariaLabel: btn.getAttribute('aria-label'),
                    dataAttributes: Object.keys(btn.dataset)
                }));
                
                const closeButtons = Array.from(modal.querySelectorAll('.close, .btn-close, [aria-label*="close"], [aria-label*="Close"], button[class*="close"]')).map(btn => ({
                    text: btn.textContent.trim(),
                    class: btn.className,
                    tagName: btn.tagName,
                    ariaLabel: btn.getAttribute('aria-label')
                }));
                
                // Check modal header
                const modalHeader = modal.querySelector('.modal-header');
                const headerButtons = modalHeader ? Array.from(modalHeader.querySelectorAll('button, .close, .btn-close')).map(btn => ({
                    text: btn.textContent.trim(),
                    class: btn.className,
                    ariaLabel: btn.getAttribute('aria-label')
                })) : [];
                
                // Check for backdrop
                const backdrop = document.querySelector('.modal-backdrop');
                
                // Get modal classes and attributes
                const modalAttributes = {
                    class: modal.className,
                    id: modal.id,
                    role: modal.getAttribute('role'),
                    ariaModal: modal.getAttribute('aria-modal'),
                    ariaLabelledby: modal.getAttribute('aria-labelledby'),
                    dataBackdrop: modal.getAttribute('data-backdrop'),
                    dataBsDismiss: modal.getAttribute('data-bs-dismiss'),
                    dataKeyboard: modal.getAttribute('data-keyboard'),
                    tabindex: modal.getAttribute('tabindex'),
                    style: modal.getAttribute('style')
                };
                
                // Check parent elements
                const parentInfo = {
                    parentClass: modal.parentElement ? modal.parentElement.className : null,
                    parentId: modal.parentElement ? modal.parentElement.id : null
                };
                
                return {
                    found: true,
                    buttons: buttons,
                    closeButtons: closeButtons,
                    headerButtons: headerButtons,
                    hasBackdrop: backdrop !== null,
                    backdropClass: backdrop ? backdrop.className : null,
                    modalAttributes: modalAttributes,
                    parentInfo: parentInfo,
                    innerHTML: modal.innerHTML.substring(0, 500) + '...'
                };
            })()
        """)
        
        print(f"   Modal found: {modal_info['found']}")
        if modal_info['found']:
            print(f"   Modal attributes: {modal_info['modalAttributes']}")
            print(f"   All buttons: {modal_info['buttons']}")
            print(f"   Close buttons found: {modal_info['closeButtons']}")
            print(f"   Header buttons: {modal_info['headerButtons']}")
            print(f"   Has backdrop: {modal_info['hasBackdrop']}")
            print(f"   Parent info: {modal_info['parentInfo']}")
        
        # 2. Check for hidden close buttons by exploring the full modal HTML
        print("\n2. Searching for hidden close elements...")
        hidden_elements = await client.evaluate("""
            (() => {
                // Find modal using same logic as before
                let modal = document.querySelector('.modal.show');
                if (!modal) modal = document.querySelector('.modal[style*="display: block"]');
                if (!modal) modal = document.querySelector('.modal[style*="display:block"]');
                if (!modal) modal = document.querySelector('[role="dialog"]');
                if (!modal) {
                    const welcomeElements = Array.from(document.querySelectorAll('*')).filter(el => 
                        el.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!')
                    );
                    if (welcomeElements.length > 0) {
                        let current = welcomeElements[0];
                        while (current && current.parentElement) {
                            if (current.className && (current.className.includes('modal') || 
                                current.getAttribute('role') === 'dialog')) {
                                modal = current;
                                break;
                            }
                            current = current.parentElement;
                        }
                    }
                }
                
                if (!modal) return { found: false, closeElements: [] };
                
                // Look for any element that might close the modal
                const potentialCloseElements = modal.querySelectorAll('*');
                const closeElements = [];
                
                potentialCloseElements.forEach(el => {
                    const text = el.textContent.trim().toLowerCase();
                    const className = (el.className || '').toString().toLowerCase();
                    const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                    const role = (el.getAttribute('role') || '').toLowerCase();
                    const onclick = el.onclick;
                    const dataDismiss = el.getAttribute('data-dismiss') || el.getAttribute('data-bs-dismiss');
                    
                    if (
                        className.includes('close') ||
                        ariaLabel.includes('close') ||
                        text === 'x' || text === '×' ||
                        dataDismiss === 'modal' ||
                        (onclick && onclick.toString().includes('close'))
                    ) {
                        closeElements.push({
                            tagName: el.tagName,
                            text: el.textContent.trim(),
                            class: el.className,
                            ariaLabel: el.getAttribute('aria-label'),
                            dataDismiss: dataDismiss,
                            hidden: el.offsetParent === null,
                            display: window.getComputedStyle(el).display,
                            visibility: window.getComputedStyle(el).visibility,
                            opacity: window.getComputedStyle(el).opacity,
                            position: window.getComputedStyle(el).position,
                            bounds: el.getBoundingClientRect()
                        });
                    }
                });
                
                return {
                    found: true,
                    closeElements: closeElements
                };
            })()
        """)
        
        print(f"   Potential close elements: {hidden_elements.get('closeElements', [])}")
        
        # 3. Try clicking on backdrop
        print("\n3. Testing backdrop click...")
        backdrop_result = await client.evaluate("""
            (() => {
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    // Check if backdrop has event listeners
                    const hasListeners = backdrop.onclick !== null;
                    
                    // Try to click it
                    backdrop.click();
                    
                    // Check if modal is still visible after a short delay
                    return new Promise(resolve => {
                        setTimeout(() => {
                            const modalStillVisible = document.querySelector('.modal.show') !== null;
                            resolve({
                                backdropFound: true,
                                hasListeners: hasListeners,
                                modalStillVisible: modalStillVisible
                            });
                        }, 500);
                    });
                } else {
                    return { backdropFound: false };
                }
            })()
        """)
        
        print(f"   Backdrop test result: {backdrop_result}")
        
        await wait_and_check(client, WAIT_SHORT, "Checking if backdrop click worked")
        await take_screenshot_and_check(client, "modal_investigation_02_after_backdrop.png", 
                                      "After backdrop click attempt")
        
        # 4. Try ESC key
        print("\n4. Testing ESC key...")
        await client.evaluate("""
            (() => {
                // Focus the modal first
                let modal = document.querySelector('.modal.show');
                if (!modal) modal = document.querySelector('.modal[style*="display: block"]');
                if (!modal) modal = document.querySelector('.modal[style*="display:block"]');
                if (!modal) modal = document.querySelector('[role="dialog"]');
                
                if (modal) {
                    modal.focus();
                    
                    // Dispatch ESC key event
                    const event = new KeyboardEvent('keydown', {
                        key: 'Escape',
                        code: 'Escape',
                        keyCode: 27,
                        which: 27,
                        bubbles: true,
                        cancelable: true
                    });
                    modal.dispatchEvent(event);
                    document.dispatchEvent(event);
                }
            })()
        """)
        
        await wait_and_check(client, WAIT_SHORT, "Checking if ESC key worked")
        
        esc_result = await client.evaluate("""
            (() => {
                const modalShow = document.querySelector('.modal.show');
                const modalBlock = document.querySelector('.modal[style*="display: block"]');
                const modalBlock2 = document.querySelector('.modal[style*="display:block"]');
                const dialog = document.querySelector('[role="dialog"]');
                
                return {
                    modalStillVisible: modalShow !== null || modalBlock !== null || modalBlock2 !== null || dialog !== null
                };
            })()
        """)
        
        print(f"   ESC key result - Modal still visible: {esc_result['modalStillVisible']}")
        
        await take_screenshot_and_check(client, "modal_investigation_03_after_esc.png", 
                                      "After ESC key attempt")
        
        # 5. Look for Bootstrap modal methods
        print("\n5. Checking for Bootstrap modal instance...")
        bootstrap_result = await client.evaluate("""
            (() => {
                let modal = document.querySelector('.modal.show');
                if (!modal) modal = document.querySelector('.modal[style*="display: block"]');
                if (!modal) modal = document.querySelector('.modal[style*="display:block"]');
                if (!modal) modal = document.querySelector('[role="dialog"]');
                if (!modal) return { found: false };
                
                // Try different Bootstrap versions
                let modalInstance = null;
                
                // Bootstrap 5
                if (window.bootstrap && window.bootstrap.Modal) {
                    modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                        return { found: true, version: 'Bootstrap 5', hidden: true };
                    }
                }
                
                // Bootstrap 4 with jQuery
                if (window.$ && $.fn.modal) {
                    $(modal).modal('hide');
                    return { found: true, version: 'Bootstrap 4 (jQuery)', hidden: true };
                }
                
                // Check if modal has _modal property (some Bootstrap implementations)
                if (modal._modal && modal._modal.hide) {
                    modal._modal.hide();
                    return { found: true, version: 'Custom implementation', hidden: true };
                }
                
                return { found: false };
            })()
        """)
        
        print(f"   Bootstrap modal result: {bootstrap_result}")
        
        await wait_and_check(client, WAIT_SHORT, "Checking if Bootstrap method worked")
        await take_screenshot_and_check(client, "modal_investigation_04_after_bootstrap.png", 
                                      "After Bootstrap hide attempt")
        
        # 6. Try removing modal classes directly
        print("\n6. Attempting to remove modal directly...")
        removal_result = await client.evaluate("""
            (() => {
                let modal = document.querySelector('.modal.show');
                if (!modal) modal = document.querySelector('.modal[style*="display: block"]');
                if (!modal) modal = document.querySelector('.modal[style*="display:block"]');
                if (!modal) modal = document.querySelector('[role="dialog"]');
                
                const backdrop = document.querySelector('.modal-backdrop');
                
                if (modal) {
                    // Remove the 'show' class
                    modal.classList.remove('show');
                    
                    // Hide it with style
                    modal.style.display = 'none';
                    
                    // Remove backdrop
                    if (backdrop) {
                        backdrop.remove();
                    }
                    
                    // Remove body modal-open class
                    document.body.classList.remove('modal-open');
                    
                    return { success: true };
                }
                
                return { success: false };
            })()
        """)
        
        print(f"   Direct removal result: {removal_result}")
        
        await wait_and_check(client, WAIT_SHORT, "Checking if direct removal worked")
        await take_screenshot_and_check(client, "modal_investigation_05_after_removal.png", 
                                      "After direct removal attempt")
        
        # 7. Final check - is modal gone?
        print("\n7. Final verification...")
        final_check = await client.evaluate("""
            (() => {
                return {
                    modalVisible: document.querySelector('.modal.show') !== null,
                    anyModalVisible: document.querySelector('.modal[style*="display: block"]') !== null,
                    anyModalVisible2: document.querySelector('.modal[style*="display:block"]') !== null,
                    dialogVisible: document.querySelector('[role="dialog"]') !== null,
                    backdropPresent: document.querySelector('.modal-backdrop') !== null,
                    bodyHasModalOpen: document.body.classList.contains('modal-open')
                };
            })()
        """)
        
        print(f"   Final state:")
        print(f"   - Modal with 'show' class: {final_check['modalVisible']}")
        print(f"   - Any visible modal (display: block): {final_check['anyModalVisible']}")
        print(f"   - Any visible modal (display:block): {final_check['anyModalVisible2']}")
        print(f"   - Dialog element visible: {final_check['dialogVisible']}")
        print(f"   - Backdrop present: {final_check['backdropPresent']}")
        print(f"   - Body has modal-open class: {final_check['bodyHasModalOpen']}")
        
        # Document what worked
        if not final_check['modalVisible'] and not final_check['anyModalVisible'] and not final_check['anyModalVisible2'] and not final_check['dialogVisible']:
            print("\n✅ SUCCESS! Modal was closed using direct removal method:")
            print("   1. Remove 'show' class from modal")
            print("   2. Set modal display to 'none'")
            print("   3. Remove backdrop element")
            print("   4. Remove 'modal-open' class from body")
        else:
            print("\n❌ Modal is still visible. Need to investigate further.")
        
        print_step_result(True, "Investigation completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during investigation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(investigate_modal())