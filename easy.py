#!/usr/bin/env python3
import sys


class EasyError(Exception):
    pass


def parse_value(raw, memory):
    raw = raw.strip()

    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        return raw[1:-1]

    if raw in memory:
        return memory[raw]

    try:
        return int(raw)
    except ValueError:
        raise EasyError(f"unknown value: {raw}")


def run(source):
    memory = {}
    output = []

    for line_number, original_line in enumerate(source.splitlines(), start=1):
        line = original_line.strip()

        if not line or line.startswith("#"):
            continue

        parts = line.split(maxsplit=2)
        command = parts[0]

        try:
            if command == "say":
                if len(parts) < 2:
                    raise EasyError("say needs one value")
                output.append(str(parse_value(original_line.strip()[4:], memory)))

            elif command == "set":
                if len(parts) != 3:
                    raise EasyError("set needs a name and value")
                memory[parts[1]] = parse_value(parts[2], memory)

            elif command in ("add", "sub"):
                if len(parts) != 3:
                    raise EasyError(f"{command} needs a name and value")
                name = parts[1]
                current = memory.get(name, 0)
                change = parse_value(parts[2], memory)
                if not isinstance(current, int) or not isinstance(change, int):
                    raise EasyError(f"{command} only works with numbers")
                memory[name] = current + change if command == "add" else current - change

            else:
                raise EasyError(f"unknown command: {command}")

        except EasyError as error:
            raise EasyError(f"line {line_number}: {error}")

    return output


def main():
    if len(sys.argv) != 2:
        print("usage: python3 easy.py path/to/file.easy", file=sys.stderr)
        return 2

    try:
        with open(sys.argv[1], "r", encoding="utf-8") as file:
            source = file.read()
        for line in run(source):
            print(line)
    except OSError as error:
        print(f"file error: {error}", file=sys.stderr)
        return 1
    except EasyError as error:
        print(f"easy error: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
