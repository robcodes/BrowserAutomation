# Compatibility imports
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Make server and client easily importable
from .server.browser_server_enhanced import BrowserManager
from .clients.browser_client_enhanced import EnhancedBrowserClient