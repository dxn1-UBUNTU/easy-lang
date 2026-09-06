import pathlib
import subprocess


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    result = subprocess.run(
        ["python3", "easy.py", "examples/hello.easy"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "hello from easy\n15\n"
    print("smoke test passed")


if __name__ == "__main__":
    main()
