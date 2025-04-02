from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:password@database-service:3306/tutorials_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

db = SQLAlchemy(app)

# Models
class Tutorial(db.Model):
    __tablename__ = 'tutorials'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False)
    steps = db.relationship('TutorialStep', backref='tutorial', lazy=True, order_by='TutorialStep.order')
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "order": self.order,
            "steps_count": len(self.steps)
        }

class TutorialStep(db.Model):
    __tablename__ = 'tutorial_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorials.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    validation_script = db.Column(db.Text, nullable=False)  # Script to validate user's solution
    order = db.Column(db.Integer, nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "tutorial_id": self.tutorial_id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "order": self.order
        }

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    step_id = db.Column(db.Integer, db.ForeignKey('tutorial_steps.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "step_id": self.step_id,
            "completed": self.completed,
            "completed_at": self.completed_at
        }

# Create tables
with app.app_context():
    db.create_all()
    
    # Add sample data if tables are empty
    if Tutorial.query.count() == 0:
        # Add a sample tutorial
        tutorial = Tutorial(
            title="Docker Basics",
            description="Learn the fundamentals of Docker containers", 
            order=1
        )
        db.session.add(tutorial)
        db.session.commit()
        
        # Add sample steps
        steps = [
            TutorialStep(
                tutorial_id=tutorial.id,
                title="What is Docker?",
                description="Introduction to Docker",
                content="Docker is a platform for developing, shipping, and running applications in containers...",
                validation_script="# No validation for this introductory step\nexit 0",
                order=1
            ),
            TutorialStep(
                tutorial_id=tutorial.id,
                title="Your First Container",
                description="Run your first Docker container",
                content="In this step, you'll learn to run a simple container using the 'docker run' command...",
                validation_script="docker ps -a | grep hello-world && echo 'Success!' && exit 0 || echo 'Try again' && exit 1",
                order=2
            ),
            TutorialStep(
                tutorial_id=tutorial.id,
                title="Building Images",
                description="Create your own Docker image",
                content="Now, you'll learn to create a Dockerfile and build your own image...",
                validation_script="docker images | grep myimage && echo 'Success!' && exit 0 || echo 'Try again' && exit 1",
                order=3
            )
        ]
        
        for step in steps:
            db.session.add(step)
        
        db.session.commit()

# Middleware to verify token
def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        
        try:
            token = token.split(" ")[1]  # Remove "Bearer " prefix
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except:
            return jsonify({"message": "Token is invalid"}), 401
            
        return f(current_user_id, *args, **kwargs)
    
    return decorated

# Routes
@app.route('/tutorials', methods=['GET'])
@token_required
def get_tutorials(current_user_id):
    tutorials = Tutorial.query.order_by(Tutorial.order).all()
    return jsonify([tutorial.to_dict() for tutorial in tutorials])

@app.route('/tutorials/steps', methods=['GET'])
@token_required
def get_steps_with_progress(current_user_id):
    steps = TutorialStep.query.order_by(TutorialStep.order).all()
    progress = UserProgress.query.filter_by(user_id=current_user_id).all()
    
    # Create a mapping of completed steps
    completed_steps = {p.step_id: p.completed for p in progress}
    
    # Get the current step (first uncompleted step)
    current_step_id = None
    for step in steps:
        if step.id not in completed_steps or not completed_steps[step.id]:
            current_step_id = step.id
            break
    
    result = []
    for step in steps:
        step_dict = step.to_dict()
        step_dict['completed'] = completed_steps.get(step.id, False)
        step_dict['current'] = step.id == current_step_id
        result.append(step_dict)
    
    return jsonify(result)

@app.route('/tutorials/steps/<int:step_id>', methods=['GET'])
@token_required
def get_step(current_user_id, step_id):
    step = TutorialStep.query.get_or_404(step_id)
    progress = UserProgress.query.filter_by(user_id=current_user_id, step_id=step_id).first()
    
    result = step.to_dict()
    result['completed'] = progress.completed if progress else False
    
    return jsonify(result)

@app.route('/tutorials/steps/<int:step_id>/complete', methods=['POST'])
@token_required
def complete_step(current_user_id, step_id):
    from datetime import datetime
    
    # Check if step exists
    step = TutorialStep.query.get_or_404(step_id)
    
    # Update or create progress record
    progress = UserProgress.query.filter_by(user_id=current_user_id, step_id=step_id).first()
    
    if progress:
        progress.completed = True
        progress.completed_at = datetime.utcnow()
    else:
        progress = UserProgress(
            user_id=current_user_id,
            step_id=step_id,
            completed=True,
            completed_at=datetime.utcnow()
        )
        db.session.add(progress)
    
    db.session.commit()
    
    return jsonify({"message": "Step marked as completed"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)