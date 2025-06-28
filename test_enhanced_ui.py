#!/usr/bin/env python3
"""
Test script to verify the enhanced UI is working
"""
import subprocess
import time
import webbrowser

print("Starting the browser server...")
# Start the server in the background
server_process = subprocess.Popen(
    ["python3", "server/browser_server_enhanced.py"],
    cwd="/home/ubuntu/browser_automation"
)

# Give it time to start
print("Waiting for server to start...")
time.sleep(3)

# Open the enhanced UI in browser
url = "http://localhost:8000/ui-enhanced"
print(f"Opening enhanced UI at: {url}")
webbrowser.open(url)

print("\nServer is running. Press Ctrl+C to stop.")
try:
    server_process.wait()
except KeyboardInterrupt:
    print("\nShutting down server...")
    server_process.terminate()
    server_process.wait()
    print("Server stopped.")