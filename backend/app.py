from flask import Flask, request, jsonify, send_from_directory
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import json
import os

# Import models and db
from models import db, User, Photo, Violation, ProcessingTask

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
CORS(app, supports_credentials=True, origins=['http://localhost:3000'])

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = None  # Disable automatic redirects for API endpoints

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
# with app.app_context():
#     db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and check_password_hash(user.password, data['password']):
        login_user(user)
        return jsonify({"message": "Logged in successfully"}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/auth/me', methods=['GET'])
@login_required
def api_me():
    if not current_user.is_authenticated:
        return jsonify({"message": "Not authenticated"}), 401
    
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }), 200

@app.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    # Получаем логин (может быть email или username)
    login_field = data.get('email') or data.get('username') or data.get('login')
    password = data.get('password')
    
    if not login_field or not password:
        return jsonify({"message": "Login and password are required"}), 400
    
    # Ищем пользователя по email или username
    user = User.query.filter(
        (User.email == login_field) | (User.username == login_field)
    ).first()
    
    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({
            "message": "Logged in successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/auth/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({"message": "Missing required fields"}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({"message": "User already exists"}), 400
        
        # Check if username already exists
        existing_username = User.query.filter_by(username=data['username']).first()
        if existing_username:
            return jsonify({"message": "Username already exists"}), 400
        
        hashed_password = generate_password_hash(data['password'])
        new_user = User(username=data['username'], email=data['email'], password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return jsonify({
            "message": "User registered successfully",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Registration failed: {str(e)}"}), 500

@app.route('/auth/logout', methods=['POST'])
def api_logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


# Ensure upload directory exists
os.makedirs(app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads')), exist_ok=True)

# Serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Register API blueprints individually
try:
    from routes.maps import bp as maps_bp
    app.register_blueprint(maps_bp)
    print("✅ Maps API registered successfully")
except Exception as e:
    print(f"❌ Maps API registration failed: {e}")

try:
    from routes.violation_api import bp as violation_api_bp
    app.register_blueprint(violation_api_bp)
    print("✅ Violation API registered successfully")
except Exception as e:
    print(f"❌ Violation API registration failed: {e}")

try:
    from routes.geo_api import geo_bp
    app.register_blueprint(geo_bp)
    print("✅ Geo API registered successfully")
except Exception as e:
    print(f"❌ Geo API registration failed: {e}")

try:
    from routes.cache_api import bp as cache_api_bp
    app.register_blueprint(cache_api_bp)
    print("✅ Cache API registered successfully")
except Exception as e:
    print(f"❌ Cache API registration failed: {e}")

try:
    from routes.rosreestr_api import bp as rosreestr_bp
    app.register_blueprint(rosreestr_bp)
    print("✅ Rosreestr API registered successfully")
except Exception as e:
    print(f"❌ Rosreestr API registration failed: {e}")

try:
    from routes.openstreetmap_api import bp as openstreetmap_bp
    app.register_blueprint(openstreetmap_bp)
    print("✅ OpenStreetMap API registered successfully")
except Exception as e:
    print(f"❌ OpenStreetMap API registration failed: {e}")

try:
    from routes.sentinel_api import sentinel_api
    app.register_blueprint(sentinel_api, url_prefix='/api/sentinel')
    print("✅ Sentinel API registered successfully")
except Exception as e:
    print(f"❌ Sentinel API registration failed: {e}")

# Register Satellite API separately
try:
    from routes.satellite_api import satellite_bp
    app.register_blueprint(satellite_bp, url_prefix='/api/satellite')
    print("✅ Satellite API registered successfully")
except Exception as e:
    print(f"❌ Satellite API registration failed: {e}")
    import traceback
    traceback.print_exc()

# Register OCR API separately to catch specific errors
try:
    from routes.ocr_api import ocr_api
    app.register_blueprint(ocr_api, url_prefix='/api/ocr')
    print("✅ OCR API registered successfully")
except Exception as e:
    print(f"❌ OCR API registration failed: {e}")
    import traceback
    traceback.print_exc()

# Register Notification API
try:
    from routes.notification_api import notification_api
    app.register_blueprint(notification_api, url_prefix='/api/notifications')
    print("✅ Notification API registered successfully")
except Exception as e:
    print(f"❌ Notification API registration failed: {e}")
    import traceback
    traceback.print_exc()

# Register OpenStreetMap API
try:
    from routes.openstreetmap_api import bp as osm_bp
    app.register_blueprint(osm_bp, url_prefix='/api/osm')
    print("✅ OpenStreetMap API registered successfully")
except Exception as e:
    print(f"❌ OpenStreetMap API registration failed: {e}")
    import traceback
    traceback.print_exc()

@app.route('/')
def index():
    """Show available API endpoints."""
    routes = []
    for rule in app.url_map.iter_rules():
        # Skip static routes and debugger routes
        if not rule.rule.startswith('/static') and not rule.rule.startswith('/debugtoolbar'):
            routes.append({
                'endpoint': rule.endpoint,
                'methods': sorted(rule.methods - {'OPTIONS', 'HEAD'}),
                'path': rule.rule
            })
    return jsonify({
        'name': 'Geo Locator API',
        'endpoints': routes
    })

@app.route('/health', methods=['GET'])
def health():
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        db_status = 'connected' if inspector.has_table('users') else 'no users table'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'version': '1.0',
        'database': db_status
    })

# This endpoint is now handled by the violation_api blueprint
if __name__ == '__main__':
    app.run(debug=True)
