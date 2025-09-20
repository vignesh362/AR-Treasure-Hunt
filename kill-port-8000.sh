#!/bin/bash
# Kill any processes using port 8000

echo "🔍 Looking for processes using port 8000..."

# Find processes using port 8000
PIDS=$(lsof -ti :8000 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo "✅ No processes found using port 8000"
    exit 0
fi

echo "🔍 Found processes: $PIDS"

# Kill each process
for PID in $PIDS; do
    echo "🔄 Killing process $PID..."
    kill -TERM $PID 2>/dev/null
    sleep 1
    
    # Check if still running and force kill if needed
    if kill -0 $PID 2>/dev/null; then
        echo "⚡ Force killing process $PID..."
        kill -KILL $PID 2>/dev/null
    else
        echo "✅ Process $PID terminated successfully"
    fi
done

echo "✅ Port 8000 cleanup complete"
