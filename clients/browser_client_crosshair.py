#!/usr/bin/env python3
"""
Enhanced Browser Client with built-in crosshair visualization for all clicks
"""
import asyncio
import time
from typing import Optional, Dict, Any, Union, Tuple
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from clients.browser_client_enhanced import EnhancedBrowserClient

class CrosshairBrowserClient(EnhancedBrowserClient):
    """Browser client that shows crosshairs for all click operations"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        self.crosshair_screenshots = True  # Enable by default
        self.crosshair_color = "red"
        self.crosshair_size = 40
        self.screenshot_dir = Path(__file__).parent.parent / "screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)
    
    async def click_with_crosshair(self, 
                                  selector: Optional[str] = None,
                                  x: Optional[float] = None, 
                                  y: Optional[float] = None,
                                  label: str = "click",
                                  take_screenshot: bool = True) -> Dict[str, Any]:
        """
        Click with crosshair visualization
        
        Args:
            selector: CSS selector to click (will find center)
            x, y: Direct coordinates to click
            label: Label for the screenshot
            take_screenshot: Whether to take a screenshot with crosshair
            
        Returns:
            Dict with click result and screenshot path
        """
        # Determine click coordinates
        if selector:
            # Get element center
            element_info = await self.evaluate(f"""
                (() => {{
                    const element = document.querySelector('{selector}');
                    if (!element) return null;
                    const rect = element.getBoundingClientRect();
                    return {{
                        x: rect.left + rect.width / 2,
                        y: rect.top + rect.height / 2,
                        width: rect.width,
                        height: rect.height,
                        tagName: element.tagName,
                        className: element.className,
                        text: element.textContent?.substring(0, 50)
                    }};
                }})()
            """)
            
            if not element_info:
                return {"success": False, "error": f"Element not found: {selector}"}
            
            x = element_info['x']
            y = element_info['y']
            label = f"{label}_{selector.replace('.', '_').replace('#', '_')}"
        
        elif x is None or y is None:
            return {"success": False, "error": "Must provide either selector or x,y coordinates"}
        
        # Round coordinates
        x = round(x)
        y = round(y)
        
        screenshot_path = None
        
        if take_screenshot and self.crosshair_screenshots:
            # Draw crosshair
            await self.evaluate(f"""
                (() => {{
                    // Remove any existing crosshair
                    const existing = document.getElementById('debug-crosshair');
                    if (existing) existing.remove();
                    
                    // Create crosshair container
                    const crosshair = document.createElement('div');
                    crosshair.id = 'debug-crosshair';
                    crosshair.style.position = 'fixed';
                    crosshair.style.left = '{x}px';
                    crosshair.style.top = '{y}px';
                    crosshair.style.width = '0';
                    crosshair.style.height = '0';
                    crosshair.style.zIndex = '999999';
                    crosshair.style.pointerEvents = 'none';
                    
                    // Horizontal line
                    const hLine = document.createElement('div');
                    hLine.style.position = 'absolute';
                    hLine.style.width = '{self.crosshair_size}px';
                    hLine.style.height = '2px';
                    hLine.style.backgroundColor = '{self.crosshair_color}';
                    hLine.style.left = '-{self.crosshair_size//2}px';
                    hLine.style.top = '-1px';
                    hLine.style.boxShadow = '0 0 3px rgba(0,0,0,0.8)';
                    
                    // Vertical line
                    const vLine = document.createElement('div');
                    vLine.style.position = 'absolute';
                    vLine.style.width = '2px';
                    vLine.style.height = '{self.crosshair_size}px';
                    vLine.style.backgroundColor = '{self.crosshair_color}';
                    vLine.style.left = '-1px';
                    vLine.style.top = '-{self.crosshair_size//2}px';
                    vLine.style.boxShadow = '0 0 3px rgba(0,0,0,0.8)';
                    
                    // Center dot
                    const dot = document.createElement('div');
                    dot.style.position = 'absolute';
                    dot.style.width = '8px';
                    dot.style.height = '8px';
                    dot.style.backgroundColor = 'yellow';
                    dot.style.border = '2px solid {self.crosshair_color}';
                    dot.style.borderRadius = '50%';
                    dot.style.left = '-5px';
                    dot.style.top = '-5px';
                    dot.style.boxShadow = '0 0 3px rgba(0,0,0,0.8)';
                    
                    // Label
                    const labelDiv = document.createElement('div');
                    labelDiv.style.position = 'absolute';
                    labelDiv.style.left = '15px';
                    labelDiv.style.top = '15px';
                    labelDiv.style.backgroundColor = 'yellow';
                    labelDiv.style.color = 'black';
                    labelDiv.style.padding = '3px 8px';
                    labelDiv.style.fontSize = '14px';
                    labelDiv.style.fontWeight = 'bold';
                    labelDiv.style.fontFamily = 'monospace';
                    labelDiv.style.border = '2px solid {self.crosshair_color}';
                    labelDiv.style.borderRadius = '3px';
                    labelDiv.style.boxShadow = '0 0 5px rgba(0,0,0,0.8)';
                    labelDiv.textContent = '{label} ({x}, {y})';
                    
                    crosshair.appendChild(hLine);
                    crosshair.appendChild(vLine);
                    crosshair.appendChild(dot);
                    crosshair.appendChild(labelDiv);
                    document.body.appendChild(crosshair);
                }})()
            """)
            
            # Wait for render
            await asyncio.sleep(0.1)
            
            # Take screenshot
            timestamp = int(time.time() * 1000)
            screenshot_name = f"crosshair_{label}_{x}_{y}_{timestamp}.png"
            screenshot_path = self.screenshot_dir / screenshot_name
            await self.screenshot(screenshot_name)
        
        # Perform the click
        click_result = await self.evaluate(f"""
            (() => {{
                const element = document.elementFromPoint({x}, {y});
                
                if (!element) {{
                    return {{
                        success: false,
                        error: 'No element at coordinates'
                    }};
                }}
                
                // Log what we're clicking
                console.log('Crosshair clicking:', element.tagName, element.className, 'at', {x}, {y});
                
                // Try multiple click methods
                try {{
                    // Method 1: Direct click
                    element.click();
                    
                    // Method 2: Dispatch mouse event
                    element.dispatchEvent(new MouseEvent('click', {{
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: {x},
                        clientY: {y}
                    }}));
                    
                    // Method 3: Pointer events
                    element.dispatchEvent(new PointerEvent('pointerdown', {{
                        clientX: {x},
                        clientY: {y},
                        bubbles: true
                    }}));
                    element.dispatchEvent(new PointerEvent('pointerup', {{
                        clientX: {x},
                        clientY: {y},
                        bubbles: true
                    }}));
                    
                    return {{
                        success: true,
                        element: {{
                            tagName: element.tagName,
                            className: element.className,
                            id: element.id,
                            text: element.textContent?.substring(0, 50)
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
        
        # Remove crosshair
        if self.crosshair_screenshots:
            await self.evaluate("""
                (() => {
                    const crosshair = document.getElementById('debug-crosshair');
                    if (crosshair) crosshair.remove();
                })()
            """)
        
        return {
            "success": click_result.get("success", False),
            "coordinates": {"x": x, "y": y},
            "screenshot_path": str(screenshot_path) if screenshot_path else None,
            "element": click_result.get("element"),
            "error": click_result.get("error")
        }
    
    async def click(self, selector: str) -> None:
        """Override base click to use crosshair version"""
        result = await self.click_with_crosshair(selector=selector, label="click")
        if not result["success"]:
            raise Exception(f"Click failed: {result.get('error', 'Unknown error')}")
    
    async def click_at(self, x: float, y: float, label: str = "click_at") -> Dict[str, Any]:
        """Click at specific coordinates with crosshair"""
        return await self.click_with_crosshair(x=x, y=y, label=label)
    
    def disable_crosshairs(self):
        """Disable crosshair screenshots"""
        self.crosshair_screenshots = False
    
    def enable_crosshairs(self):
        """Enable crosshair screenshots"""
        self.crosshair_screenshots = True