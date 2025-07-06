#!/bin/bash

# Start API Server for VPS Production
echo "=== STARTING API SERVER - VPS PRODUCTION ==="

# Check if virtual environment exists
if [ -d "vps_env" ]; then
    source vps_env/bin/activate
    echo "Virtual environment activated"
else
    echo "Virtual environment not found. Run setup_vps.sh first"
    exit 1
fi

# Check if already running
if [ -f "api_server.pid" ]; then
    PID=$(cat api_server.pid)
    if ps -p $PID > /dev/null; then
        echo "API server already running (PID: $PID)"
        echo "Server should be available at: http://$(curl -s ifconfig.me):5000"
        exit 1
    else
        rm -f api_server.pid
    fi
fi

# Create logs directory
mkdir -p logs

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

# Start API server with Gunicorn for production
echo "Starting API server with Gunicorn..."
nohup gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --log-level info --access-logfile logs/api_access.log --error-logfile logs/api_error.log api_server:app > logs/api_server_stdout.log 2>&1 &
API_PID=$!

# Save PID
echo $API_PID > api_server.pid

echo "API server started successfully!"
echo "PID: $API_PID"
echo "Public URL: http://$SERVER_IP:5000"
echo "API Endpoint: http://$SERVER_IP:5000/api/trading"
echo "Health Check: http://$SERVER_IP:5000/api/health"
echo ""
echo "Logs:"
echo "  - Access: logs/api_access.log"
echo "  - Error: logs/api_error.log"
echo "  - Application: api_server.log"

# Show status
sleep 3
if ps -p $API_PID > /dev/null; then
    echo "Status: RUNNING"
    echo "To stop: ./stop_api_server.sh"
    echo "To monitor: tail -f logs/api_access.log"
else
    echo "Status: FAILED TO START"
    echo "Check logs for errors"
fi
