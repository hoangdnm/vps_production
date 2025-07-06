#!/bin/bash

# Stop API Server
echo "=== STOPPING API SERVER ==="

if [ -f "api_server.pid" ]; then
    PID=$(cat api_server.pid)
    if ps -p $PID > /dev/null; then
        echo "Stopping API server (PID: $PID)..."
        kill $PID
        sleep 3
        
        # Force kill if still running
        if ps -p $PID > /dev/null; then
            echo "Force killing..."
            kill -9 $PID
        fi
        
        rm -f api_server.pid
        echo "API server stopped!"
    else
        echo "API server not running (PID not found)"
        rm -f api_server.pid
    fi
else
    echo "No PID file found"
fi

# Kill any remaining Gunicorn processes
pkill -f "gunicorn.*api_server:app" 2>/dev/null || true

echo "Cleanup complete!"
