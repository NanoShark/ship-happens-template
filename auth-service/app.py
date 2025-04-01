from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:password@database-service:3306/auth_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

db = SQLAlchemy(app)

# Auth model
class Auth(db.Model):
    __tablename__ = 'auth'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email
        }

# Create tables
with app.app_context():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    
    # Check if user already exists
    existing_user = Auth.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"message": "User already exists"}), 409
    
    # Hash the password
    hashed_password = generate_password_hash(data['password'], method='sha256')
    
    # Create new auth user
    new_auth = Auth(email=data['email'], password=hashed_password)
    db.session.add(new_auth)
    db.session.commit()
    
    return jsonify({"message": "Registration successful"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    
    # Find the user
    user = Auth.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"message": "Invalid credentials"}), 401
    
    # Generate token
    token = jwt.encode({
        'user_id': user.id,
        'email': user.email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user_id": user.id,
        "email": user.email
    })

# Middleware to verify token
def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        
        try:
            token = token.split(" ")[1]  # Remove "Bearer " prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = Auth.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({"message": "Token is invalid"}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/validate-token', methods=['GET'])
@token_required
def validate_token(current_user):
    return jsonify({
        "message": "Token is valid",
        "user_id": current_user.id,
        "email": current_user.email
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)