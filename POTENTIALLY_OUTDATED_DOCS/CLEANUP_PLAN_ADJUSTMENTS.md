# Cleanup Plan Adjustments

## 1. Screenshot Folder
Add to the plan:
```bash
# Move screenshots folder to browser_automation
mv /home/ubuntu/screenshots ./
```

## 2. Rename Final Files More Clearly
Instead of:
- `browser_server_final.py` → `browser_server_enhanced.py` (keep original name, it's descriptive)
- `browser_client_final.py` → `browser_client_enhanced.py` (keep original name)

## 3. Create Import Compatibility
After moving, create symlinks or update imports:
```bash
# Create compatibility imports in browser_automation/
echo "from .server.browser_server_enhanced import *" > ./__init__.py
```

## 4. Keep Active Test Files Accessible
Some test files are useful for development:
```bash
mkdir -p ./tests
mv ./server/test_browser_server.py ./tests/
```

## 5. Don't Move Everything at Once
Consider a phased approach:
- Phase 1: Create structure and move deprecated files
- Phase 2: Move and test server/client files
- Phase 3: Move remaining files after verifying nothing breaks

## 6. Add .gitignore
```bash
echo "*.log
*.pyc
__pycache__/
sessions/
.DS_Store" > ./.gitignore
```

## Overall Assessment: 
The plan is **95% correct** and ready to execute with these minor adjustments!