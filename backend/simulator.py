"""Bounded, deterministic training shell. NEVER executes a host command."""

import datetime
import posixpath
import shlex

# This is a path in an in-memory dictionary, never a host filesystem access.
VIRTUAL_TMP = "/tmp"  # nosec B108

LOG = (
    "2026-09-27T09:00:00 INFO api started on :8080\n"
    "2026-09-27T09:00:02 INFO healthcheck passed\n"
    "2026-09-27T09:01:14 ERROR database connection refused\n"
    "2026-09-27T09:01:15 WARN retrying connection (1/3)\n"
    "2026-09-27T09:01:18 ERROR database connection refused\n"
    "2026-09-27T09:01:21 INFO connection recovered\n"
)
PROCESSES = (
    "USER       PID %CPU %MEM COMMAND\n"
    "root         1  0.0  0.1 /sbin/init\n"
    "arena       42  1.2  2.0 nginx: worker\n"
    "arena       81 86.4  8.2 python worker.py\n"
    "arena      102  0.0  0.2 bash\n"
)
FIXTURES = {
    "docker ps": "CONTAINER ID   IMAGE            STATUS         NAMES\na9c2ef710d00   arena/web:1.4    Up 10 minutes  web\n",
    "docker ps -a": "CONTAINER ID   IMAGE            STATUS                      NAMES\na9c2ef710d00   arena/web:1.4    Restarting (1) 5 seconds ago web\nb81d66301400   postgres:16      Exited (1) 2 minutes ago    db\n",
    "docker images": "REPOSITORY   TAG   IMAGE ID       SIZE\narena/web    1.4   53b2a887fc01   84MB\npostgres     16    b19083a2d319   430MB\n",
    "docker logs web": LOG,
    "docker inspect web": '{"Name":"web","State":{"Status":"restarting","ExitCode":1},"Config":{"Image":"arena/web:1.4","User":"10001"}}\n',
    "kubectl get pods": "NAME       READY   STATUS             RESTARTS   AGE\napi-7d9    0/1     CrashLoopBackOff   4          12m\nweb-4b2    1/1     Running            0          20m\n",
    "kubectl describe pod api-7d9": "Name: api-7d9\nNamespace: default\nState: Waiting\nReason: CrashLoopBackOff\nLast exit code: 1\nEvents:\n  Warning BackOff Back-off restarting failed container api\n",
    "kubectl logs api-7d9": "INFO starting API\nERROR missing required environment variable: DATABASE_URL\n",
    "kubectl get nodes": "NAME       STATUS   ROLES    VERSION\nworker-1   Ready    <none>   v1.34.0\nworker-2   Ready    <none>   v1.34.0\n",
    "kubectl get services": "NAME   TYPE        CLUSTER-IP    PORT(S)\napi    ClusterIP   10.96.12.10   8080/TCP\nweb    ClusterIP   10.96.12.11   80/TCP\n",
    "kubectl get deployments": "NAME   READY   UP-TO-DATE   AVAILABLE\napi    0/1     1            0\nweb    2/2     2            2\n",
    "git status": "On branch main\nYour branch is up to date with origin/main.\n\nnothing to commit, working tree clean\n",
    "git log --oneline": "f19e412 fix: add application healthcheck\nc391a07 feat: containerize web service\n94eac02 chore: initialize release pipeline\n",
    "git branch": "* main\n  staging\n",
}
HELP = """Available practice commands:
  pwd, whoami, id, ls [-la], cd, cat, head, tail, grep [-in], wc [-l]
  mkdir [-p], touch, cp, mv, rm [-rf], echo, chmod, stat, find
  df -h, du -sh PATH, ps aux, uname -a, date, clear, help
  docker ps [-a], docker images, docker logs web, docker inspect web
  kubectl get pods|nodes|services|deployments
  kubectl describe pod api-7d9, kubectl logs api-7d9
  git status, git log --oneline, git branch
Pipes (|), redirection (> and >>), and && are supported.
This is a learning simulator, not a full Linux shell.
Docker, Kubernetes, Git, and host outputs use fixed practice snapshots.
"""


def initial_state():
    return {
        "cwd": "/workspace",
        "dirs": ["/", "/workspace", "/var", "/var/log", VIRTUAL_TMP],
        "files": {
            "/workspace/README.md": "# ShellArena workspace\nTry help to see supported commands.\n",
            "/workspace/config.env": "APP_ENV=staging\nPORT=8080\n",
            "/workspace/demo.env": "DEMO_TOKEN=fictional-training-value\n",
            "/var/log/app.log": LOG,
        },
        "modes": {},
        "history": [],
    }


class ShellError(Exception):
    pass


def path(state, value):
    return posixpath.normpath(posixpath.join(state["cwd"], value))


def file_data(state, value):
    p = path(state, value)
    if p not in state["files"]:
        raise ShellError(f"{value}: no such file")
    return state["files"][p]


def write_file(state, p, data):
    if p in state["dirs"]:
        raise ShellError(f"{p}: is a directory")
    if posixpath.dirname(p) not in state["dirs"]:
        raise ShellError("parent directory does not exist")
    if len(data.encode()) > 16384:
        raise ShellError("practice file limit: 16 KB")
    if p not in state["files"] and len(state["files"]) >= 64:
        raise ShellError("practice limit: 64 files")
    if sum(len(v.encode()) for k, v in state["files"].items() if k != p) + len(data.encode()) > 131072:
        raise ShellError("practice workspace limit: 128 KB")
    state["files"][p] = data


def single(state, tokens, stdin=None):
    if not tokens:
        return ""
    cmd, *args = tokens
    key = " ".join(tokens)
    if key in FIXTURES:
        return FIXTURES[key]
    if cmd == "help":
        return HELP
    if cmd == "clear":
        return ""
    if cmd == "pwd":
        return state["cwd"] + "\n"
    if cmd == "whoami":
        return "arena\n"
    if cmd == "id":
        return "uid=10001(arena) gid=10001(arena) groups=10001(arena)\n"
    if cmd == "date":
        return datetime.datetime.now(datetime.timezone.utc).isoformat() + "\n"
    if cmd == "uname":
        return "Linux shellarena 6.8.0-practice x86_64 GNU/Linux (simulated)\n"
    if cmd == "echo":
        return " ".join(args) + "\n"
    if cmd == "cd":
        p = path(state, args[0] if args else "/workspace")
        if p not in state["dirs"]:
            raise ShellError("directory not found")
        state["cwd"] = p
        return ""
    if cmd in ("ls", "find"):
        target = next((x for x in args if not x.startswith("-")), ".")
        p = path(state, target)
        if p in state["files"]:
            return posixpath.basename(p) + "\n"
        if p not in state["dirs"]:
            raise ShellError("directory not found")
        all_paths = set(state["dirs"] + list(state["files"]))
        if cmd == "find":
            return "\n".join(sorted(x for x in all_paths if x == p or x.startswith(p.rstrip("/") + "/"))) + "\n"
        names = sorted(
            posixpath.basename(x) + ("/" if x in state["dirs"] else "")
            for x in all_paths
            if x != p and posixpath.dirname(x) == p
        )
        if any(x in ("-l", "-la", "-al") for x in args):
            return (
                "\n".join(("drwxr-xr-x" if x.endswith("/") else "-rw-r--r--") + "  arena arena  " + x for x in names)
                + "\n"
            )
        return "  ".join(names) + "\n"
    if cmd in ("cat", "head", "tail", "wc"):
        count = 10
        rest = list(args)
        if "-n" in rest:
            i = rest.index("-n")
            if i + 1 >= len(rest) or not rest[i + 1].isdigit():
                raise ShellError("use -n followed by a line count")
            count = min(int(rest[i + 1]), 200)
            del rest[i : i + 2]
        files = [x for x in rest if not x.startswith("-")]
        data = "".join(file_data(state, x) for x in files) if files else stdin
        if data is None:
            raise ShellError("provide a file or piped input")
        lines = data.splitlines(True)
        if cmd == "cat":
            return data
        if cmd == "head":
            return "".join(lines[:count])
        if cmd == "tail":
            return "".join(lines[-count:]) if count else ""
        return str(len(lines)) + "\n" if "-l" in args else f"{len(lines)} {len(data.split())} {len(data.encode())}\n"
    if cmd == "grep":
        rest = [x for x in args if not x.startswith("-")]
        if not rest:
            raise ShellError("usage: grep PATTERN FILE")
        pattern, *files = rest
        data = "".join(file_data(state, x) for x in files) if files else stdin
        if data is None:
            raise ShellError("provide a file or piped input")
        ignore = any("i" in x for x in args if x.startswith("-"))
        numbered = any("n" in x for x in args if x.startswith("-"))
        matches = "".join(
            (f"{i}:" if numbered else "") + line + "\n"
            for i, line in enumerate(data.splitlines(), 1)
            if (pattern.lower() in line.lower() if ignore else pattern in line)
        )
        if not matches:
            raise ShellError("grep: no matching lines")
        return matches
    if cmd == "mkdir":
        targets = [x for x in args if not x.startswith("-")]
        if not targets:
            raise ShellError("usage: mkdir [-p] DIRECTORY")
        for target in targets:
            p = path(state, target)
            if p in state["files"]:
                raise ShellError("file already exists")
            if p in state["dirs"] and "-p" not in args:
                raise ShellError("directory already exists")
            parents = []
            cursor = p
            while cursor not in state["dirs"]:
                parents.append(cursor)
                cursor = posixpath.dirname(cursor)
            if len(parents) > 1 and "-p" not in args:
                raise ShellError("parent directory does not exist")
            if len(state["dirs"]) + len(parents) > 64:
                raise ShellError("practice limit: 64 directories")
            state["dirs"].extend(reversed(parents))
        return ""
    if cmd == "touch":
        if not args:
            raise ShellError("usage: touch FILE")
        for value in args:
            p = path(state, value)
            write_file(state, p, state["files"].get(p, ""))
        return ""
    if cmd in ("cp", "mv"):
        if len(args) != 2:
            raise ShellError(f"usage: {cmd} SOURCE DESTINATION")
        source, target = [path(state, x) for x in args]
        if target in state["dirs"]:
            target = posixpath.join(target, posixpath.basename(source))
        data = file_data(state, args[0])
        write_file(state, target, data)
        if cmd == "mv" and source != target:
            del state["files"][source]
        return ""
    if cmd == "rm":
        for value in [x for x in args if not x.startswith("-")]:
            p = path(state, value)
            if p in ("/", "/workspace", "/var", VIRTUAL_TMP):
                raise ShellError("practice root directories are protected")
            if p in state["dirs"] and not any("r" in x for x in args if x.startswith("-")):
                raise ShellError("is a directory; use -r")
            state["files"] = {k: v for k, v in state["files"].items() if not (k == p or k.startswith(p + "/"))}
            state["dirs"] = [x for x in state["dirs"] if not (x == p or x.startswith(p + "/"))]
        if state["cwd"] not in state["dirs"]:
            state["cwd"] = "/workspace"
        return ""
    if cmd == "chmod":
        if len(args) != 2 or len(args[0]) != 3 or any(c not in "01234567" for c in args[0]):
            raise ShellError("usage: chmod MODE FILE (example: chmod 600 config.env)")
        file_data(state, args[1])
        state["modes"][path(state, args[1])] = args[0]
        return ""
    if cmd == "stat":
        if len(args) != 1:
            raise ShellError("usage: stat FILE")
        data = file_data(state, args[0])
        p = path(state, args[0])
        return f"File: {p}\nSize: {len(data.encode())} bytes\nAccess: ({state['modes'].get(p, '644')}) Uid: (10001/arena)\n"
    if key == "df -h":
        return "Filesystem      Size  Used Avail Use% Mounted on\n/dev/practice    20G   14G  6.0G  70% /\n"
    if cmd == "du" and len(args) == 2 and args[0] == "-sh":
        p = path(state, args[1])
        if p not in state["dirs"] and p not in state["files"]:
            raise ShellError("path does not exist")
        size = sum(len(v.encode()) for k, v in state["files"].items() if k == p or k.startswith(p + "/"))
        return f"{max(1, (size + 1023) // 1024)}K\t{args[1]}\n"
    if key == "ps aux":
        return PROCESSES
    raise ShellError(f"{cmd}: unsupported practice command. Type help for available commands.")


def execute(state, command):
    try:
        if any(x in command for x in ("`", "$(", "\x00", "\n", "\r")):
            raise ShellError("command substitution and multiline scripts are not supported")
        lexer = shlex.shlex(command, posix=True, punctuation_chars="|>&;")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
        if any(x in tokens for x in (";", "&", "||", "<<", "<")):
            raise ShellError("use one command, a pipeline, or &&")
        groups, current = [], []
        for token in tokens:
            if token == "&&":
                if not current:
                    raise ShellError("missing command before &&")
                groups.append(current)
                current = []
            else:
                current.append(token)
        if not current:
            raise ShellError("missing command")
        groups.append(current)
        result = ""
        for group in groups:
            redirect, append = None, False
            for symbol in (">>", ">"):
                if symbol in group:
                    i = group.index(symbol)
                    if i != len(group) - 2:
                        raise ShellError("redirection requires one destination")
                    redirect, append = path(state, group[-1]), symbol == ">>"
                    group = group[:i]
                    break
            pipeline, stage = [], []
            for token in group:
                if token == "|":
                    if not stage:
                        raise ShellError("empty pipeline stage")
                    pipeline.append(stage)
                    stage = []
                else:
                    stage.append(token)
            if not stage:
                raise ShellError("missing command")
            pipeline.append(stage)
            output = None
            for stage in pipeline:
                output = single(state, stage, output)
                if len(output.encode()) > 32768:
                    raise ShellError("practice output limit: 32 KB")
            if redirect:
                write_file(state, redirect, (state["files"].get(redirect, "") if append else "") + output)
            else:
                result += output
        return result[:32768], 0
    except (ShellError, ValueError) as exc:
        return f"{exc}\n", 1
