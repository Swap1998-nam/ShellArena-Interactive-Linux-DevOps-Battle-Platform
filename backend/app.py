from flask import Flask, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def home():
    return jsonify({
        "message": "ShellArena Backend Running 🚀"
    })

@socketio.on("terminal_input")
def handle_terminal(data):
    command = data.get("command", "")

    output = f"Executed command: {command}"

    emit("terminal_output", {
        "output": output
    })

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)