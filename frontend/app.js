const socket=io(
"http://localhost:5000"
)

const terminal=
new Terminal()

terminal.open(
document
.getElementById(
'terminal'
)
)

terminal.write(
"Welcome To ShellArena\r\n"
)

terminal.prompt=()=>{

terminal.write(
"\r\n$ "
)

}

terminal.prompt()

let command=""

terminal.onData(data=>{

if(data==="\r"){

socket.emit(
'terminal_input',
{
command
}
)

command=""

}
else{

command+=data

terminal.write(data)

}

})

socket.on(
'terminal_output',

data=>{

terminal.write(
`\r\n${data.output}`
)

terminal.prompt()

}
)