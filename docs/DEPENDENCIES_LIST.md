# 📦 **GEO LOCATOR - Полный список зависимостей**

## 🐍 **Backend Dependencies (Python)**

### **Core Framework**
```
flask==3.0.3                 # Web framework
flask-sqlalchemy==3.1.1      # ORM integration
flask-cors==4.0.1             # CORS support
flask-migrate==4.0.7          # Database migrations
flask-login==0.6.3            # User authentication
werkzeug==3.0.3               # WSGI utilities
```

### **Database & Storage**
```
sqlalchemy==2.0.32            # SQL toolkit and ORM
psycopg2-binary==2.9.9        # PostgreSQL adapter
geoalchemy2==0.15.2           # Spatial database extension
pgvector==0.3.0               # Vector similarity search
redis==5.0.8                  # In-memory data store
celery==5.4.0                 # Distributed task queue
```

### **AI & Machine Learning**
```
torch==2.4.0                 # PyTorch deep learning framework
torchvision==0.19.0          # Computer vision for PyTorch
ultralytics==8.0.196         # YOLOv8 object detection
transformers==4.44.0         # Hugging Face transformers
opencv-python==4.10.0.84     # Computer vision library
pillow==10.4.0               # Python Imaging Library
numpy>=1.26.0                # Numerical computing
scipy==1.14.1                # Scientific computing
scikit-image==0.24.0         # Image processing
matplotlib==3.9.2            # Plotting library
```

### **Geospatial & Mapping**
```
geopy==2.4.1                 # Geocoding library
shapely==2.0.6               # Geometric objects manipulation
fiona==1.10.1                # OGR vector data access
rasterio==1.4.1              # Raster data I/O
pyproj==3.7.0                # Cartographic projections
folium==0.17.0               # Interactive maps
exifread==3.0.0              # EXIF metadata extraction
```

### **External APIs & Services**
```
requests==2.32.3             # HTTP library
aiohttp==3.10.11             # Async HTTP client/server
google-generativeai==0.7.2   # Google Gemini API
google-cloud-vision==3.7.2   # Google Vision API
sentinelhub==3.10.3          # Sentinel satellite data
requests-oauthlib==2.0.0     # OAuth for requests
oauthlib==3.2.2              # OAuth implementation
```

### **Media Processing**
```
ffmpeg-python==0.2.0         # FFmpeg wrapper
stitching==0.5.1             # Image stitching
imageio==2.35.1              # Image I/O
pytesseract==0.3.10          # OCR wrapper for Tesseract
```

### **Utilities & Tools**
```
python-dotenv==1.0.1         # Environment variables
tenacity==9.0.0              # Retry library
jinja2==3.1.4                # Template engine
email-validator==2.1.1       # Email validation
python-magic==0.4.27         # File type detection
click==8.1.7                 # Command line interface
tqdm==4.66.5                 # Progress bars
pandas==2.2.3                # Data manipulation
aiofiles==24.1.0             # Async file operations
```

### **Development & Testing**
```
pytest==8.3.2                # Testing framework
pytest-flask==1.3.0          # Flask testing utilities
pytest-cov==5.0.0            # Coverage plugin
```

---

## ⚛️ **Frontend Dependencies (Node.js)**

### **Core Framework**
```json
{
  "react": "^18.3.1",                    // React library
  "react-dom": "^18.3.1",               // React DOM rendering
  "react-scripts": "5.0.1",             // Create React App scripts
  "react-router-dom": "^6.15.0"         // React routing
}
```

### **UI Components & Styling**
```json
{
  "@mui/material": "^5.14.1",           // Material-UI components
  "@mui/icons-material": "^5.14.1",     // Material-UI icons
  "@emotion/react": "^11.11.1",         // CSS-in-JS library
  "@emotion/styled": "^11.11.0",        // Styled components
  "notistack": "^3.0.2"                 // Notification system
}
```

### **Data Visualization**
```json
{
  "@mui/x-charts": "^6.0.0",            // MUI charts
  "@mui/x-data-grid": "^6.16.0",        // Data grid component
  "recharts": "^2.8.0"                  // Chart library
}
```

### **Maps & Geolocation**
```json
{
  "leaflet": "^1.9.4",                  // Interactive maps
  "react-leaflet": "^4.2.1",            // React Leaflet integration
  "react-leaflet-cluster": "^2.1.0",    // Marker clustering
  "@pbe/react-yandex-maps": "^1.2.5",   // Yandex Maps for React
  "2gis-maps": "^3.0.0"                 // 2GIS Maps integration
}
```

### **HTTP & State Management**
```json
{
  "axios": "^1.7.3",                    // HTTP client
  "react-query": "^3.39.3"              // Data fetching and caching
}
```

### **File Upload & Processing**
```json
{
  "react-dropzone": "^14.3.8"           // Drag and drop file uploads
}
```

---

## 🖥️ **System Dependencies**

### **Ubuntu/Debian**
```bash
# Core development tools
build-essential
python3-dev
python3-venv
nodejs
npm

# Database systems
postgresql
postgresql-contrib
postgresql-server-dev-all
redis-server

# Geospatial libraries
gdal-bin
libgdal-dev
libproj-dev
libgeos-dev

# Computer vision libraries
libgl1-mesa-glx
libglib2.0-0
libsm6
libxext6
libxrender-dev
libgomp1

# OCR support
tesseract-ocr
tesseract-ocr-rus

# Media processing
ffmpeg

# System utilities
curl
wget
git
```

### **macOS (via Homebrew)**
```bash
# Core tools
python@3.8
node
postgresql
redis

# Geospatial
gdal

# OCR
tesseract
tesseract-lang

# Media
ffmpeg
```

### **Windows (via Chocolatey)**
```powershell
# Core tools
python --version=3.8.10
nodejs
postgresql
redis-64
git

# Additional tools
vcredist2019  # Visual C++ Redistributable
```

---

## 🐳 **Docker Dependencies**

### **Base Images**
```dockerfile
# Backend
FROM python:3.8-slim

# Frontend
FROM node:18-alpine

# Database
FROM postgis/postgis:14-3.2

# Cache
FROM redis:7-alpine
```

### **Docker Compose Services**
```yaml
services:
  postgres:
    image: postgis/postgis:14-3.2
    
  redis:
    image: redis:7-alpine
    
  backend:
    build: ./backend
    
  frontend:
    build: ./frontend
```

---

## 🔧 **Development Tools**

### **Code Quality**
```
# Python
black                         # Code formatter
flake8                        # Linting
mypy                          # Type checking
isort                         # Import sorting

# JavaScript
eslint                        # Linting
prettier                      # Code formatting
```

### **Testing**
```
# Python
pytest                        # Testing framework
pytest-cov                   # Coverage
pytest-mock                  # Mocking

# JavaScript
jest                          # Testing framework (included in react-scripts)
@testing-library/react       # React testing utilities
```

---

## 📊 **Production Dependencies**

### **Web Server**
```
gunicorn==21.2.0             # WSGI HTTP Server
nginx                        # Reverse proxy (system package)
```

### **Process Management**
```
supervisor                   # Process control system
systemd                      # System and service manager (Linux)
```

### **Monitoring**
```
prometheus-client==0.17.1    # Metrics collection
sentry-sdk==1.32.0          # Error tracking
```

### **Security**
```
cryptography==41.0.4        # Cryptographic recipes
bcrypt==4.0.1               # Password hashing
```

---

## 🌐 **External Services**

### **Required API Keys**
```
YANDEX_API_KEY               # Yandex Maps API
DGIS_API_KEY                 # 2GIS API
MISTRAL_API_KEY              # Mistral AI API
```

### **Optional API Keys**
```
ROSCOSMOS_API_KEY            # Roscosmos satellite data
GOOGLE_VISION_API_KEY        # Google Vision API
SENTINELHUB_CLIENT_ID        # Sentinel Hub
SENTINELHUB_CLIENT_SECRET    # Sentinel Hub
```

---

## 💾 **Storage Requirements**

### **Disk Space**
```
Base installation:           ~2GB
Python dependencies:         ~3GB
Node.js dependencies:        ~500MB
YOLO model:                  ~6MB
Sample data:                 ~1GB
Logs and cache:              ~500MB
Total recommended:           ~10GB
```

### **Database Storage**
```
PostgreSQL base:             ~100MB
Sample violations data:      ~50MB
Spatial indexes:             ~20MB
Growth per 1000 violations:  ~10MB
```

---

## 🚀 **Installation Commands**

### **Backend Setup**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download YOLO model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### **Frontend Setup**
```bash
# Install Node.js dependencies
npm install

# Build for production
npm run build
```

### **System Setup**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-dev nodejs postgresql redis-server

# macOS
brew install python@3.8 node postgresql redis

# Start services
sudo systemctl start postgresql redis-server  # Linux
brew services start postgresql redis          # macOS
```

---

## 🔍 **Version Compatibility**

### **Python Versions**
- **Supported:** 3.8, 3.9, 3.10, 3.11
- **Recommended:** 3.8+ (tested)
- **Not supported:** < 3.8

### **Node.js Versions**
- **Supported:** 16.x, 18.x, 20.x
- **Recommended:** 18.x (LTS)
- **Not supported:** < 16.x

### **Database Versions**
- **PostgreSQL:** 12+, 13, 14, 15 (recommended: 14+)
- **Redis:** 6.0+, 7.x (recommended: 7.x)

---

## ⚡ **Performance Optimization**

### **Python Optimizations**
```bash
# Install optimized packages
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118  # CUDA
pip install opencv-python-headless  # Headless OpenCV for servers
```

### **Node.js Optimizations**
```bash
# Production build
npm run build
npm install -g serve
serve -s build -l 3000
```

### **Database Optimizations**
```sql
-- PostgreSQL configuration
shared_preload_libraries = 'postgis-3'
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
```

---

*Список зависимостей обновлен: 16 сентября 2025 г.*
*Версия проекта: 1.0.0*
