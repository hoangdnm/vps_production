#!/bin/bash

# Start Data Collector for VPS Production
echo "=== STARTING DATA COLLECTOR - VPS PRODUCTION ==="

# Check if virtual environment exists
if [ -d "vps_env" ]; then
    source vps_env/bin/activate
    echo "Virtual environment activated"
else
    echo "Virtual environment not found. Run setup_vps.sh first"
    exit 1
fi

# Check if already running
if [ -f "data_collector.pid" ]; then
    PID=$(cat data_collector.pid)
    if ps -p $PID > /dev/null; then
        echo "Data collector already running (PID: $PID)"
        exit 1
    else
        rm -f data_collector.pid
    fi
fi

# Create logs directory
mkdir -p logs

# Start data collector in background
echo "Starting data collector..."
nohup python3 data_collector.py > logs/data_collector_stdout.log 2>&1 &
COLLECTOR_PID=$!

# Save PID
echo $COLLECTOR_PID > data_collector.pid

echo "Data collector started successfully!"
echo "PID: $COLLECTOR_PID"
echo "Logs: logs/data_collector_stdout.log"
echo "Application logs: data_collector.log"

# Show status
sleep 2
if ps -p $COLLECTOR_PID > /dev/null; then
    echo "Status: RUNNING"
    echo "To stop: ./stop_data_collector.sh"
    echo "To monitor: tail -f logs/data_collector_stdout.log"
else
    echo "Status: FAILED TO START"
    echo "Check logs for errors"
fi
