#!/bin/bash

# Cleanup script for stopping all geo-locator processes
echo "🧹 Cleaning up geo-locator processes..."

# Kill processes on port 3000 (frontend)
echo "Stopping processes on port 3000..."
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Kill processes on port 5001 (backend)
echo "Stopping processes on port 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null

# Kill React development server processes
echo "Stopping React processes..."
pkill -f "react-scripts start" 2>/dev/null
pkill -f "npm start" 2>/dev/null

# Kill Python Flask processes
echo "Stopping Flask processes..."
pkill -f "run_local.py" 2>/dev/null
pkill -f "flask run" 2>/dev/null

# Kill Node.js processes related to the project
echo "Stopping Node.js processes..."
pkill -f "node.*geo-locator" 2>/dev/null

echo "✅ Cleanup completed"
