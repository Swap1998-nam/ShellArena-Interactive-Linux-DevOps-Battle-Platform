const socket =
io(
"http://localhost:5000"
)

const terminal =
new Terminal({

cursorBlink:true

})

terminal.open(

document
.getElementById(
'terminal'
)

)

terminal.write(

'Welcome To ShellArena\r\n'

)

terminal.write(
'$ '
)

let command=''

terminal.onData(

(data)=>{

if(
data==='\r'
){

terminal.write(
'\r\n'
)

socket.emit(

'terminal_input',

{

command

}

)

command=''

}

else if(

data==='\u007F'

){

if(
command.length>0
){

command=

command.slice(
0,-1
)

terminal.write(
'\b \b'
)

}

}

else{

command+=data

terminal.write(
data
)

}

}

)

socket.on(

'terminal_output',

(data)=>{

terminal.write(

data.output

+

'\r\n$ '

)

}

)