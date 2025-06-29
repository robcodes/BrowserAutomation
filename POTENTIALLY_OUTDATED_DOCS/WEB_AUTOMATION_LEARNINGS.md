# Web Automation Learnings - Quick Reference

## What Works ✅
1. **Persistent browser sessions** - External server maintains browser state between Claude executions
2. **Console log capture** - All JS errors, warnings, and logs are captured with timestamps
3. **Network monitoring** - Track API calls and responses (e.g., 401 auth errors)
4. **Same-origin iframe access** - Can fill forms in iframes IF they're same domain/protocol
5. **Shadow DOM detection** - Can detect web components but access is limited
6. **Screenshot-based debugging** - Essential for understanding current page state

## What Doesn't Work ❌
1. **Cross-origin iframes** - Browser security blocks access (even if visually on same site)
2. **Direct shadow DOM manipulation** - Can't access elements inside shadow roots
3. **Finding elements outside viewport** - Elements at (0,0) or off-screen are hard to detect
4. **Generic selectors** - Must use specific selectors; generic searches miss custom elements

## Key Insights 🔍
- **Web components hide elements** - `<fuzzy-avatar>` inside `<fuzzycode-notifications>` wasn't found by standard queries
- **Iframes CAN be same-origin** - `https://fuzzycode.dev/` and `https://fuzzycode.dev/user_login` = same origin
- **Console logs reveal root causes** - 401 errors explained why code generation failed
- **Bounding box detection works** - Best method for finding clickable elements by position
- **Always verify element visibility** - `offsetParent !== null` is crucial check