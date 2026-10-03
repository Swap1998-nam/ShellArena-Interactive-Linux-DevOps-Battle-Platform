"""Mission content. Validation rules stay server-side."""


def mission(slug, title, category, difficulty, xp, minutes, description, objectives, hints, tags):
    return dict(
        id=slug,
        title=title,
        category=category,
        difficulty=difficulty,
        xp=xp,
        minutes=minutes,
        description=description,
        objectives=objectives,
        hints=hints,
        tags=tags,
    )


def step(label, rule, value):
    return dict(label=label, rule=rule, value=value)


MISSIONS = [
    mission(
        "first-contact",
        "First contact",
        "Linux",
        "Beginner",
        100,
        5,
        "Every great engineer starts with a prompt. Get your bearings, identify your user, and inspect the workspace.",
        [
            step("Find your current directory", "command", "pwd"),
            step("Identify your current user", "command", "whoami"),
            step("List the workspace files", "command", "ls"),
        ],
        ["Run pwd to see where you are.", "whoami identifies your user; ls lists the files around you."],
        ["navigation", "shell"],
    ),
    mission(
        "read-the-signals",
        "Read the signals",
        "Linux",
        "Beginner",
        150,
        8,
        "An application is reporting errors. Read its log, isolate the failures, and inspect the most recent entries.",
        [
            step("Read /var/log/app.log", "contains", "cat /var/log/app.log"),
            step("Find ERROR entries in the application log", "grep", "ERROR"),
            step("Read the last 3 log lines", "contains", "tail -n 3 /var/log/app.log"),
        ],
        [
            "Use cat /var/log/app.log to read the log.",
            "Try grep ERROR /var/log/app.log and tail -n 3 /var/log/app.log.",
        ],
        ["logs", "troubleshooting"],
    ),
    mission(
        "release-workspace",
        "A place for every release",
        "Linux",
        "Beginner",
        150,
        7,
        "Prepare a clean release directory and copy the application configuration into it.",
        [
            step("Create /workspace/releases", "directory", "/workspace/releases"),
            step(
                "Copy config.env to releases/config.env",
                "file_equals",
                ["/workspace/releases/config.env", "APP_ENV=staging\nPORT=8080\n"],
            ),
            step("Create releases/READY", "file", "/workspace/releases/READY"),
        ],
        [
            "Use mkdir releases while in /workspace.",
            "Run cp config.env releases/config.env, then touch releases/READY.",
        ],
        ["files", "deployment"],
    ),
    mission(
        "least-privilege",
        "For your eyes only",
        "Security",
        "Intermediate",
        200,
        8,
        "A configuration file is readable by everyone. Restrict it to its owner and verify the new permission mode.",
        [
            step("Set config.env permissions to 600", "mode", ["/workspace/config.env", "600"]),
            step("Inspect config.env with stat", "contains", "stat config.env"),
        ],
        ["chmod changes permissions. Owner read + write is 6.", "Use chmod 600 config.env, then stat config.env."],
        ["permissions", "hardening"],
    ),
    mission(
        "error-budget",
        "Count the failures",
        "Linux",
        "Intermediate",
        200,
        10,
        "Turn noisy logs into a useful number. Filter the errors and count them using a pipeline.",
        [
            step("Count application log lines", "contains", "wc -l /var/log/app.log"),
            step("Pipe ERROR entries into wc -l", "pipeline", "grep ERROR /var/log/app.log | wc -l"),
        ],
        ["wc -l counts input lines.", "Combine grep ERROR /var/log/app.log with wc -l using |."],
        ["pipes", "observability"],
    ),
    mission(
        "release-note",
        "Leave a release note",
        "Linux",
        "Beginner",
        150,
        6,
        "Write a small deployment artifact. Create a release note with the content release-ready and read it back.",
        [
            step(
                "Write release-ready to /workspace/release.txt",
                "file_equals",
                ["/workspace/release.txt", "release-ready\n"],
            ),
            step("Read release.txt", "contains", "cat release.txt"),
        ],
        [
            "echo prints text and > writes it into a file.",
            "Run echo release-ready > release.txt, then cat release.txt.",
        ],
        ["redirection", "files"],
    ),
    mission(
        "disk-detective",
        "Where did the space go?",
        "Linux",
        "Beginner",
        150,
        6,
        "Investigate a disk alert using filesystem capacity and directory usage in this simulated host.",
        [
            step("Inspect human-readable filesystem usage", "contains", "df -h"),
            step("Summarize /var/log disk usage", "contains", "du -sh /var/log"),
        ],
        ["df -h shows filesystem capacity.", "du -sh /var/log summarizes the size of the log directory."],
        ["storage", "incident"],
    ),
    mission(
        "process-patrol",
        "Process patrol",
        "Linux",
        "Intermediate",
        200,
        8,
        "Inspect the running processes and find the worker that is consuming CPU in the practice snapshot.",
        [
            step("List the running processes", "contains", "ps aux"),
            step("Filter the process list for worker", "pipeline", "ps aux | grep worker"),
        ],
        ["ps aux shows a detailed process list.", "Pipe ps aux into grep worker."],
        ["processes", "troubleshooting"],
    ),
    mission(
        "container-recon",
        "Container reconnaissance",
        "Docker",
        "Beginner",
        150,
        8,
        "Explore a simulated container host. Inventory running containers, available images, and application logs.",
        [
            step("List running containers", "contains", "docker ps"),
            step("List local images", "contains", "docker images"),
            step("Read the web container logs", "contains", "docker logs web"),
        ],
        [
            "Use docker ps and docker images to inspect the host.",
            "docker logs web retrieves the application log fixture.",
        ],
        ["containers", "logs"],
    ),
    mission(
        "container-inspect",
        "Under the container hood",
        "Docker",
        "Intermediate",
        250,
        10,
        "A web container keeps restarting. Use the practice snapshots to inspect its state and identify the failing dependency.",
        [
            step("Include stopped containers in the inventory", "contains", "docker ps -a"),
            step("Inspect the web container", "contains", "docker inspect web"),
            step("Find ERROR entries in its logs", "pipeline", "docker logs web | grep ERROR"),
        ],
        [
            "docker ps -a includes stopped containers.",
            "Inspect with docker inspect web; pipe docker logs web into grep ERROR.",
        ],
        ["debugging", "containers"],
    ),
    mission(
        "pod-patrol",
        "A pod out of place",
        "Kubernetes",
        "Beginner",
        200,
        10,
        "Triage a simulated Kubernetes workload. Find the unhealthy pod and inspect its events and logs.",
        [
            step("List pods", "contains", "kubectl get pods"),
            step("Describe api-7d9", "contains", "kubectl describe pod api-7d9"),
            step("Read api-7d9 logs", "contains", "kubectl logs api-7d9"),
        ],
        ["Start with kubectl get pods.", "Use kubectl describe pod api-7d9 and kubectl logs api-7d9."],
        ["pods", "incident"],
    ),
    mission(
        "cluster-map",
        "Map the cluster",
        "Kubernetes",
        "Intermediate",
        250,
        10,
        "Understand the topology of a practice cluster by inspecting nodes, services, and deployments.",
        [
            step("Inspect nodes", "contains", "kubectl get nodes"),
            step("Inspect services", "contains", "kubectl get services"),
            step("Inspect deployments", "contains", "kubectl get deployments"),
        ],
        [
            "kubectl get accepts the kind of resource you want to inspect.",
            "Try nodes, services, and deployments with kubectl get.",
        ],
        ["networking", "workloads"],
    ),
    mission(
        "git-recon",
        "Know what you ship",
        "Git",
        "Beginner",
        150,
        6,
        "Check the practice repository before a release. Inspect its state, recent commits, and current branch.",
        [
            step("Check the working tree", "contains", "git status"),
            step("Read the concise commit log", "contains", "git log --oneline"),
            step("Find the current branch", "contains", "git branch"),
        ],
        ["git status summarizes your working tree.", "Use git log --oneline and git branch."],
        ["version-control", "release"],
    ),
    mission(
        "secret-hunt",
        "Secrets do not belong here",
        "Security",
        "Intermediate",
        250,
        10,
        "Find the demo credential in a configuration file, then secure the file. All values in this lab are fictional.",
        [
            step("Inspect /workspace/demo.env", "contains", "cat demo.env"),
            step("Find DEMO_TOKEN in the file", "grep", "DEMO_TOKEN"),
            step("Restrict demo.env to its owner", "mode", ["/workspace/demo.env", "600"]),
        ],
        [
            "Read demo.env, then search it using grep DEMO_TOKEN demo.env.",
            "Use chmod 600 demo.env. Real credentials belong in a secrets manager.",
        ],
        ["secrets", "hardening"],
    ),
    mission(
        "health-triage",
        "The first five minutes",
        "Linux",
        "Advanced",
        300,
        12,
        "Build an initial picture of a failing host: kernel, storage, processes, and application errors.",
        [
            step("Inspect kernel information", "contains", "uname -a"),
            step("Check disk capacity", "contains", "df -h"),
            step("Inspect processes", "contains", "ps aux"),
            step("Find application ERROR entries", "grep", "ERROR"),
        ],
        ["Start with uname -a, df -h, and ps aux.", "Filter /var/log/app.log with grep ERROR."],
        ["incident", "diagnostics"],
    ),
    mission(
        "delivery-preflight",
        "Ready for the green light",
        "DevOps",
        "Advanced",
        350,
        15,
        "Run a complete release preflight across a simulated Git repository, container host, and Kubernetes cluster.",
        [
            step("Check repository status", "contains", "git status"),
            step("Inspect container images", "contains", "docker images"),
            step("Check Kubernetes deployments", "contains", "kubectl get deployments"),
            step(
                "Write release-ready to /workspace/release.txt",
                "file_equals",
                ["/workspace/release.txt", "release-ready\n"],
            ),
        ],
        [
            "Check git status, docker images, and kubectl get deployments.",
            "Record the preflight using echo release-ready > release.txt.",
        ],
        ["release", "ci-cd"],
    ),
]
BY_ID = {m["id"]: m for m in MISSIONS}


def public_mission(m):
    return {
        **{k: v for k, v in m.items() if k not in ("objectives", "hints")},
        "objectives": [x["label"] for x in m["objectives"]],
        "hint_count": len(m["hints"]),
    }


def validate(m, state, command, exit_code, previous):
    import shlex

    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = []
    normalized = " ".join(tokens)
    passed = list(previous)
    for i, obj in enumerate(m["objectives"]):
        rule, value = obj["rule"], obj["value"]
        ok = False
        if exit_code == 0:
            if rule == "command":
                ok = bool(tokens) and tokens[0] == value
            elif rule in ("contains", "pipeline"):
                ok = normalized == value
            elif rule == "grep":
                ok = bool(tokens) and tokens[0] == "grep" and value in tokens and len(tokens) >= 3
            elif rule == "directory":
                ok = value in state["dirs"]
            elif rule == "file":
                ok = value in state["files"]
            elif rule == "file_equals":
                ok = state["files"].get(value[0]) == value[1]
            elif rule == "mode":
                ok = state["modes"].get(value[0]) == value[1]
        passed[i] = passed[i] or ok
    return passed
