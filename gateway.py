import os
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # allow cross-origin

# In-memory storage (replace with Redis or DB for production)
store = {"account_id": None}

@app.route('/')
def index():
    return render_template("gateway.html")  # Optional: HTML test page

ACCOUNT_FILE_PATH = "/tmp/account_id.txt"

@app.route('/set_account', methods=['POST'])
def set_account():
    account_id = request.args.get("account_id")  # <-- from URL/query param
    if not account_id:
        return jsonify({"error": "Missing account_id"}), 400

    with open(ACCOUNT_FILE_PATH, "w") as f:
        f.write(account_id)

    return jsonify({"status": "success", "account_id": account_id})


@app.route('/get_account', methods=['GET'])
def get_account():
    if os.path.exists(ACCOUNT_FILE_PATH):
        with open(ACCOUNT_FILE_PATH) as f:
            account_id = f.read().strip()
    else:
        account_id = None

    return jsonify({"account_id": account_id})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
