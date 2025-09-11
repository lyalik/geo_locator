#!/bin/bash

# Simple startup script for Geo Locator
echo "🚀 Starting Geo Locator (Simple Mode)"
echo "====================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Cleanup existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "react-scripts start" 2>/dev/null
pkill -f "npm start" 2>/dev/null
pkill -f "run_local.py" 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
lsof -ti:5001 | xargs kill -9 2>/dev/null

# Create logs directory
mkdir -p logs

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    # Kill all related processes
    pkill -f "react-scripts start" 2>/dev/null
    pkill -f "npm start" 2>/dev/null
    pkill -f "run_local.py" 2>/dev/null
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    
    echo "✅ Services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM EXIT

# Start backend
echo "🔧 Starting backend..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start backend in background
export POSTGRES_PASSWORD=3666599
python run_local.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend started (PID: $BACKEND_PID)"
sleep 3

# Check backend health
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${YELLOW}⚠️ Backend health check failed, but continuing...${NC}"
fi

# Start frontend
echo "🎨 Starting frontend..."
cd ../frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Set environment variables
export BROWSER=none
export REACT_APP_API_URL=http://localhost:5001

# Start frontend in background
npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "Frontend started (PID: $FRONTEND_PID)"
sleep 5

# Wait for frontend to be ready
echo "Waiting for frontend to start..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️ Frontend may still be starting...${NC}"
    fi
    sleep 2
done

echo ""
echo "🎉 Geo Locator is running!"
echo "=========================="
echo -e "${GREEN}📍 Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}📍 Backend API: http://localhost:5001${NC}"
echo -e "${GREEN}📍 API Health: http://localhost:5001/health${NC}"
echo ""
echo -e "${YELLOW}📋 Logs:${NC}"
echo "  Backend: logs/backend.log"
echo "  Frontend: logs/frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================="

# Keep script running
while true; do
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Backend process died${NC}"
        break
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Frontend process died${NC}"
        break
    fi
    sleep 5
done
