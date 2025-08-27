from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

import os

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
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


# Ensure upload directory exists
os.makedirs(app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads')), exist_ok=True)

# Serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Register API blueprints
try:
    from routes.maps import bp as maps_bp
    from routes.violation_api import bp as violation_bp
    app.register_blueprint(maps_bp)
    app.register_blueprint(violation_bp)
except Exception as e:
    # Avoid crashing startup if blueprints fail to import; log later
    pass

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok'
    })

@app.route('/api/violations/detect', methods=['POST'])
def detect_violations():
    # Implement the violation detection logic here
    data = request.get_json()
    image_path = data['image_path']
    result = perform_violation_detection(image_path)

    # Write the result to a file
    with open('violation_detection_result.json', 'w') as f:
        json.dump(result, f)

    return jsonify(result)

def perform_violation_detection(image_path):
    # Dummy implementation of the violation detection logic
    # Replace this with the actual implementation
    return {
        "violation_detected": True,
        "details": "Dummy details of the detected violation."
    }
if __name__ == '__main__':
    app.run(debug=True)
