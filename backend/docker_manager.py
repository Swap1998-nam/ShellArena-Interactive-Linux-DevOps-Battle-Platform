import docker

client = docker.from_env()

def execute_command(cmd):

    try:

        output = client.containers.run(
            "ubuntu:22.04",
            command=["sh", "-c", cmd],
            remove=True,
            stdout=True,
            stderr=True
        )

        return output.decode()

    except Exception as e:

        return str(e)