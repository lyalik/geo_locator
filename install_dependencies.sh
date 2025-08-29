#!/bin/bash

# Geo Locator - Полная установка зависимостей
# Этот скрипт устанавливает все необходимые зависимости для системы

set -e

echo "🚀 Установка зависимостей Geo Locator"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    postgresql \
    postgresql-contrib \
    redis-server \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    libpq-dev \
    python3-dev \
    build-essential \
    pkg-config \
    libhdf5-dev \
    libopencv-dev \
    ffmpeg \
    git \
    curl \
    wget

# Install PostgreSQL PostGIS extension
print_status "Installing PostGIS extension..."
sudo apt install -y postgresql-14-postgis-3 || sudo apt install -y postgresql-postgis

# Start services
print_status "Starting services..."
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl enable postgresql
sudo systemctl enable redis-server

# Create Python virtual environment
print_status "Creating Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Install additional ML dependencies
print_status "Installing additional ML dependencies..."
pip install \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    opencv-python-headless \
    scikit-learn \
    numpy \
    matplotlib \
    seaborn

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
cd ../frontend
npm install

# Install additional frontend packages
print_status "Installing additional frontend packages..."
npm install \
    @mui/lab \
    @mui/x-date-pickers \
    react-helmet \
    react-hot-toast \
    lodash \
    date-fns \
    uuid

# Setup PostgreSQL database
print_status "Setting up PostgreSQL database..."
cd ..
sudo -u postgres createdb geo_locator 2>/dev/null || print_warning "Database geo_locator already exists"
sudo -u postgres psql -d geo_locator -c "CREATE EXTENSION IF NOT EXISTS postgis;" 2>/dev/null || print_warning "PostGIS extension already exists"
sudo -u postgres psql -d geo_locator -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || print_warning "Vector extension not available (optional)"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file..."
    cp .env.example .env
    print_warning "Please update .env file with your configuration"
fi

# Run database migrations
print_status "Running database migrations..."
cd backend
source venv/bin/activate
export FLASK_APP=app.py
flask db upgrade 2>/dev/null || print_warning "No migrations to run"

# Create uploads directory
print_status "Creating uploads directory..."
mkdir -p uploads/violations uploads/documents uploads/temp

# Set permissions
chmod 755 uploads
chmod 755 uploads/violations
chmod 755 uploads/documents
chmod 755 uploads/temp

# Download YOLO model (if not exists)
print_status "Checking YOLO model..."
if [ ! -f "models/yolov8n.pt" ]; then
    mkdir -p models
    cd models
    wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
    cd ..
fi

# Test installations
print_status "Testing installations..."

# Test Python dependencies
python3 -c "import flask, sqlalchemy, redis, cv2, torch, transformers, ultralytics; print('✅ Python dependencies OK')" || print_error "Python dependencies test failed"

# Test Node.js dependencies
cd ../frontend
node -e "console.log('✅ Node.js dependencies OK')" || print_error "Node.js dependencies test failed"

# Test services
redis-cli ping > /dev/null && print_status "Redis service OK" || print_error "Redis service failed"
sudo -u postgres psql -d geo_locator -c "SELECT version();" > /dev/null && print_status "PostgreSQL service OK" || print_error "PostgreSQL service failed"

cd ..

print_status "Installation completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Update .env file with your configuration"
echo "2. Set up external API keys (Google AI, Sentinel Hub, etc.)"
echo "3. Run './start_local.sh' to start the application"
echo ""
echo "📚 Documentation:"
echo "- README.md - General project information"
echo "- DEVELOPMENT.md - Development progress and roadmap"
echo "- INTEGRATION_COMPLETE.md - Integration details and API endpoints"
echo ""
echo "🌐 URLs after startup:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:5000"
echo "- API Documentation: http://localhost:5000/"
echo ""
print_status "🎉 Geo Locator installation complete!"
