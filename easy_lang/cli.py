import argparse
import sys

from easy_lang.interpreter import EasyError, run


def read_source(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def run_file(args):
    try:
        for line in run(read_source(args.file)):
            print(line)
    except OSError as error:
        print(f"file error: {error}", file=sys.stderr)
        return 1
    except EasyError as error:
        print(f"easy error: {error}", file=sys.stderr)
        return 1

    return 0


def check_file(args):
    try:
        run(read_source(args.file))
    except OSError as error:
        print(f"file error: {error}", file=sys.stderr)
        return 1
    except EasyError as error:
        print(f"easy error: {error}", file=sys.stderr)
        return 1

    print("ok")
    return 0


def repl(_args):
    print("Easy REPL. Type exit to quit.")
    lines = []

    while True:
        try:
            line = input("easy> ")
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
            print(f"easy error: {error}", file=sys.stderr)
            lines.pop()

    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="easy", description="Run Easy language programs.")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="run an Easy file")
    run_parser.add_argument("file")
    run_parser.set_defaults(func=run_file)

    check_parser = subparsers.add_parser("check", help="check an Easy file for errors")
    check_parser.add_argument("file")
    check_parser.set_defaults(func=check_file)

    repl_parser = subparsers.add_parser("repl", help="start an interactive Easy session")
    repl_parser.set_defaults(func=repl)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 2

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
