CHALLENGES = [

{

"id":1,

"title":"Find Current Directory",

"answer":"pwd",

"xp":50

},

{

"id":2,

"title":"Check Disk Usage",

"answer":"df -h",

"xp":100

},

{

"id":3,

"title":"Current User",

"answer":"whoami",

"xp":50

}

]


def validate(command):

    for challenge in CHALLENGES:

        if command.strip() == challenge['answer']:

            return (

                True,

                challenge['xp']

            )

    return False,0