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
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
}
RESET = "\033[0m"

STYLES = {
    "bold": "\033[1m",
    "dim": "\033[2m",
    "italic": "\033[3m",
    "underline": "\033[4m",
    "blink": "\033[5m",
    "reverse": "\033[7m",
    "strikethrough": "\033[9m",
}

BORDERS = {
    "single": ("\u250c", "\u2500", "\u2510", "\u2502", "\u2514", "\u2500", "\u2518"),
    "double": ("\u2554", "\u2550", "\u2557", "\u2551", "\u255a", "\u2550", "\u255d"),
    "rounded": ("\u256d", "\u2500", "\u256e", "\u2502", "\u2570", "\u2500", "\u256f"),
    "bold": ("\u250f", "\u2501", "\u2513", "\u2503", "\u2517", "\u2501", "\u251b"),
    "dotted": ("\u250c", "\u00b7", "\u2510", "\u2502", "\u2514", "\u00b7", "\u2518"),
}


def strip_ansi(text):
    return re.sub(r"\033\[[0-9;]*m", "", text)


def visible_width(text):
    return len(strip_ansi(text))


def ansi_len(text):
    return len(strip_ansi(text))


def apply_styles(text, styles_list):
    prefix = ""
    suffix = RESET
    for style in styles_list:
        if style in STYLES:
            prefix += STYLES[style]
    return f"{prefix}{text}{suffix}"


def apply_color(text, color_name):
    if color_name in COLORS:
        return f"{COLORS[color_name]}{text}{RESET}"
    return text


def apply_bg(text, color_name):
    bg_map = {
        "green": "\033[42m",
        "red": "\033[41m",
        "blue": "\033[44m",
        "yellow": "\033[43m",
        "cyan": "\033[46m",
        "magenta": "\033[45m",
        "white": "\033[47m",
        "black": "\033[40m",
    }
    if color_name in bg_map:
        return f"{bg_map[color_name]}{text}{RESET}"
    return text


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


def parse_tags(raw):
    result = {
        "box": False,
        "box_style": "single",
        "chat": None,
        "sidebar": False,
        "header": False,
        "footer": False,
        "alert": False,
        "list": False,
        "table": False,
        "progress": None,
        "spinner": False,
        "input": None,
        "hr": False,
        "align": "left",
        "padding": 1,
        "width": None,
        "bg": None,
        "styles": [],
    }

    box_match = re.search(r"\[box(?::(\w+))?\]", raw, re.IGNORECASE)
    if box_match:
        result["box"] = True
        result["box_style"] = (box_match.group(1) or "single").lower()

    chat_match = re.search(r"\[chat:(left|right)\]", raw, re.IGNORECASE)
    if chat_match:
        result["chat"] = chat_match.group(1).lower()

    if re.search(r"\[sidebar\]", raw, re.IGNORECASE):
        result["sidebar"] = True
    if re.search(r"\[header\]", raw, re.IGNORECASE):
        result["header"] = True
    if re.search(r"\[footer\]", raw, re.IGNORECASE):
        result["footer"] = True
    if re.search(r"\[alert\]", raw, re.IGNORECASE):
        result["alert"] = True
    if re.search(r"\[list\]", raw, re.IGNORECASE):
        result["list"] = True
    if re.search(r"\[table\]", raw, re.IGNORECASE):
        result["table"] = True
    if re.search(r"\[hr\]", raw, re.IGNORECASE):
        result["hr"] = True
    if re.search(r"\[spinner\]", raw, re.IGNORECASE):
        result["spinner"] = True

    progress_match = re.search(r"\[progress:(\d+)\]", raw, re.IGNORECASE)
    if progress_match:
        result["progress"] = max(0, min(100, int(progress_match.group(1))))

    input_match = re.search(r"\[input:([^\]]+)\]", raw, re.IGNORECASE)
    if input_match:
        result["input"] = input_match.group(1)

    align_match = re.search(r"\[align:(left|center|right)\]", raw, re.IGNORECASE)
    if align_match:
        result["align"] = align_match.group(1).lower()

    padding_match = re.search(r"\[padding:(\d+)\]", raw, re.IGNORECASE)
    if padding_match:
        result["padding"] = max(0, int(padding_match.group(1)))

    width_match = re.search(r"\[width:(\d+)\]", raw, re.IGNORECASE)
    if width_match:
        result["width"] = max(1, int(width_match.group(1)))

    bg_match = re.search(r"\[bg:(\w+)\]", raw, re.IGNORECASE)
    if bg_match:
        result["bg"] = bg_match.group(1).lower()

    for style_name in ["bold", "dim", "italic", "underline", "blink", "reverse", "strikethrough"]:
        if re.search(rf"\[{style_name}\]", raw, re.IGNORECASE):
            result["styles"].append(style_name)

    return result


def strip_tags(raw):
    return re.sub(
        r"\[(?:"
        r"box(?::\w+)?|"
        r"chat:(?:left|right)|"
        r"sidebar|"
        r"header|"
        r"footer|"
        r"alert|"
        r"list|"
        r"table|"
        r"progress:\d+|"
        r"spinner|"
        r"input:[^\]]+|"
        r"hr|"
        r"align:(?:left|center|right)|"
        r"padding:\d+|"
        r"width:\d+|"
        r"bg:\w+|"
        r"bold|"
        r"dim|"
        r"italic|"
        r"underline|"
        r"blink|"
        r"reverse|"
        r"strikethrough"
        r")\]",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip()


def parse_color(raw):
    color_code = None
    color_match = re.search(r":(\w+):\s*$", raw)
    if color_match:
        color_name = color_match.group(1)
        if color_name in COLORS:
            color_code = COLORS[color_name]
        raw = raw[: color_match.start()].strip()
    return color_code, raw


def parse_say_args(raw, memory):
    raw = raw.strip()
    color_code, raw = parse_color(raw)
    component = parse_tags(raw)
    raw = strip_tags(raw)
    value = parse_value(raw, memory)
    return str(value), component, color_code


def format_border(text, style_name="single", width=None):
    visible = strip_ansi(text)
    width = width or len(visible)
    tl, h, tr, v, bl, h2, br = BORDERS.get(style_name, BORDERS["single"])
    top = f"{tl}{h * (width + 2)}{tr}"
    middle = f"{v} {text} {v}"
    bottom = f"{bl}{h2 * (width + 2)}{br}"
    return [top, middle, bottom]


def format_chat(text, side):
    if side == "left":
        return [f"\u25b6 {text}"]
    return [f"{text} \u25c0"]


def format_sidebar(text, padding=1, width=None):
    visible = strip_ansi(text)
    width = width or max(len(visible), 20)
    inner = " " * padding + text + " " * padding
    top = f"\u252c{'─' * (width + 2)}\u252c"
    middle = f"\u2502{inner}\u2502"
    bottom = f"\u2514{'─' * (width + 2)}\u2518"
    return [top, middle, bottom]


def format_header(text, width=None):
    visible = strip_ansi(text)
    width = width or len(visible)
    top = f"\u2550\u2550{'\u2550' * width}\u2550\u2550"
    middle = f"\u2551 {text} \u2551"
    bottom = f"\u2550\u2550{'\u2550' * width}\u2550\u2550"
    return [top, middle, bottom]


def format_footer(text, width=None):
    visible = strip_ansi(text)
    width = width or len(visible)
    top = f"\u2501\u2501{'\u2501' * width}\u2501\u2501"
    middle = f"\u2503 {text} \u2503"
    bottom = f"\u2501\u2501{'\u2501' * width}\u2501\u2501"
    return [top, middle, bottom]


def format_alert(text):
    return [f"\u26a0 {text}"]


def format_list(text):
    return [f"  \u2022 {text}"]


def format_hr(width=40):
    return ["\u2500" * width]


def format_progress(percent, width=30):
    filled = int(width * percent / 100)
    bar = "\u2588" * filled + "\u2591" * (width - filled)
    return [f"[{bar}] {percent}%"]


def format_spinner(frame):
    frames = ["\u25d0", "\u25d3", "\u25d1", "\u25d2"]
    return [frames[frame % len(frames)]]


def align_text(text, alignment, width=None):
    visible = strip_ansi(text)
    width = width or len(visible)
    if alignment == "center":
        pad = max(0, (width - len(visible)) // 2)
        return " " * pad + text
    if alignment == "right":
        pad = max(0, width - len(visible))
        return " " * pad + text
    return text


def format_output(text, component, color_code):
    if color_code:
        text = f"{color_code}{text}{RESET}"

    if component["bg"]:
        text = apply_bg(text, component["bg"])

    if component["styles"]:
        text = apply_styles(text, component["styles"])

    text = align_text(text, component["align"], component["width"])

    if component["alert"]:
        return format_alert(text)

    if component["chat"]:
        return format_chat(text, component["chat"])

    if component["sidebar"]:
        return format_sidebar(text, component["padding"], component["width"])

    if component["header"]:
        return format_header(text, component["width"])

    if component["footer"]:
        return format_footer(text, component["width"])

    if component["list"]:
        return format_list(text)

    if component["hr"]:
        return format_hr(component["width"] or 40)

    if component["progress"] is not None:
        return format_progress(component["progress"], component["width"] or 30)

    if component["spinner"]:
        return format_spinner(0)

    if component["box"]:
        return format_border(text, component["box_style"], component["width"])

    return [text]


def run(source):
    memory = {}
    output = []
    spinner_frame = 0

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
                if component["spinner"]:
                    spinner_frame += 1
                    value = format_spinner(spinner_frame - 1)[0]
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
