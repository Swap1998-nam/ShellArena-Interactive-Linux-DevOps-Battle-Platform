from flask import Flask
from challenges import validate
from flask_socketio import SocketIO, emit

from docker_manager import execute_command

app = Flask(__name__)

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)


@app.route('/')
def health():

    return {
        "status": "ShellArena Running 🚀"
    }


@socketio.on('terminal_input')
def handle(data):

    try:

        cmd = data.get('command', '').strip()

        if not cmd:

            emit(
                'terminal_output',
                {
                    'output': 'No command entered'
                }
            )

            return

        output = execute_command(cmd)

        success,xp = validate(cmd)

        if success:

         output += (

         f"\n\n🏆 Challenge Completed"

         f"\n+{xp} XP"

        )

        emit(
            'terminal_output',
            {
                'output': output
            }
        )

    except Exception as e:

        emit(
            'terminal_output',
            {
                'output': f'Error: {str(e)}'
            }
        )


if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )