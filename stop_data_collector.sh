#!/bin/bash

# Stop Data Collector
echo "=== STOPPING DATA COLLECTOR ==="

if [ -f "data_collector.pid" ]; then
    PID=$(cat data_collector.pid)
    if ps -p $PID > /dev/null; then
        echo "Stopping data collector (PID: $PID)..."
        kill $PID
        sleep 3
        
        # Force kill if still running
        if ps -p $PID > /dev/null; then
            echo "Force killing..."
            kill -9 $PID
        fi
        
        rm -f data_collector.pid
        echo "Data collector stopped!"
    else
        echo "Data collector not running (PID not found)"
        rm -f data_collector.pid
    fi
else
    echo "No PID file found"
fi

# Kill any remaining processes
pkill -f "data_collector.py" 2>/dev/null || true

echo "Cleanup complete!"
