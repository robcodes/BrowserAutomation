#!/usr/bin/env python3
"""
Detailed investigation of the welcome modal structure
"""
from common import *

async def investigate_modal_detailed():
    print_step_header("DETAILED", "Detailed Modal Investigation")
    
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
        await take_screenshot_and_check(client, "modal_detailed_01_initial.png", 
                                      "Current state of the page")
        
        # 1. Look for any element containing the welcome text
        print("\n1. Searching for welcome message...")
        welcome_search = await client.evaluate("""
            (() => {
                const allElements = document.querySelectorAll('*');
                const welcomeElements = [];
                
                allElements.forEach(el => {
                    if (el.textContent && el.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!')) {
                        // Only include if this is the most specific element containing the text
                        const hasChildWithText = Array.from(el.children).some(child => 
                            child.textContent && child.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!')
                        );
                        
                        if (!hasChildWithText) {
                            welcomeElements.push({
                                tagName: el.tagName,
                                className: el.className,
                                id: el.id,
                                parentClassName: el.parentElement ? el.parentElement.className : null,
                                parentId: el.parentElement ? el.parentElement.id : null,
                                display: window.getComputedStyle(el).display,
                                visibility: window.getComputedStyle(el).visibility,
                                position: window.getComputedStyle(el).position,
                                zIndex: window.getComputedStyle(el).zIndex,
                                bounds: el.getBoundingClientRect()
                            });
                        }
                    }
                });
                
                return welcomeElements;
            })()
        """)
        
        print(f"   Found {len(welcome_search)} elements with welcome text:")
        for el in welcome_search:
            print(f"   - {el['tagName']} (class: {el['className']}, display: {el['display']}, visible: {el['visibility']})")
            print(f"     Position: {el['position']}, Z-index: {el['zIndex']}")
            print(f"     Bounds: {el['bounds']}")
        
        # 2. Look for all modal-like elements
        print("\n2. Searching for all modal-like elements...")
        modal_search = await client.evaluate("""
            (() => {
                const modalElements = [];
                
                // Search by class
                const classSelectors = ['.modal', '.popup', '.overlay', '.dialog', '.lightbox'];
                classSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        modalElements.push({
                            selector: selector,
                            tagName: el.tagName,
                            className: el.className,
                            id: el.id,
                            display: window.getComputedStyle(el).display,
                            visibility: window.getComputedStyle(el).visibility,
                            innerHTML: el.innerHTML.substring(0, 100) + '...'
                        });
                    });
                });
                
                // Search by role
                document.querySelectorAll('[role="dialog"], [role="alertdialog"]').forEach(el => {
                    modalElements.push({
                        selector: 'role=' + el.getAttribute('role'),
                        tagName: el.tagName,
                        className: el.className,
                        id: el.id,
                        display: window.getComputedStyle(el).display,
                        visibility: window.getComputedStyle(el).visibility,
                        innerHTML: el.innerHTML.substring(0, 100) + '...'
                    });
                });
                
                // Search by fixed/absolute positioning with high z-index
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    const style = window.getComputedStyle(el);
                    const zIndex = parseInt(style.zIndex);
                    if ((style.position === 'fixed' || style.position === 'absolute') && zIndex > 1000) {
                        modalElements.push({
                            selector: 'high-z-index',
                            tagName: el.tagName,
                            className: el.className,
                            id: el.id,
                            display: style.display,
                            visibility: style.visibility,
                            position: style.position,
                            zIndex: zIndex,
                            innerHTML: el.innerHTML.substring(0, 100) + '...'
                        });
                    }
                });
                
                return modalElements;
            })()
        """)
        
        print(f"   Found {len(modal_search)} modal-like elements:")
        for el in modal_search:
            print(f"   - {el['selector']}: {el['tagName']} (class: {el['className']}, display: {el['display']})")
        
        # 3. Check current page state
        print("\n3. Checking current page state...")
        page_state = await client.evaluate("""
            (() => {
                // Check if any element is blocking interaction
                const centerX = window.innerWidth / 2;
                const centerY = window.innerHeight / 2;
                const elementAtCenter = document.elementFromPoint(centerX, centerY);
                
                return {
                    bodyClass: document.body.className,
                    htmlClass: document.documentElement.className,
                    hasModalBackdrop: document.querySelector('.modal-backdrop') !== null,
                    elementAtCenter: elementAtCenter ? {
                        tagName: elementAtCenter.tagName,
                        className: elementAtCenter.className,
                        id: elementAtCenter.id,
                        text: elementAtCenter.textContent.substring(0, 50)
                    } : null,
                    scrollable: {
                        body: document.body.style.overflow,
                        html: document.documentElement.style.overflow
                    }
                };
            })()
        """)
        
        print(f"   Body class: {page_state['bodyClass']}")
        print(f"   HTML class: {page_state['htmlClass']}")
        print(f"   Has modal backdrop: {page_state['hasModalBackdrop']}")
        print(f"   Element at center: {page_state['elementAtCenter']}")
        print(f"   Overflow styles: {page_state['scrollable']}")
        
        # 4. Try to interact with the page
        print("\n4. Testing page interaction...")
        interaction_test = await client.evaluate("""
            (() => {
                // Check if we can click on elements
                const testButton = document.querySelector('button:not(.modal button)');
                const isClickable = testButton ? true : false;
                
                // Check focus
                const activeElement = document.activeElement;
                
                return {
                    hasInteractableElements: isClickable,
                    activeElement: activeElement ? {
                        tagName: activeElement.tagName,
                        className: activeElement.className,
                        id: activeElement.id
                    } : null
                };
            })()
        """)
        
        print(f"   Can interact with page: {interaction_test['hasInteractableElements']}")
        print(f"   Active element: {interaction_test['activeElement']}")
        
        # 5. Check if the welcome message is actually in a modal
        print("\n5. Analyzing welcome message container hierarchy...")
        hierarchy = await client.evaluate("""
            (() => {
                const welcomeElement = Array.from(document.querySelectorAll('*')).find(el => 
                    el.textContent && el.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!') &&
                    !Array.from(el.children).some(child => 
                        child.textContent && child.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!')
                    )
                );
                
                if (!welcomeElement) return null;
                
                const hierarchy = [];
                let current = welcomeElement;
                while (current && current !== document.body) {
                    hierarchy.push({
                        tagName: current.tagName,
                        className: current.className,
                        id: current.id,
                        display: window.getComputedStyle(current).display,
                        position: window.getComputedStyle(current).position,
                        zIndex: window.getComputedStyle(current).zIndex
                    });
                    current = current.parentElement;
                }
                
                return hierarchy;
            })()
        """)
        
        if hierarchy:
            print("   Element hierarchy (from welcome text up to body):")
            for i, el in enumerate(hierarchy):
                print(f"   {' ' * i}└─ {el['tagName']} (class: {el['className']}, position: {el['position']}, z-index: {el['zIndex']})")
        else:
            print("   Welcome message not found in DOM")
        
        # Take final screenshot
        await take_screenshot_and_check(client, "modal_detailed_02_final.png", 
                                      "Final state after investigation")
        
        print_step_result(True, "Detailed investigation completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during investigation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(investigate_modal_detailed())