import pathlib
import subprocess
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from easy_lang.interpreter import run


def main():
    result = subprocess.run(
        ["python3", "-m", "easy_lang.cli", "run", "examples/hello.easy"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "hello from easy\n15\n"

    direct_result = subprocess.run(
        ["python3", "-m", "easy_lang.cli", "examples/hello.easy"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert direct_result.returncode == 0, direct_result.stderr
    assert direct_result.stdout == "hello from easy\n15\n"

    check_result = subprocess.run(
        ["python3", "-m", "easy_lang.cli", "check", "examples/hello.easy"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert check_result.returncode == 0, check_result.stderr
    assert check_result.stdout == "ok\n"

    control_flow = '''\
func label(name):
    return upper(name)
set total 0
for number in range(1, 4):
    add total number
if total == 6:
    say label("easy")
else:
    say "wrong"
while total < 8:
    add total 1
say total
'''
    assert run(control_flow) == ["EASY", "8"]

    workspace = '''\
set data {"name": "easy", "rank": 1}
say title(get(data, "name"))
say count(keys(data))
row "left\\nmore" | "right" [left:20]
'''
    workspace_output = run(workspace)
    assert workspace_output[:2] == ["Easy", "2"]
    assert "more" in workspace_output[4]
    print("smoke test passed")


if __name__ == "__main__":
    main()
