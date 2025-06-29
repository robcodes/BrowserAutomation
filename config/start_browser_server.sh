#!/bin/bash
# Start the browser server in the background

echo "Starting Persistent Browser Server..."

# Ensure display is set
export DISPLAY=:99

# Install fastapi and uvicorn if needed
pip3 install fastapi uvicorn httpx pydantic > /dev/null 2>&1

# Start server in background
nohup python3 ~/browser_server_poc.py > ~/browser_server.log 2>&1 &

# Save PID
echo $! > ~/browser_server.pid

echo "Server starting..."
sleep 3

# Check if running
if ps -p $(cat ~/browser_server.pid) > /dev/null; then
    echo "✓ Server is running on http://localhost:8000"
    echo "✓ PID: $(cat ~/browser_server.pid)"
    echo "✓ Logs: ~/browser_server.log"
else
    echo "✗ Server failed to start"
    echo "Check logs: ~/browser_server.log"
    tail -20 ~/browser_server.log
fi