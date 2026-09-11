import argparse
import sys
import subprocess
import os
import shutil


RESET = "\033[0m"
CYAN = "\033[96m"
PURPLE = "\033[95m"
MUTED = "\033[90m"
BOLD = "\033[1m"

from metrix_lang.interpreter import EasyError, run

try:
    from metrix_lang.editor import edit_file
except ImportError:
    edit_file = None

try:
    from metrix_lang.installer import install as installer_install
except ImportError:
    installer_install = None


def read_source(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def home_screen():
    """A useful landing screen for `metrix` and the short `m` command."""
    print(f"{BOLD}{PURPLE}METRIX{RESET}  {MUTED}terminal language studio{RESET}")
    print(f"{MUTED}{'─' * 62}{RESET}")
    print(f"{BOLD}{CYAN}Start building{RESET}")
    print("  m edit app.met          Open METRIX Studio")
    print("  m run app.met           Run a terminal app")
    print("  m repl                  Experiment interactively")
    print()
    print(f"{BOLD}{CYAN}Create your first screen{RESET}")
    print('  echo \'say "Hello, METRIX" [box:rounded] :cyan:\' > app.met')
    print("  m edit app.met")
    print()
    print(f"{BOLD}{CYAN}Studio controls{RESET}")
    print("  Type to open suggestions  ·  ↑/↓ select  ·  Tab accept")
    print("  F5 preview  ·  F6 tidy  ·  Ctrl+S save  ·  Ctrl+Q quit")
    print()
    print(f"{MUTED}Run m --help to see every command.  Update with: metrix update metrix{RESET}")


def run_file(args):
    try:
        for line in run(read_source(args.file)):
            print(line)
    except OSError as error:
        print(f"file error: {error}", file=sys.stderr)
        return 1
    except EasyError as error:
        print(f"metrix error: {error}", file=sys.stderr)
        return 1

    return 0


def check_file(args):
    try:
        run(read_source(args.file))
    except OSError as error:
        print(f"file error: {error}", file=sys.stderr)
        return 1
    except EasyError as error:
        print(f"metrix error: {error}", file=sys.stderr)
        return 1

    print("ok")
    return 0


def edit_file_command(args):
    if edit_file is None:
        print("metrix error: prompt_toolkit is required for the editor. Install it with: pip install prompt_toolkit pygments", file=sys.stderr)
        return 1
    edit_file(args.file)
    return 0


def install_command(args):
    if installer_install is None:
        print("metrix error: installer is unavailable.", file=sys.stderr)
        return 1
    try:
        installer_install(args.target)
    except Exception as error:
        print(f"metrix error: {error}", file=sys.stderr)
        return 1
    return 0


def update_command(args):
    if getattr(args, "target", None) != "metrix":
        print("metrix error: use 'metrix update metrix' to update METRIX", file=sys.stderr)
        return 1
    metrix_bin = shutil.which("metrix")
    if not metrix_bin:
        print("metrix error: could not find metrix binary in PATH", file=sys.stderr)
        return 1

    install_script = os.path.join(os.path.dirname(__file__), "..", "install", "install.sh")
    install_script = os.path.abspath(install_script)

    if not os.path.exists(install_script):
        print(f"metrix error: installer script not found at {install_script}", file=sys.stderr)
        return 1

    print("Updating METRIX...")
    result = subprocess.run(["bash", install_script], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"metrix error: update failed\n{result.stderr}", file=sys.stderr)
        return 1

    print(result.stdout.strip() or "METRIX updated.")
    return 0


def repl(_args):
    print("METRIX REPL. Type exit to quit.")
    lines = []

    while True:
        try:
            line = input("metrix> ")
        except EOFError:
            print()
            break

        if line.strip() in ("exit", "quit"):
            break

        lines.append(line)
        try:
            for output_line in run("\n".join(lines)):
                print(output_line)
        except EasyError as error:
            print(f"metrix error: {error}", file=sys.stderr)
            lines.pop()

    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="metrix", description="Run METRIX language programs.")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="run a METRIX file")
    run_parser.add_argument("file")
    run_parser.set_defaults(func=run_file)

    check_parser = subparsers.add_parser("check", help="check a METRIX file for errors")
    check_parser.add_argument("file")
    check_parser.set_defaults(func=check_file)

    edit_parser = subparsers.add_parser("edit", help="edit a METRIX file")
    edit_parser.add_argument("file")
    edit_parser.set_defaults(func=edit_file_command)

    install_parser = subparsers.add_parser("install", help="install a package or repo")
    install_parser.add_argument("target", help="package name, npm package, GitHub repo, or URL")
    install_parser.set_defaults(func=install_command)

    update_parser = subparsers.add_parser("update", help="update METRIX itself")
    update_parser.add_argument("target", choices=["metrix"], help="what to update")
    update_parser.set_defaults(func=update_command)

    repl_parser = subparsers.add_parser("repl", help="start an interactive METRIX session")
    repl_parser.set_defaults(func=repl)

    return parser


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        home_screen()
        return 0
    if len(argv) == 1 and argv[0].endswith((".met", ".metrix")):
        return run_file(argparse.Namespace(file=argv[0]))

    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 2

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
