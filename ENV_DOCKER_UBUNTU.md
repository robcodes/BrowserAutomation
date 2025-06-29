# Docker Ubuntu Environment Configuration

This document contains Docker Ubuntu-specific instructions and configurations for the browser automation project.

## Environment Detection
You are running in Docker Ubuntu if:
- `HOME=/home/ubuntu`
- Platform is Linux with Ubuntu distribution
- Running inside a Docker container with noVNC access

## System Architecture
- **Host OS**: Ubuntu Desktop
- **Container Platform**: Docker
- **Container Management**: Portainer
- **Container OS**: Ubuntu Desktop (running inside Docker)
- **Access Method**: noVNC2 (browser-based VNC client)

## Environment Details
- **Working Directory**: `/home/ubuntu`
- **Platform**: Linux
- **Kernel Version**: 6.11.0-26-generic
- **Distribution**: Ubuntu 20.04.2 LTS (Focal Fossa)
- **Architecture**: x86_64

## Access Flow
1. Ubuntu Desktop (Host) → Portainer → Docker Container (Ubuntu Desktop)
2. Container exposes VNC server
3. User accesses via noVNC2 in web browser
4. Full desktop environment available through browser

## Installed Development Environment

### Programming Languages & Runtimes
**Installed:**
- Python 3.8.5 (with Python 3 symlink)
- Node.js v20.11.0
- npm 10.2.4
- GCC 9.4.0 (C compiler)
- G++ 9.4.0 (C++ compiler)
- Perl 5.30.0

**NOT Installed by default:**
- Java/JDK
- Go
- Rust
- Ruby
- PHP

### Build Tools & Package Managers
**Installed:**
- GNU Make 4.2.1
- build-essential package (includes gcc, g++, make, etc.)

**NOT Installed by default:**
- CMake
- pip/pip3 (Python package manager)
- yarn
- cargo (Rust)
- Maven
- Gradle

### Critical Missing Tools (Install These First)
1. **Git** - Essential for version control
2. **Text editor** (vim/nano/emacs) - No console editors available by default
3. **pip/pip3** - Can't install Python packages without it
4. **SSH** - Can't connect to remote repositories

### Initial Setup Commands
```bash
# Update package list
sudo apt update

# Install essential tools
sudo apt install -y git vim nano python3-pip openssh-client

# Install Python dependencies
pip3 install -r config/requirements.txt
pip3 install pillow

# Install Playwright browsers
npx playwright install chromium
# or
playwright install chromium
```

### Browser Setup (Playwright)
For Docker Ubuntu, Playwright can use standard installation:
```bash
# Install system dependencies
sudo npx playwright install-deps

# Install browsers
npx playwright install chromium
```

### Server Configuration
The browser server runs on `http://0.0.0.0:8000`. Access depends on Docker networking:
- If port is mapped: `http://localhost:8000` from host
- Within container: `http://localhost:8000`
- Check Docker/Portainer for port mappings

### File Paths
- Working directory: `/home/ubuntu`
- Python packages: Usually in `/usr/local/lib/python3.8/dist-packages/`
- Playwright browsers: `~/.cache/ms-playwright/`

### Docker-Specific Considerations
- File system is isolated within the Docker container
- Network access subject to Docker networking configuration
- Performance may be affected by VNC overhead
- GUI applications accessible through noVNC in browser

### Running the Server
```bash
cd .
python3 server/browser_server_enhanced.py
```

### Troubleshooting
1. **Permission issues**: Use `sudo` for system package installation
2. **Network access**: Check Docker port mappings in Portainer
3. **Display issues**: Ensure VNC/noVNC is properly configured
4. **Missing dependencies**: Use `apt install` to add system packages

### Best Practices
1. Keep track of installed packages for container reproducibility
2. Use virtual environments for Python projects
3. Document port mappings and network configuration
4. Regular backups of important data (containers are ephemeral)

### Recommendations for Complete Development Setup
```bash
# Version control & editors
sudo apt install -y git vim nano emacs

# Python development
sudo apt install -y python3-pip python3-venv python3-dev

# Additional tools
sudo apt install -y openssh-client ripgrep cmake

# For GUI development (if needed)
sudo apt install -y code  # VS Code
```