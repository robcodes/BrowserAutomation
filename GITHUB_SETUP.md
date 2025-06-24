# GitHub Setup Instructions

## Prerequisites
1. GitHub account
2. Personal Access Token (PAT) with `repo` scope
3. New empty repository created on GitHub

## Steps to Push

1. **Add your remote repository** (replace with your actual URL):
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

2. **Verify the remote was added:**
```bash
git remote -v
```

3. **Push to GitHub:**
When prompted for password, use your Personal Access Token (not your GitHub password):
```bash
git push -u origin master
```

## If you get authentication errors:

### Option 1: Use token in URL (temporary)
```bash
git remote set-url origin https://YOUR_GITHUB_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin master
```

### Option 2: Cache credentials (recommended)
```bash
# Cache credentials for 1 hour
git config --global credential.helper 'cache --timeout=3600'

# Then push (enter username and PAT when prompted)
git push -u origin master
```

### Option 3: Store credentials (less secure)
```bash
git config --global credential.helper store
# Then push (credentials will be saved after first use)
git push -u origin master
```

## After successful push:

Your repository will be available at:
`https://github.com/YOUR_USERNAME/YOUR_REPO_NAME`

## To clone on another machine:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
python server/browser_server_enhanced.py  # Start the server
```

## Important files to check on GitHub:
- `/scripts/fuzzycode_steps/` - Reference implementation
- `/docs/VISUAL_VERIFICATION_GUIDE.md` - Critical documentation
- `/clients/browser_client_crosshair.py` - The enhanced client
- `README.md` - Project overview

## Security Note:
- Never commit your Personal Access Token
- The `.gitignore` file excludes sensitive files like credentials
- Screenshots are excluded to keep repo size manageable