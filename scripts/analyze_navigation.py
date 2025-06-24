#!/usr/bin/env python3
"""
Analyze website navigation by combining screenshot analysis and code inspection
"""
from playwright_agent_advanced import create_browser_session
import base64
import json
import os

def analyze_website_navigation(url, save_screenshots=True):
    """
    Analyze a website's navigation structure using both visual and code analysis
    """
    os.environ['DISPLAY'] = ':99'
    
    # Create browser session
    agent = create_browser_session(headless=True)
    
    try:
        # Navigate to the site
        print(f'=== Analyzing {url} ===\n')
        agent.page.goto(url)
        agent.page.wait_for_load_state('networkidle')
        agent.page.wait_for_timeout(2000)
        
        # 1. Take screenshot for visual analysis
        if save_screenshots:
            agent.page.screenshot(path='/home/ubuntu/screenshots/analysis_initial.png', full_page=True)
            print('Screenshot saved: analysis_initial.png\n')
        
        # 2. Extract page structure
        print('1. PAGE STRUCTURE ANALYSIS:')
        
        # Get all interactive elements
        buttons = agent.page.locator('button, input[type="button"], input[type="submit"], a.btn, .button').all()
        links = agent.page.locator('a[href]').all()
        inputs = agent.page.locator('input[type="text"], input[type="email"], input[type="password"], textarea').all()
        forms = agent.page.locator('form').all()
        
        print(f'   - Buttons found: {len(buttons)}')
        print(f'   - Links found: {len(links)}')
        print(f'   - Input fields found: {len(inputs)}')
        print(f'   - Forms found: {len(forms)}')
        
        # 3. Analyze navigation structure
        print('\n2. NAVIGATION ELEMENTS:')
        
        # Check for common navigation patterns
        nav_selectors = [
            'nav', 'header nav', '.navbar', '.navigation', '#navigation',
            '.menu', '#menu', '.nav-menu', '[role="navigation"]'
        ]
        
        nav_found = False
        for selector in nav_selectors:
            nav_elements = agent.page.locator(selector).all()
            if nav_elements:
                nav_found = True
                print(f'   Found navigation with selector: {selector}')
                for nav in nav_elements[:1]:  # Just first one
                    nav_links = nav.locator('a').all()
                    print(f'   Navigation contains {len(nav_links)} links')
                    for link in nav_links[:5]:
                        text = link.inner_text().strip()
                        href = link.get_attribute('href')
                        if text:
                            print(f'     - "{text}" -> {href}')
        
        if not nav_found:
            print('   No standard navigation elements found')
        
        # 4. Extract main CTAs (Call to Actions)
        print('\n3. MAIN CALL-TO-ACTION ELEMENTS:')
        
        # Look for prominent buttons/links
        cta_selectors = [
            'a.btn-primary', 'button.primary', '.cta', '.call-to-action',
            'a[class*="primary"]', 'button[class*="primary"]',
            'a.play', 'button.play', '[class*="play"]',
            'a.btn-lg', 'button.btn-lg', '.hero a', '.hero button'
        ]
        
        cta_found = False
        for selector in cta_selectors:
            try:
                ctas = agent.page.locator(selector).all()
                if ctas:
                    cta_found = True
                    print(f'   Found CTAs with selector: {selector}')
                    for cta in ctas[:3]:  # First 3
                        text = cta.inner_text().strip()
                        if text:
                            print(f'     - "{text}"')
            except:
                pass
        
        if not cta_found:
            print('   No prominent CTA elements found')
        
        # 5. Extract visible text from buttons and links
        print('\n4. INTERACTIVE ELEMENTS TEXT:')
        
        print('   Buttons:')
        button_texts = []
        for button in buttons[:10]:  # First 10 buttons
            try:
                text = button.inner_text().strip()
                if text and text not in button_texts:
                    button_texts.append(text)
                    print(f'     - "{text}"')
            except:
                pass
        
        print('\n   Links:')
        for link in links[:10]:  # First 10 links
            try:
                text = link.inner_text().strip()
                href = link.get_attribute('href')
                if text and href:
                    print(f'     - "{text}" -> {href}')
            except:
                pass
        
        # 6. Check page source for routing information
        print('\n5. PAGE SOURCE ANALYSIS:')
        
        # Get page content
        content = agent.page.content()
        
        # Check for common frameworks
        frameworks = []
        if 'react' in content.lower() or 'React' in content:
            frameworks.append('React')
        if 'vue' in content.lower() or 'Vue' in content:
            frameworks.append('Vue')
        if 'angular' in content.lower() or 'Angular' in content:
            frameworks.append('Angular')
        if 'svelte' in content.lower():
            frameworks.append('Svelte')
        
        if frameworks:
            print(f'   - Detected frameworks: {", ".join(frameworks)}')
        
        # Check for routing patterns
        if 'router' in content.lower() or 'route' in content.lower():
            print('   - Found routing configuration')
        
        # 7. Extract meta information
        print('\n6. META INFORMATION:')
        title = agent.page.title()
        url = agent.page.url
        
        try:
            description = agent.page.locator('meta[name="description"]').get_attribute('content')
        except:
            description = None
        
        print(f'   - Title: {title}')
        print(f'   - Current URL: {url}')
        if description:
            print(f'   - Description: {description}')
        
        # 8. Try to identify navigation patterns
        print('\n7. NAVIGATION PATTERN ANALYSIS:')
        
        # Check if there's a "Play" or "Start" button (common in game/learning sites)
        play_buttons = agent.page.locator('button:has-text("Play"), a:has-text("Play"), button:has-text("Start"), a:has-text("Start")').all()
        if play_buttons:
            print(f'   - Found {len(play_buttons)} Play/Start buttons')
            
        # Check for login/signup
        auth_elements = agent.page.locator('button:has-text("Login"), a:has-text("Login"), button:has-text("Sign"), a:has-text("Sign")').all()
        if auth_elements:
            print(f'   - Found {len(auth_elements)} authentication elements')
        
        # 9. Test navigation by clicking
        print('\n8. TESTING NAVIGATION:')
        
        if len(links) > 0:
            initial_url = agent.page.url
            try:
                # Find the most promising link to click
                target_link = None
                for link in links:
                    text = link.inner_text().strip().lower()
                    if any(keyword in text for keyword in ['play', 'start', 'begin', 'enter', 'go']):
                        target_link = link
                        break
                
                if not target_link and len(links) > 0:
                    target_link = links[0]
                
                if target_link:
                    link_text = target_link.inner_text().strip()
                    print(f'   - Clicking link: "{link_text}"')
                    target_link.click()
                    agent.page.wait_for_timeout(3000)
                    new_url = agent.page.url
                    
                    if new_url != initial_url:
                        print(f'   - Navigation successful: {initial_url} -> {new_url}')
                        
                        if save_screenshots:
                            agent.page.screenshot(path='/home/ubuntu/screenshots/analysis_after_navigation.png')
                            print('   - Screenshot saved: analysis_after_navigation.png')
                            
                        # Analyze the new page
                        new_title = agent.page.title()
                        print(f'   - New page title: {new_title}')
                    else:
                        print('   - No URL change (might be SPA or modal)')
                        
            except Exception as e:
                print(f'   - Navigation test failed: {e}')
        
        # 10. Generate navigation map
        print('\n9. SUGGESTED NAVIGATION APPROACH:')
        
        if 'fuzzycode' in url.lower():
            print('   For FuzzyCode:')
            print('   1. Main page has a "Play Now" link')
            print('   2. Click "Play Now" to navigate to the game/learning interface')
            print('   3. The site appears to be a learning platform with interactive elements')
        else:
            print('   General approach:')
            print('   1. Look for main navigation menu or prominent CTAs')
            print('   2. Check for authentication if needed')
            print('   3. Follow the natural user flow')
        
        return {
            'buttons': len(buttons),
            'links': len(links),
            'forms': len(forms),
            'frameworks': frameworks,
            'title': title,
            'url': url
        }
        
    except Exception as e:
        print(f'Error during analysis: {e}')
        return None
    finally:
        agent.stop()

if __name__ == "__main__":
    import sys
    
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://fuzzycode.dev'
    analyze_website_navigation(url)