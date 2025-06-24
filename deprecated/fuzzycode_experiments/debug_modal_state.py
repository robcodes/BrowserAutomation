#!/usr/bin/env python3
"""Debug the current modal state"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from clients.browser_client_enhanced import EnhancedBrowserClient
from common import load_session_info

async def main():
    session_info = await load_session_info()
    client = EnhancedBrowserClient()
    await client.connect_session(session_info['session_id'])
    await client.set_page(session_info['page_id'])
    
    print("Analyzing page state...\n")
    
    # Comprehensive modal analysis
    analysis = await client.evaluate("""
        (() => {
            // Find all modals
            const allModals = document.querySelectorAll('.modal');
            const modalInfo = [];
            
            allModals.forEach((modal, index) => {
                const style = window.getComputedStyle(modal);
                const rect = modal.getBoundingClientRect();
                
                // Look for close buttons in this modal
                const closeButtons = modal.querySelectorAll('button.close, .close, button[aria-label="Close"], .btn-close, button:contains("×")');
                const allButtons = modal.querySelectorAll('button');
                
                modalInfo.push({
                    index: index,
                    classes: modal.className,
                    id: modal.id,
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    isVisible: modal.offsetParent !== null,
                    hasShowClass: modal.classList.contains('show'),
                    rect: {
                        top: rect.top,
                        left: rect.left,
                        width: rect.width,
                        height: rect.height
                    },
                    closeButtonCount: closeButtons.length,
                    totalButtonCount: allButtons.length,
                    innerHTML: modal.innerHTML.substring(0, 200) + '...'
                });
            });
            
            // Check for modal backdrop
            const backdrop = document.querySelector('.modal-backdrop');
            const backdropInfo = backdrop ? {
                classes: backdrop.className,
                display: window.getComputedStyle(backdrop).display,
                opacity: window.getComputedStyle(backdrop).opacity
            } : null;
            
            // Look for the welcome text
            const welcomeElements = Array.from(document.querySelectorAll('*')).filter(el => 
                el.textContent.includes('Welcome, robert.norbeau+test2@gmail.com!')
            );
            
            // Find X button in header
            const modalHeaders = document.querySelectorAll('.modal-header');
            const xButtons = [];
            modalHeaders.forEach(header => {
                const buttons = header.querySelectorAll('button');
                buttons.forEach(btn => {
                    if (btn.textContent.trim() === '×' || btn.getAttribute('aria-label') === 'Close') {
                        xButtons.push({
                            text: btn.textContent.trim(),
                            classes: btn.className,
                            ariaLabel: btn.getAttribute('aria-label'),
                            type: btn.type,
                            onclick: btn.onclick ? 'has onclick' : 'no onclick'
                        });
                    }
                });
            });
            
            return {
                modalCount: allModals.length,
                modals: modalInfo,
                backdrop: backdropInfo,
                welcomeElementCount: welcomeElements.length,
                bodyClasses: document.body.className,
                xButtons: xButtons
            };
        })()
    """)
    
    print(f"Found {analysis['modalCount']} modal(s)")
    print(f"Body classes: {analysis['bodyClasses']}")
    print(f"Backdrop: {analysis['backdrop']}")
    print(f"Welcome elements: {analysis['welcomeElementCount']}")
    
    for modal in analysis['modals']:
        print(f"\nModal {modal['index']}:")
        print(f"  Classes: {modal['classes']}")
        print(f"  ID: {modal['id']}")
        print(f"  Display: {modal['display']}")
        print(f"  Visibility: {modal['visibility']}")
        print(f"  Has 'show' class: {modal['hasShowClass']}")
        print(f"  Is visible (offsetParent): {modal['isVisible']}")
        print(f"  Close buttons found: {modal['closeButtonCount']}")
        print(f"  Total buttons: {modal['totalButtonCount']}")
        print(f"  Position: top={modal['rect']['top']}, left={modal['rect']['left']}")
        print(f"  Size: {modal['rect']['width']}x{modal['rect']['height']}")
    
    print(f"\nX Buttons found: {len(analysis['xButtons'])}")
    for i, btn in enumerate(analysis['xButtons']):
        print(f"  Button {i}: text='{btn['text']}', aria-label='{btn['ariaLabel']}', classes='{btn['classes']}'")
    
    # Take a screenshot
    await client.screenshot('debug_modal_state.png')
    print("\nScreenshot saved as debug_modal_state.png")

if __name__ == "__main__":
    asyncio.run(main())