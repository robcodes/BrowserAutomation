# MCP Browser Control Options Guide

## Overview
MCP (Model Context Protocol) allows Claude and other AI assistants to control browsers through specialized servers. This guide covers all available options for Ubuntu 20.04 LTS.

## 1. Microsoft's Official Playwright MCP Server (@playwright/mcp)
**Status**: Official, Most Popular, Actively Maintained
**GitHub**: Part of Microsoft's Playwright ecosystem

### Features:
- Supports Chromium, Firefox, and WebKit
- Headless and headed modes
- Cross-browser testing capabilities
- Excellent documentation and support

### Installation:
```bash
# Install Node.js if not present (you already have v20.11.0)
# Install the MCP server
npx @playwright/mcp@latest

# Or install globally
npm install -g @playwright/mcp
```

### Ubuntu 20.04 Requirements:
```bash
# Install browser dependencies
sudo npx playwright install-deps
# This installs all necessary libraries for Chromium, Firefox, and WebKit
```

### Configuration:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

## 2. Puppeteer-based MCP Servers

### a) @modelcontextprotocol/server-puppeteer
**Status**: Official Example, Well-maintained
**GitHub**: https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer

### Features:
- Chrome/Chromium automation
- Screenshot capabilities
- PDF generation
- Network interception

### Installation:
```bash
# Clone the repository
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/puppeteer
npm install
npm run build
```

### Configuration:
```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "node",
      "args": ["/path/to/servers/src/puppeteer/dist/index.js"]
    }
  }
}
```

### b) twolven/mcp-server-puppeteer-py (Python)
**Status**: Active, Python-based
**GitHub**: https://github.com/twolven/mcp-server-puppeteer-py

### Features:
- Python implementation
- Uses Playwright under the hood
- Good for Python developers

### Installation:
```bash
# First install pip if not present
sudo apt update
sudo apt install -y python3-pip

# Install the server
pip install mcp-server-puppeteer-py
```

## 3. Selenium-based MCP Servers

### a) @angiejones/mcp-selenium
**Status**: Most Popular Selenium Implementation
**GitHub**: https://github.com/angiejones/mcp-selenium

### Features:
- Wide browser support
- Established ecosystem
- Good for existing Selenium users

### Installation:
```bash
# Install via npm
npm install -g @angiejones/mcp-selenium

# Install ChromeDriver
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install -y google-chrome-stable

# Download ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1)
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION} -O /tmp/chromedriver_version
CHROMEDRIVER_VERSION=$(cat /tmp/chromedriver_version)
wget https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

### Configuration:
```json
{
  "mcpServers": {
    "selenium": {
      "command": "npx",
      "args": ["-y", "@angiejones/mcp-selenium"]
    }
  }
}
```

## 4. Cloud-based Solutions

### Browserbase MCP Server
**Status**: Commercial, Cloud-based
**Website**: https://browserbase.com

### Features:
- No local setup required
- Scalable cloud infrastructure
- API-based access

### Installation:
```bash
npm install @browserbase/mcp-server
```

### Configuration:
```json
{
  "mcpServers": {
    "browserbase": {
      "command": "npx",
      "args": ["@browserbase/mcp-server"],
      "env": {
        "BROWSERBASE_API_KEY": "your-api-key"
      }
    }
  }
}
```

## 5. Ubuntu 20.04 Specific Setup

### Essential Dependencies:
```bash
# Update system
sudo apt update

# Install essential tools
sudo apt install -y \
  git \
  curl \
  wget \
  build-essential \
  ca-certificates \
  fonts-liberation \
  libappindicator3-1 \
  libasound2 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libc6 \
  libcairo2 \
  libcups2 \
  libdbus-1-3 \
  libexpat1 \
  libfontconfig1 \
  libgbm1 \
  libgcc1 \
  libglib2.0-0 \
  libgtk-3-0 \
  libnspr4 \
  libnss3 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libstdc++6 \
  libx11-6 \
  libx11-xcb1 \
  libxcb1 \
  libxcomposite1 \
  libxcursor1 \
  libxdamage1 \
  libxext6 \
  libxfixes3 \
  libxi6 \
  libxrandr2 \
  libxrender1 \
  libxss1 \
  libxtst6 \
  lsb-release \
  xdg-utils

# For headless operation
sudo apt install -y xvfb
```

### Virtual Display Setup (for headless):
```bash
# Install Xvfb
sudo apt install -y xvfb

# Start virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
```

## 6. Recommendations

### Best Choice for Your Setup: Microsoft's Official Playwright MCP

**Why Playwright MCP is recommended:**
1. **Official Support**: Backed by Microsoft
2. **Multi-browser**: Supports Chrome, Firefox, and Safari
3. **Active Development**: Regular updates and bug fixes
4. **Great Documentation**: Comprehensive guides
5. **Works well on Ubuntu 20.04**: Tested compatibility

### Quick Start Commands:
```bash
# 1. Install dependencies
sudo apt update
sudo apt install -y git python3-pip

# 2. Install Playwright MCP
npm install -g @playwright/mcp

# 3. Install browser dependencies
sudo npx playwright install-deps

# 4. Test installation
npx playwright --version
```

### Alternative: Puppeteer MCP (if you prefer Chrome-only)
```bash
# Clone and install
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/puppeteer
npm install
npm run build
```

## 7. Integration with Claude Desktop

### Configuration file location:
- Linux: `~/.config/Claude/claude_desktop_config.json`

### Example configuration:
```json
{
  "mcpServers": {
    "browser": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "DISPLAY": ":99"
      }
    }
  }
}
```

## 8. Testing Your Setup

### Basic test script:
```javascript
// test-browser.js
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://example.com');
  console.log(await page.title());
  await browser.close();
})();
```

### Run test:
```bash
node test-browser.js
```

## 9. Troubleshooting

### Common Issues:

1. **Missing dependencies error**:
   ```bash
   sudo npx playwright install-deps
   ```

2. **Display not found (headed mode)**:
   ```bash
   export DISPLAY=:99
   Xvfb :99 -screen 0 1920x1080x24 &
   ```

3. **Permission denied**:
   ```bash
   sudo chmod +x /usr/local/bin/chromedriver
   ```

4. **npm permission issues**:
   ```bash
   mkdir ~/.npm-global
   npm config set prefix '~/.npm-global'
   echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
   source ~/.bashrc
   ```

## 10. Next Steps

1. Choose your preferred MCP server (recommend Playwright)
2. Install dependencies
3. Configure Claude Desktop
4. Test the connection
5. Start automating browser tasks

For your specific Ubuntu 20.04 Docker environment accessed via noVNC, the Playwright MCP with Xvfb for virtual display would work best.