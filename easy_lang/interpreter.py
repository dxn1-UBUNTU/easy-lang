import re


class EasyError(Exception):
    pass


COLORS = {
    "green": "\033[32m",
    "red": "\033[31m",
    "blue": "\033[34m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "white": "\033[37m",
    "black": "\033[30m",
}
RESET = "\033[0m"


def strip_ansi(text):
    return re.sub(r"\033\[[0-9;]*m", "", text)


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


def parse_say_args(raw, memory):
    raw = raw.strip()

    color_code = None
    color_match = re.search(r":(\w+):\s*$", raw)
    if color_match:
        color_name = color_match.group(1)
        if color_name in COLORS:
            color_code = COLORS[color_name]
        raw = raw[: color_match.start()].strip()

    has_box = "[box]" in raw
    if has_box:
        raw = raw.replace("[box]", "").strip()

    value = parse_value(raw, memory)
    return str(value), has_box, color_code


def format_output(text, has_box, color_code):
    if color_code:
        text = f"{color_code}{text}{RESET}"

    if has_box:
        visible = strip_ansi(text)
        width = len(visible)
        top = f"\u250c{'─' * (width + 2)}\u2510"
        middle = f"\u2502 {text} \u2502"
        bottom = f"\u2514{'─' * (width + 2)}\u2518"
        return [top, middle, bottom]

    return [text]


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
                value, has_box, color_code = parse_say_args(line[4:], memory)
                output.extend(format_output(value, has_box, color_code))

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
