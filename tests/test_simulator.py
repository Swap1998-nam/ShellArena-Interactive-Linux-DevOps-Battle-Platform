from pathlib import Path
import pytest
from backend.simulator import execute, initial_state


def test_stateful_shell_files_pipes_and_permissions():
    state = initial_state()
    for command in [
        "mkdir -p releases/v1",
        "cd releases/v1",
        "echo ready > note.txt",
        "echo next >> note.txt",
        "cp note.txt copy.txt",
        "mv copy.txt moved.txt",
        "chmod 600 note.txt",
    ]:
        assert execute(state, command)[1] == 0
    assert execute(state, "pwd")[0] == "/workspace/releases/v1\n"
    assert execute(state, "cat note.txt")[0] == "ready\nnext\n"
    assert execute(state, "cat note.txt | grep ready | wc -l")[0] == "1\n"
    assert "600" in execute(state, "stat note.txt")[0]
    assert execute(state, "head -n 1 note.txt")[0] == "ready\n"
    assert execute(state, "tail -n 1 note.txt")[0] == "next\n"
    assert execute(state, "tail -n 0 note.txt")[0] == ""
    assert execute(state, "rm moved.txt")[1] == 0
    assert execute(state, "cat moved.txt")[1] == 1
    assert execute(state, "cd /workspace && ls")[1] == 0


@pytest.mark.parametrize(
    "command",
    [
        "cat /etc/passwd",
        "cat /proc/self/environ",
        "curl https://example.com",
        "python -c evil",
        "echo $(whoami)",
        "echo `whoami`",
        "pwd; whoami",
        "pwd || whoami",
        "ls &",
        "cat missing",
        "cd missing",
        "chmod 999 config.env",
        "head -n bad /var/log/app.log",
        "grep",
        "touch",
        "mkdir",
        "stat",
        "cp config.env",
        "echo x > missing/file",
        "echo x > /workspace",
        "| ls",
        "ls |",
    ],
)
def test_unsupported_or_invalid_commands_cannot_touch_host(command):
    state = initial_state()
    assert execute(state, command)[1] == 1


def test_host_files_are_not_created(tmp_path):
    marker = tmp_path / "host-marker"
    state = initial_state()
    execute(state, f"touch {marker}")
    assert not marker.exists()
    assert Path("/etc/passwd").exists()  # Host has it, but the simulator does not.
    assert execute(state, "cat /etc/passwd")[1] == 1


def test_workspace_bounds():
    state = initial_state()
    for i in range(70):
        execute(state, f"touch f{i}")
    assert len(state["files"]) == 64
    for i in range(70):
        execute(state, f"mkdir d{i}")
    assert len(state["dirs"]) == 64
    assert execute(state, "rm -rf /workspace")[1] == 1
    execute(state, "echo abc > config.env")
    for _ in range(20):
        execute(state, "cat config.env >> config.env")
    assert len(state["files"]["/workspace/config.env"].encode()) <= 16384
