import os
import time

from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from langchain_google_genai import ChatGoogleGenerativeAI
from SearchAgent.Searcher import Searcher
from DBAgent.Querier import Querier
from SuperviseAgent.buildGraph import GraphBuilder

load_dotenv(override=True)
base_model = os.getenv("MODEL")
base_api = os.getenv("BASE_API")

llm = ChatGoogleGenerativeAI(
    model=base_model, google_api_key=base_api, temperature=0)
querier = Querier()
searcher = Searcher()
graph = GraphBuilder(llm, querier, searcher).buildGraph()

# Load .env file
load_dotenv(override=True)
# Get values from .env
base_api = os.getenv("BASE_API")
base_url = os.getenv("BASE_URL")

app = Flask(__name__)
socketio = SocketIO(app)

agent = Searcher()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/execute_task', methods=['POST'])
def execute_task():
    agent.task_stopped = False
    agent.stop_processing = False
    task = request.json.get('task')
    try:
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
            # agent.execute(task)
            for s in graph.stream(
            {"messages": [("user", task)]}, subgraphs=True
            ):
                print(s)
                print("----")
            # msg = {"messages": [("user", task)]}
            # messages = graph.invoke(msg, subgraphs=True)
            # print(messages['messages'][-1].content)
            if agent.task_stopped is True:
                emit('receive_message', {'status': 'error', 'message': 'Task execution stopped'})
            else:
                emit('receive_message', {'status': 'completed', 'message': 'Task executed successfully'})
                agent.task_stopped = False
        except Exception as e:
            # Handle any errors during task execution
            emit('receive_message', {'status': 'error', 'message': str(e)})

@app.after_request
def add_header(response):
    response.headers['X-Frame-Options'] = 'ALLOW-FROM http://localhost:8080'
    return response


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8081, allow_unsafe_werkzeug=True)
