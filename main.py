import os
import time

from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from SearchAgent import SearchAgent

# Load .env file
load_dotenv(override=True)
# Get values from .env
base_api = os.getenv("BASE_API")
base_url = os.getenv("BASE_URL")

app = Flask(__name__)
socketio = SocketIO(app)

agent = SearchAgent()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/execute_task', methods=['POST'])
def execute_task():
    agent.task_stopped = False
    agent.stop_processing = False
    task = request.json.get('task')
    try:
        agent.execute(task)
        return jsonify({'status': 'success', 'message': 'Task executed successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@socketio.on('clear')
def clear():
    try:
        agent.clear_global_history = True  # Clear global history
        agent.task_stopped = False
        agent.stop_processing = False
        print(agent.global_history)
        return jsonify({'status': 'success', 'message': 'Tasks cleared successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@socketio.on('stop_processing')
def stop_processing():
    agent.stop_processing = True  # Clear global history
    emit('receive_message', {'status': 'error', 'message': 'Stopping task... please wait'})



@socketio.on('send_message')
def handle_send_message(data):
        task = data.get('task')
        try:
            # Execute the task
            agent.execute(task)
            if agent.task_stopped is True:
                emit('receive_message', {'status': 'error', 'message': 'Task execution stopped'})
            else:
                emit('receive_message', {'status': 'completed', 'message': 'Task executed successfully'})
                agent.task_stopped = False
        except Exception as e:
            # Handle any errors during task execution
            emit('receive_message', {'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
