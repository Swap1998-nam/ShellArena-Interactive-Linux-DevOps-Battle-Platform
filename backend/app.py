from flask import Flask

from flask_socketio import (
SocketIO,
emit
)

from docker_manager import (
execute_command
)

app=Flask(__name__)

socketio=SocketIO(
app,
cors_allowed_origins="*"
)

@app.route('/')

def health():

    return {

    "status":

    "ShellArena Running"

    }

@socketio.on(
'terminal_input'
)

def handle(
data
):

    cmd=data['command']

    output=execute_command(cmd)

    emit(

    'terminal_output',

    {

    'output':

    output

    }

    )

if __name__=="__main__":

    socketio.run(

    app,

    host="0.0.0.0",

    port=5000

)