#!/bin/bash

# Geo Locator - Local Development Startup Script
echo "🚀 Starting Geo Locator Local Development Environment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a service is running
check_service() {
    if pgrep -x "$1" > /dev/null; then
        echo -e "${GREEN}✅ $1 is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 is not running${NC}"
        return 1
    fi
}

# Check required dependencies
echo "🔍 Checking dependencies..."

# Check Python
if command_exists python3; then
    echo -e "${GREEN}✅ Python3 found${NC}"
else
    echo -e "${RED}❌ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check Node.js
if command_exists node; then
    echo -e "${GREEN}✅ Node.js found${NC}"
else
    echo -e "${RED}❌ Node.js not found. Please install Node.js 16+${NC}"
    exit 1
fi

# Check PostgreSQL
if command_exists psql; then
    echo -e "${GREEN}✅ PostgreSQL client found${NC}"
    if check_service "postgres"; then
        echo -e "${GREEN}✅ PostgreSQL service is running${NC}"
    else
        echo -e "${YELLOW}⚠️  PostgreSQL service not running. Starting...${NC}"
        sudo systemctl start postgresql || {
            echo -e "${RED}❌ Failed to start PostgreSQL${NC}"
            echo "Please start PostgreSQL manually: sudo systemctl start postgresql"
            exit 1
        }
    fi
else
    echo -e "${RED}❌ PostgreSQL not found. Please install PostgreSQL 13+${NC}"
    exit 1
fi

# Check Redis
if command_exists redis-server; then
    echo -e "${GREEN}✅ Redis found${NC}"
    if check_service "redis-server"; then
        echo -e "${GREEN}✅ Redis service is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis service not running. Starting...${NC}"
        sudo systemctl start redis || {
            echo -e "${RED}❌ Failed to start Redis${NC}"
            echo "Please start Redis manually: sudo systemctl start redis"
            exit 1
        }
    fi
else
    echo -e "${RED}❌ Redis not found. Please install Redis${NC}"
    exit 1
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "📝 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Setup database
echo "🗄️  Setting up database..."
export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
psql -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-postgres}" -c "CREATE DATABASE ${POSTGRES_DB:-geo_locator};" 2>/dev/null || echo "Database may already exist"
psql -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-postgres}" -c "CREATE USER geo_user WITH PASSWORD 'geo_password';" 2>/dev/null || echo "User may already exist"
psql -h "${POSTGRES_HOST:-localhost}" -U "${POSTGRES_USER:-postgres}" -c "GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB:-geo_locator} TO geo_user;" 2>/dev/null

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

# Create .env file if it doesn't exist
cd ..
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=geo_locator

# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Keys (replace with your actual keys)
YANDEX_API_KEY=your_yandex_api_key_here
DGIS_API_KEY=your_dgis_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Security
SECRET_KEY=dev-secret-key-change-in-production
EOF
    echo -e "${YELLOW}⚠️  Please update .env file with your actual API keys${NC}"
fi

# Start services
echo "🚀 Starting services..."

# Start backend
echo "Starting backend server..."
cd backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found at backend/venv/"
    echo "Please run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
export POSTGRES_PASSWORD=3666599
python run_local.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "Starting frontend server..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "🎉 Geo Locator is starting up!"
echo "=================================================="
echo -e "${GREEN}📍 Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}📍 Backend API: http://localhost:5000${NC}"
echo -e "${GREEN}📍 API Health: http://localhost:5000/health${NC}"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM

# Wait for processes
wait
