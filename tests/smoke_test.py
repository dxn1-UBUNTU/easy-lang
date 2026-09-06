import pathlib
import subprocess


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


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
    print("smoke test passed")


if __name__ == "__main__":
    main()
