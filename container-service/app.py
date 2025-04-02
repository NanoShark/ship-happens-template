from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import jwt
import os
import uuid
import subprocess
import threading
import time
import docker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*")

# Docker client
docker_client = docker.from_env()

# Store active container sessions
# Format: { "session_id": { "container_id": "...", "user_id": "...", "step_id": "...", "created_at": "..." } }
active_sessions = {}

# Clean up sessions that have been inactive for more than 30 minutes
def cleanup_inactive_sessions():
    while True:
        current_time = time.time()
        to_remove = []
        
        for session_id, session in active_sessions.items():
            # If session is older than 30 minutes, terminate it
            if current_time - session['created_at'] > 30 * 60:
                try:
                    # Stop and remove the container
                    container = docker_client.containers.get(session['container_id'])
                    container.stop()
                    container.remove()
                    to_remove.append(session_id)
                except:
                    pass
        
        # Remove terminated sessions
        for session_id in to_remove:
            del active_sessions[session_id]
        
        # Check every minute
        time.sleep(60)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_inactive_sessions)
cleanup_thread.daemon = True
cleanup_thread.start()

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
@app.route('/containers/create', methods=['POST'])
@token_required
def create_container(current_user_id):
    try:
        data = request.json
        step_id = data.get('step_id')
        
        if not step_id:
            return jsonify({"message": "Step ID is required"}), 400
        
        # Create a unique session ID
        session_id = str(uuid.uuid4())
        
        # Start a container for this session
        container = docker_client.containers.run(
            "docker:dind",  # Docker-in-Docker image
            detach=True,
            privileged=True,  # Required for Docker-in-Docker
            remove=False,
            environment={
                "DOCKER_TLS_CERTDIR": ""  # Disable TLS for simplicity
            }
        )
        
        # Store session info
        active_sessions[session_id] = {
            "container_id": container.id,
            "user_id": current_user_id,
            "step_id": step_id,
            "created_at": time.time()
        }
        
        return jsonify({
            "session_id": session_id,
            "message": "Container created successfully"
        })
    except Exception as e:
        return jsonify({"message": f"Error creating container: {str(e)}"}), 500

@app.route('/containers/validate/<session_id>', methods=['POST'])
@token_required
def validate_solution(current_user_id, session_id):
    try:
        # Check if session exists and belongs to user
        if session_id not in active_sessions or active_sessions[session_id]['user_id'] != current_user_id:
            return jsonify({"message": "Invalid session"}), 404
        
        data = request.json
        validation_script = data.get('validation_script')
        
        if not validation_script:
            return jsonify({"message": "Validation script is required"}), 400
        
        # Get the container
        container_id = active_sessions[session_id]['container_id']
        container = docker_client.containers.get(container_id)
        
        # Execute validation script in container
        exec_result = container.exec_run(
            cmd=["sh", "-c", validation_script],
            workdir="/workspace"
        )
        
        # Check validation result
        success = exec_result.exit_code == 0
        
        return jsonify({
            "success": success,
            "message": exec_result.output.decode('utf-8')
        })
    except Exception as e:
        return jsonify({"message": f"Error validating solution: {str(e)}"}), 500

@app.route('/containers/terminate/<session_id>', methods=['POST'])
@token_required
def terminate_container(current_user_id, session_id):
    try:
        # Check if session exists and belongs to user
        if session_id not in active_sessions or active_sessions[session_id]['user_id'] != current_user_id:
            return jsonify({"message": "Invalid session"}), 404
        
        # Get the container
        container_id = active_sessions[session_id]['container_id']
        container = docker_client.containers.get(container_id)
        
        # Stop and remove the container
        container.stop()
        container.remove()
        
        # Remove session
        del active_sessions[session_id]
        
        return jsonify({"message": "Container terminated successfully"})
    except Exception as e:
        return jsonify({"message": f"Error terminating container: {str(e)}"}), 500

# Socket.IO events for terminal
@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('join')
def handle_join(data):
    session_id = data.get('session_id')
    token = data.get('token')
    
    if not session_id or not token:
        emit('error', {'message': 'Session ID and token are required'})
        return
    
    try:
        # Verify token
        token_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = token_data['user_id']
        
        # Check if session exists and belongs to user
        if session_id not in active_sessions or active_sessions[session_id]['user_id'] != user_id:
            emit('error', {'message': 'Invalid session'})
            return
        
        # Join the room for this session
        join_room(session_id)
        emit('joined', {'message': 'Joined session successfully'})
    except Exception as e:
        emit('error', {'message': f'Error joining session: {str(e)}'})

@socketio.on('terminal_input')
def handle_terminal_input(data):
    session_id = data.get('session_id')
    command = data.get('command')
    
    if not session_id or not command:
        emit('error', {'message': 'Session ID and command are required'})
        return
    
    try:
        # Get the container for this session
        if session_id not in active_sessions:
            emit('error', {'message': 'Invalid session'})
            return
        
        container_id = active_sessions[session_id]['container_id']
        container = docker_client.containers.get(container_id)
        
        # Execute command in container
        exec_result = container.exec_run(
            cmd=["sh", "-c", command],
            workdir="/workspace"
        )
        
        # Send result back to client
        emit('terminal_output', {
            'output': exec_result.output.decode('utf-8'),
            'exit_code': exec_result.exit_code
        }, room=session_id)
    except Exception as e:
        emit('error', {'message': f'Error executing command: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5004, debug=True)