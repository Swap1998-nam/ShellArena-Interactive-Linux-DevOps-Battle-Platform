CHALLENGES = [

{

"title":

"Current Directory",

"answer":

"pwd",

"xp":

50

},

{

"title":

"Current User",

"answer":

"whoami",

"xp":

50

},

{

"title":

"Disk Usage",

"answer":

"df -h",

"xp":

100

}

]


def validate(command):

    for challenge in CHALLENGES:

        if (

        command.strip()

        ==

        challenge['answer']

        ):

            return (

            True,

            challenge['xp']

            )

    return False,0