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


def parse_component(raw):
    raw = raw.strip()

    box = False
    chat = None
    sidebar = False
    header = False
    footer = False
    alert = False

    for part in raw.split():
        lower = part.lower()
        if lower == "[box]":
            box = True
        elif lower.startswith("[chat:") and lower.endswith("]"):
            chat = lower[6:-1]
        elif lower == "[sidebar]":
            sidebar = True
        elif lower == "[header]":
            header = True
        elif lower == "[footer]":
            footer = True
        elif lower == "[alert]":
            alert = True

    return {
        "box": box,
        "chat": chat,
        "sidebar": sidebar,
        "header": header,
        "footer": footer,
        "alert": alert,
    }


def parse_color(raw):
    color_code = None
    color_match = re.search(r":(\w+):\s*$", raw)
    if color_match:
        color_name = color_match.group(1)
        if color_name in COLORS:
            color_code = COLORS[color_name]
        raw = raw[: color_match.start()].strip()
    return color_code, raw


def strip_component_tags(raw):
    tags = [
        "[box]",
        "[chat:left]",
        "[chat:right]",
        "[sidebar]",
        "[header]",
        "[footer]",
        "[alert]",
    ]
    result = raw
    for tag in tags:
        result = result.replace(tag, "")
    return result.strip()


def parse_say_args(raw, memory):
    raw = raw.strip()
    color_code, raw = parse_color(raw)
    component = parse_component(raw)
    raw = strip_component_tags(raw)
    value = parse_value(raw, memory)
    return str(value), component, color_code


def format_box(text, width=None):
    visible = strip_ansi(text)
    width = width or len(visible)
    top = f"\u250c{'─' * (width + 2)}\u2510"
    middle = f"\u2502 {text} \u2502"
    bottom = f"\u2514{'─' * (width + 2)}\u2518"
    return [top, middle, bottom]


def format_chat(text, side):
    visible = strip_ansi(text)
    width = len(visible)
    if side == "left":
        bubble = f"\u25b6 {text}"
        prefix = "\u25c0 "
    else:
        bubble = f"{text} \u25c0"
        prefix = " \u25b6"
    return [bubble]


def format_sidebar(text):
    visible = strip_ansi(text)
    width = len(visible)
    top = f"\u252c\u2500\u2500{'\u2500' * width}\u2500\u252c"
    middle = f"\u2502 {text} \u2502"
    bottom = f"\u2514\u2500\u2500{'\u2500' * width}\u2500\u2518"
    return [top, middle, bottom]


def format_header(text):
    visible = strip_ansi(text)
    width = len(visible)
    top = f"\u2550\u2550{'\u2550' * width}\u2550\u2550"
    middle = f"\u2551 {text} \u2551"
    bottom = f"\u2550\u2550{'\u2550' * width}\u2550\u2550"
    return [top, middle, bottom]


def format_footer(text):
    visible = strip_ansi(text)
    width = len(visible)
    top = f"\u2501\u2501{'\u2501' * width}\u2501\u2501"
    middle = f"\u2503 {text} \u2503"
    bottom = f"\u2501\u2501{'\u2501' * width}\u2501\u2501"
    return [top, middle, bottom]


def format_alert(text):
    visible = strip_ansi(text)
    width = len(visible)
    top = f"\u26a0 {text}"
    return [top]


def format_output(text, component, color_code):
    if color_code:
        text = f"{color_code}{text}{RESET}"

    if component["alert"]:
        return format_alert(text)

    if component["chat"]:
        return format_chat(text, component["chat"])

    if component["sidebar"]:
        return format_sidebar(text)

    if component["header"]:
        return format_header(text)

    if component["footer"]:
        return format_footer(text)

    if component["box"]:
        return format_box(text)

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
                value, component, color_code = parse_say_args(line[4:], memory)
                output.extend(format_output(value, component, color_code))

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
