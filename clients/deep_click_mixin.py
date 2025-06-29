#!/usr/bin/env python3
"""
Enhanced click implementation with deep element detection for iframes and shadow DOM
"""
from typing import Dict, Any, Optional, List, Tuple
import json

class DeepClickMixin:
    """
    Mixin class that provides deep click functionality for browser automation.
    This can be mixed into CrosshairBrowserClient to enhance its clicking capabilities.
    """
    
    # JavaScript implementation of deepElementsFromPoint
    DEEP_ELEMENTS_FROM_POINT_JS = """
    function deepElementsFromPoint(x, y, rootDoc = document, path = []) {
        const results = [];
        
        // Get all elements at this point in the current document
        const elements = rootDoc.elementsFromPoint(x, y);
        
        for (const element of elements) {
            // Create element info
            const elementInfo = {
                tagName: element.tagName.toLowerCase(),
                id: element.id || '',
                className: element.className || '',
                text: element.textContent ? element.textContent.substring(0, 50) : '',
                type: element.type || '',
                href: element.href || '',
                isClickable: isClickableElement(element),
                path: [...path],
                element: element,
                context: path.length > 0 ? path[path.length - 1].type : 'document'
            };
            
            results.push(elementInfo);
            
            // Check for shadow root
            if (element.shadowRoot) {
                try {
                    const shadowPath = [...path, {type: 'shadow', host: element.tagName}];
                    const shadowResults = deepElementsFromPoint(x, y, element.shadowRoot, shadowPath);
                    results.push(...shadowResults);
                } catch (e) {
                    console.warn('Error accessing shadow root:', e);
                }
            }
            
            // Check for iframe
            if (element.tagName.toLowerCase() === 'iframe') {
                try {
                    const iframeDoc = element.contentDocument || element.contentWindow?.document;
                    if (iframeDoc) {
                        // Transform coordinates to iframe space
                        const rect = element.getBoundingClientRect();
                        const iframeX = x - rect.left;
                        const iframeY = y - rect.top;
                        
                        // Only search if coordinates are within iframe bounds
                        if (iframeX >= 0 && iframeY >= 0 && 
                            iframeX <= rect.width && iframeY <= rect.height) {
                            
                            const iframePath = [...path, {
                                type: 'iframe', 
                                src: element.src || 'about:blank',
                                id: element.id || '',
                                index: Array.from(rootDoc.querySelectorAll('iframe')).indexOf(element)
                            }];
                            
                            const iframeResults = deepElementsFromPoint(
                                iframeX, 
                                iframeY, 
                                iframeDoc, 
                                iframePath
                            );
                            results.push(...iframeResults);
                        }
                    }
                } catch (e) {
                    // Cross-origin iframe or other access error
                    console.warn('Cannot access iframe:', element.src || 'unknown', e.message);
                    results.push({
                        tagName: 'iframe',
                        id: element.id || '',
                        className: element.className || '',
                        text: '[Cross-origin iframe]',
                        isClickable: false,
                        path: [...path],
                        error: 'cross-origin',
                        context: 'iframe-blocked'
                    });
                }
            }
        }
        
        return results;
    }
    
    function isClickableElement(element) {
        const clickableTags = ['a', 'button', 'input', 'select', 'textarea', 'label'];
        const tag = element.tagName.toLowerCase();
        
        // Check if it's a naturally clickable element
        if (clickableTags.includes(tag)) return true;
        
        // Check for click handlers
        if (element.onclick) return true;
        
        // Check for role attributes
        const role = element.getAttribute('role');
        if (['button', 'link', 'menuitem', 'tab'].includes(role)) return true;
        
        // Check for cursor style
        const cursor = window.getComputedStyle(element).cursor;
        if (cursor === 'pointer') return true;
        
        // Check for contenteditable
        if (element.contentEditable === 'true') return true;
        
        return false;
    }
    """
    
    async def click_at_with_deep_detection(self, 
                                         x: float, 
                                         y: float, 
                                         label: str = "deep_click",
                                         fallback_to_native: bool = True) -> Dict[str, Any]:
        """
        Enhanced click method that uses deepElementsFromPoint to handle iframes and shadow DOM.
        
        Args:
            x: X coordinate to click
            y: Y coordinate to click  
            label: Label for debugging/screenshots
            fallback_to_native: Whether to fall back to native mouse click if JS click fails
            
        Returns:
            Dict with click result, element info, and debugging details
        """
        # Round coordinates
        x = round(x)
        y = round(y)
        
        # First, inject the deepElementsFromPoint function if needed
        await self.evaluate(f"""
            if (typeof deepElementsFromPoint === 'undefined') {{
                {self.DEEP_ELEMENTS_FROM_POINT_JS}
            }}
        """)
        
        # Find all elements at the target coordinates
        deep_elements = await self.evaluate(f"""
            (() => {{
                try {{
                    const elements = deepElementsFromPoint({x}, {y});
                    
                    // Convert element references to serializable data
                    return elements.map((info, index) => {{
                        const serializable = {{
                            index: index,
                            tagName: info.tagName,
                            id: info.id,
                            className: info.className,
                            text: info.text,
                            type: info.type,
                            href: info.href,
                            isClickable: info.isClickable,
                            path: info.path,
                            context: info.context,
                            error: info.error
                        }};
                        
                        // Store element reference for later use
                        window.__deepClickElements = window.__deepClickElements || [];
                        window.__deepClickElements[index] = info.element;
                        
                        return serializable;
                    }});
                }} catch (e) {{
                    console.error('deepElementsFromPoint error:', e);
                    return [];
                }}
            }})()
        """)
        
        # Log what we found
        print(f"\n🔍 Deep element detection at ({x}, {y}):")
        print(f"   Found {len(deep_elements)} elements")
        
        # Find the best element to click
        target_element = None
        target_index = -1
        
        # First pass: find clickable elements
        for i, elem in enumerate(deep_elements):
            if elem.get('error') == 'cross-origin':
                print(f"   [{i}] ❌ {elem['tagName']} - Cross-origin iframe")
                continue
                
            context = elem.get('context', 'document')
            path_str = ' > '.join([p['type'] for p in elem.get('path', [])])
            if path_str:
                context = f"{context} ({path_str})"
                
            print(f"   [{i}] {elem['tagName']}#{elem['id'] or 'no-id'}.{elem['className'] or 'no-class'} "
                  f"[{context}] {'✓ clickable' if elem['isClickable'] else ''}")
            
            # Prioritize clickable elements
            if elem['isClickable'] and target_element is None:
                target_element = elem
                target_index = i
        
        # Second pass: if no clickable element, take the most specific (deepest) element
        if target_element is None and deep_elements:
            # Filter out large container elements
            candidates = [e for e in deep_elements if e['tagName'] not in ['html', 'body', 'div', 'section', 'main']]
            if candidates:
                # Pick the element with the longest path (deepest in DOM)
                target_element = max(candidates, key=lambda e: len(e.get('path', [])))
                target_index = deep_elements.index(target_element)
            else:
                # Fall back to the first element
                target_element = deep_elements[0]
                target_index = 0
        
        click_success = False
        click_error = None
        
        if target_element:
            print(f"\n🎯 Target element: [{target_index}] {target_element['tagName']}#{target_element['id']}")
            
            # Try to click the element using multiple methods
            click_result = await self.evaluate(f"""
                (() => {{
                    const targetElement = window.__deepClickElements && window.__deepClickElements[{target_index}];
                    
                    if (!targetElement) {{
                        return {{
                            success: false,
                            error: 'Element reference lost'
                        }};
                    }}
                    
                    console.log('Deep clicking on:', targetElement);
                    
                    try {{
                        // Method 1: Direct click
                        targetElement.click();
                        
                        // Method 2: Focus and click (for form elements)
                        if (typeof targetElement.focus === 'function') {{
                            targetElement.focus();
                        }}
                        
                        // Method 3: Dispatch mouse events
                        const mousedownEvent = new MouseEvent('mousedown', {{
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: {x},
                            clientY: {y}
                        }});
                        
                        const mouseupEvent = new MouseEvent('mouseup', {{
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: {x},
                            clientY: {y}
                        }});
                        
                        const clickEvent = new MouseEvent('click', {{
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: {x},
                            clientY: {y}
                        }});
                        
                        targetElement.dispatchEvent(mousedownEvent);
                        targetElement.dispatchEvent(mouseupEvent);
                        targetElement.dispatchEvent(clickEvent);
                        
                        return {{
                            success: true,
                            element: {{
                                tagName: targetElement.tagName,
                                id: targetElement.id,
                                className: targetElement.className,
                                text: targetElement.textContent ? targetElement.textContent.substring(0, 50) : ''
                            }}
                        }};
                    }} catch (e) {{
                        return {{
                            success: false,
                            error: e.message
                        }};
                    }}
                }})()
            """)
            
            click_success = click_result.get('success', False)
            click_error = click_result.get('error')
            
            if click_success:
                print("   ✅ JavaScript click succeeded")
            else:
                print(f"   ⚠️  JavaScript click failed: {click_error}")
        else:
            print("\n⚠️  No elements found at target coordinates")
        
        # Fall back to native mouse click if needed
        native_click_result = None
        if fallback_to_native and (not click_success or not target_element):
            print("\n🔄 Falling back to native mouse click...")
            
            # Use the execute_command method if available (for CrosshairBrowserClient)
            if hasattr(self, 'execute_command') and hasattr(self, '_session_id') and hasattr(self, '_page_id'):
                try:
                    native_result = await self.execute_command(
                        self._session_id,
                        self._page_id,
                        f"page.mouse.click({x}, {y})"
                    )
                    native_click_result = {
                        'success': native_result.get('success', False),
                        'method': 'playwright_native'
                    }
                    if native_click_result['success']:
                        print("   ✅ Native mouse click succeeded")
                        click_success = True
                except Exception as e:
                    native_click_result = {
                        'success': False,
                        'error': str(e),
                        'method': 'playwright_native'
                    }
                    print(f"   ❌ Native mouse click failed: {e}")
        
        # Clean up stored element references
        await self.evaluate("delete window.__deepClickElements;")
        
        return {
            'success': click_success,
            'coordinates': {'x': x, 'y': y},
            'deep_elements': deep_elements,
            'target_element': target_element,
            'target_index': target_index,
            'javascript_click': {
                'success': click_result.get('success', False) if target_element else False,
                'error': click_error
            },
            'native_click': native_click_result,
            'label': label
        }
    
    async def click_at_deep(self, x: float, y: float, label: str = "deep_click") -> Dict[str, Any]:
        """
        Convenience method that combines deep detection with crosshair visualization.
        This method should be used as a drop-in replacement for click_at in CrosshairBrowserClient.
        """
        # First do the deep click detection and execution
        deep_result = await self.click_at_with_deep_detection(x, y, label)
        
        # Then add crosshair visualization if this is mixed into CrosshairBrowserClient
        if hasattr(self, 'click_with_crosshair') and hasattr(self, 'crosshair_screenshots'):
            if self.crosshair_screenshots:
                # Take a screenshot with crosshair for visual debugging
                crosshair_result = await self.click_with_crosshair(
                    x=x, 
                    y=y, 
                    label=f"{label}_deep",
                    take_screenshot=True
                )
                deep_result['screenshot_path'] = crosshair_result.get('screenshot_path')
        
        return deep_result


# Example of how to integrate this into CrosshairBrowserClient:
"""
from clients.browser_client_crosshair import CrosshairBrowserClient
from CLAUDE_TMP.deep_click_implementation import DeepClickMixin

class DeepCrosshairBrowserClient(DeepClickMixin, CrosshairBrowserClient):
    '''Browser client with both crosshair visualization and deep element detection'''
    
    async def click_at(self, x: float, y: float, label: str = "click_at") -> Dict[str, Any]:
        '''Override click_at to use deep detection'''
        return await self.click_at_deep(x, y, label)

# Usage:
client = DeepCrosshairBrowserClient()
result = await client.click_at(100, 200, "my_button")

# The result will include:
# - Information about all elements found at that position
# - Which element was actually clicked
# - Whether the click succeeded
# - A crosshair screenshot showing the exact click position
"""