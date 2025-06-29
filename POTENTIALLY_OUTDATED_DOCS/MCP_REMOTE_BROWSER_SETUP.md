# Remote MCP Browser Control Setup Guide

## Overview
This guide shows how to set up your Ubuntu 20.04 box as a remote browser that can be controlled by Claude running elsewhere.

## Architecture
```
[Claude on Machine A] ---> [MCP SSE Server on Ubuntu Box] ---> [Browser Control]
                     HTTPS/SSE
```

## Method 1: Using mcp-proxy (Recommended)

### Step 1: Install Playwright MCP
```bash
# Install dependencies
sudo apt update
sudo apt install -y git python3-pip

# Install Playwright MCP
npm install -g @playwright/mcp

# Install browser dependencies
sudo npx playwright install-deps

# For headless operation in Docker
sudo apt install -y xvfb
```

### Step 2: Install mcp-proxy
```bash
# Install mcp-proxy globally
npm install -g @modelcontextprotocol/mcp-proxy

# Or use npx (no installation needed)
npx @modelcontextprotocol/mcp-proxy --help
```

### Step 3: Start Browser Control Server with Remote Access
```bash
# Set up virtual display (for Docker environment)
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &

# Start Playwright MCP with mcp-proxy exposing it remotely
npx @modelcontextprotocol/mcp-proxy \
  --host=0.0.0.0 \
  --port=8080 \
  --api-key="your-secure-api-key-here" \
  npx @playwright/mcp

# Or without API key (less secure)
npx @modelcontextprotocol/mcp-proxy \
  --host=0.0.0.0 \
  --port=8080 \
  npx @playwright/mcp
```

### Step 4: Configure Remote Claude
On the machine running Claude, add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "remote-browser": {
      "transport": "sse",
      "url": "http://YOUR_UBUNTU_BOX_IP:8080/sse",
      "headers": {
        "X-API-Key": "your-secure-api-key-here"
      }
    }
  }
}
```

## Method 2: Custom SSE Server Implementation

### Create a custom server that wraps Playwright:
```javascript
// remote-browser-server.js
import express from 'express';
import cors from 'cors';
import { chromium } from 'playwright';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';

const app = express();
app.use(cors());
app.use(express.json());

// Store active browser sessions
const sessions = new Map();

// SSE endpoint
app.get('/sse', async (req, res) => {
  // Set SSE headers
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  
  // Create MCP server
  const server = new Server({
    name: 'remote-browser',
    version: '1.0.0',
  });

  // Add browser control tools
  server.setRequestHandler('tools/list', async () => {
    return {
      tools: [
        {
          name: 'navigate',
          description: 'Navigate to a URL',
          inputSchema: {
            type: 'object',
            properties: {
              url: { type: 'string' }
            },
            required: ['url']
          }
        },
        {
          name: 'screenshot',
          description: 'Take a screenshot',
          inputSchema: {
            type: 'object',
            properties: {
              fullPage: { type: 'boolean' }
            }
          }
        },
        {
          name: 'click',
          description: 'Click an element',
          inputSchema: {
            type: 'object',
            properties: {
              selector: { type: 'string' }
            },
            required: ['selector']
          }
        }
      ]
    };
  });

  // Handle tool calls
  server.setRequestHandler('tools/call', async (request) => {
    const { name, arguments: args } = request.params;
    const sessionId = req.headers['x-session-id'] || 'default';
    
    // Get or create browser session
    if (!sessions.has(sessionId)) {
      const browser = await chromium.launch({ headless: true });
      const page = await browser.newPage();
      sessions.set(sessionId, { browser, page });
    }
    
    const { page } = sessions.get(sessionId);
    
    switch (name) {
      case 'navigate':
        await page.goto(args.url);
        return { content: [{ type: 'text', text: `Navigated to ${args.url}` }] };
        
      case 'screenshot':
        const screenshot = await page.screenshot({ 
          fullPage: args.fullPage || false,
          encoding: 'base64'
        });
        return { 
          content: [{ 
            type: 'image', 
            data: screenshot,
            mimeType: 'image/png'
          }] 
        };
        
      case 'click':
        await page.click(args.selector);
        return { content: [{ type: 'text', text: `Clicked ${args.selector}` }] };
        
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  });

  // Create SSE transport
  const transport = new SSEServerTransport('/messages', res);
  await server.connect(transport);
  
  // Cleanup on disconnect
  req.on('close', () => {
    const sessionId = req.headers['x-session-id'] || 'default';
    const session = sessions.get(sessionId);
    if (session) {
      session.browser.close();
      sessions.delete(sessionId);
    }
  });
});

// Messages endpoint
app.post('/messages', (req, res) => {
  // Forward messages to appropriate SSE connection
  // Implementation depends on your session management
  res.json({ status: 'ok' });
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Remote browser MCP server listening on port ${PORT}`);
});
```

### Install dependencies and run:
```bash
# Create package.json
cat > package.json << EOF
{
  "name": "remote-browser-mcp",
  "type": "module",
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "playwright": "^1.40.0",
    "@modelcontextprotocol/sdk": "^1.0.0"
  }
}
EOF

# Install dependencies
npm install

# Run the server
node remote-browser-server.js
```

## Method 3: Using Puppeteer with SSE

### Install and configure:
```bash
# Clone the MCP servers repository
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/puppeteer

# Modify the server to use SSE transport
npm install
npm run build

# Start with remote access
npx @modelcontextprotocol/mcp-proxy \
  --host=0.0.0.0 \
  --port=8080 \
  node dist/index.js
```

## Security Considerations

### 1. Use HTTPS with Let's Encrypt
```bash
# Install certbot
sudo apt install -y certbot

# Get certificate (replace example.com with your domain)
sudo certbot certonly --standalone -d example.com

# Use NGINX as reverse proxy
sudo apt install -y nginx

# Configure NGINX
sudo nano /etc/nginx/sites-available/mcp-browser
```

### NGINX Configuration:
```nginx
server {
    listen 443 ssl;
    server_name example.com;
    
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    location /sse {
        proxy_pass http://localhost:8080/sse;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }
    
    location /messages {
        proxy_pass http://localhost:8080/messages;
        proxy_http_version 1.1;
    }
}
```

### 2. API Key Authentication
Always use API keys when exposing servers:
```bash
# Generate secure API key
openssl rand -hex 32
```

### 3. Firewall Configuration
```bash
# Allow only specific ports
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

## Docker Deployment (Recommended for Production)

### Create Dockerfile:
```dockerfile
FROM node:20-slim

# Install Chrome dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright
RUN npm install -g @playwright/mcp @modelcontextprotocol/mcp-proxy

# Install browser binaries
RUN npx playwright install-deps

# Expose port
EXPOSE 8080

# Start with virtual display
CMD xvfb-run -a npx @modelcontextprotocol/mcp-proxy \
    --host=0.0.0.0 \
    --port=8080 \
    --api-key="${API_KEY}" \
    npx @playwright/mcp
```

### Run with Docker:
```bash
# Build image
docker build -t mcp-browser-server .

# Run container
docker run -d \
  --name mcp-browser \
  -p 8080:8080 \
  -e API_KEY=your-secure-api-key \
  --restart unless-stopped \
  mcp-browser-server
```

## Testing the Setup

### 1. Test locally first:
```bash
# Test SSE endpoint
curl -N http://localhost:8080/sse

# Test with authentication
curl -N -H "X-API-Key: your-api-key" http://localhost:8080/sse
```

### 2. Test from remote machine:
```bash
# Replace YOUR_SERVER_IP with actual IP
curl -N -H "X-API-Key: your-api-key" http://YOUR_SERVER_IP:8080/sse
```

## Systemd Service (For Auto-start)

Create service file:
```bash
sudo nano /etc/systemd/system/mcp-browser.service
```

```ini
[Unit]
Description=MCP Browser Control Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=~
Environment="DISPLAY=:99"
Environment="API_KEY=your-secure-api-key"
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 &
ExecStart=/usr/bin/npx @modelcontextprotocol/mcp-proxy --host=0.0.0.0 --port=8080 --api-key=${API_KEY} npx @playwright/mcp
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mcp-browser
sudo systemctl start mcp-browser
sudo systemctl status mcp-browser
```

## Monitoring and Logging

### View logs:
```bash
# Systemd logs
sudo journalctl -u mcp-browser -f

# Docker logs
docker logs -f mcp-browser
```

### Add logging to custom implementation:
```javascript
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'mcp-browser.log' }),
    new winston.transports.Console()
  ]
});

// Log all connections
app.get('/sse', (req, res) => {
  logger.info('New SSE connection', { 
    ip: req.ip,
    headers: req.headers 
  });
  // ... rest of code
});
```

## Quick Start Commands

For immediate setup:
```bash
# 1. Install everything needed
sudo apt update
sudo apt install -y git xvfb
npm install -g @playwright/mcp @modelcontextprotocol/mcp-proxy
sudo npx playwright install-deps

# 2. Start virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &

# 3. Generate API key
export API_KEY=$(openssl rand -hex 32)
echo "Your API key: $API_KEY"

# 4. Start the server
npx @modelcontextprotocol/mcp-proxy \
  --host=0.0.0.0 \
  --port=8080 \
  --api-key="$API_KEY" \
  npx @playwright/mcp

# 5. Server is now accessible at http://YOUR_IP:8080
```

This setup turns your Ubuntu box into a remote browser that any Claude instance can control via MCP SSE protocol!