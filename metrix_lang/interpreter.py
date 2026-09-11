import re
import ast
import json
import os
import urllib.request
import urllib.error
import urllib.parse
import subprocess
import datetime
import random
import math
import textwrap
from pathlib import Path


class EasyError(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


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
    for style in styles_list:
        if style in STYLES:
            prefix += STYLES[style]
    return f"{prefix}{text}{RESET}"


def apply_color(text, color_name):
    color_code = color_to_ansi(color_name)
    if color_code:
        return f"{color_code}{text}{RESET}"
    return text


def apply_bg(text, color_name):
    color_code = color_to_ansi(color_name, background=True)
    if color_code:
        return f"{color_code}{text}{RESET}"
    return text


def color_to_ansi(value, background=False):
    """Turn a named METRIX colour or #RGB/#RRGGBB into a terminal colour."""
    value = str(value or "").lower()
    if value in COLORS and not background:
        return COLORS[value]
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
    if background and value in bg_map:
        return bg_map[value]
    if re.fullmatch(r"#[0-9a-f]{3}|#[0-9a-f]{6}", value):
        digits = value[1:]
        if len(digits) == 3:
            digits = "".join(char * 2 for char in digits)
        red, green, blue = (int(digits[index:index + 2], 16) for index in range(0, 6, 2))
        return f"\033[{48 if background else 38};2;{red};{green};{blue}m"
    return None


def parse_value(raw, memory):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw[1:-1]
    if raw in memory:
        return memory[raw]
    if raw[:1] in ("[", "{"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(raw)
            except (ValueError, SyntaxError):
                pass
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return raw


def evaluate_condition(expression, memory):
    """Evaluate a small boolean expression using program variables only."""
    expression = re.sub(r"\btrue\b", "True", expression, flags=re.IGNORECASE)
    expression = re.sub(r"\bfalse\b", "False", expression, flags=re.IGNORECASE)
    try:
        return bool(eval(expression, {"__builtins__": {}}, dict(memory)))
    except Exception as error:
        raise EasyError(f"invalid condition: {error}")


def iterable_value(expression, memory):
    expression = expression.strip()
    range_match = re.fullmatch(r"range\(([^,]+),\s*([^\)]+)\)", expression)
    if range_match:
        start = int(parse_value(range_match.group(1), memory))
        stop = int(parse_value(range_match.group(2), memory))
        return range(start, stop)
    value = parse_value(expression, memory)
    if isinstance(value, (list, tuple, range, str, dict)):
        return value
    raise EasyError("for expects a list, string, map, or range(start, stop)")


def interpolate_text(value, memory):
    """Replace {variable} placeholders without turning strings into Python code."""
    return re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", lambda match: str(memory.get(match.group(1), match.group(0))), str(value))


def split_arguments(source):
    """Split comma-separated syntax while respecting strings and JSON literals."""
    items, current, quote, depth = [], [], None, 0
    for char in source:
        if char in ('"', "'"):
            quote = None if quote == char else char if quote is None else quote
        elif quote is None and char in "([{":
            depth += 1
        elif quote is None and char in ")]}":
            depth = max(0, depth - 1)
        if char == "," and quote is None and depth == 0:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if "".join(current).strip():
        items.append("".join(current).strip())
    return items


def parse_tags(raw):
    result = {
        "box": False,
        "box_style": "single",
        "chat": None,
        "sidebar": False,
        "header": False,
        "footer": False,
        "alert": False,
        "badge": False,
        "code": False,
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
        "fg": None,
        "panel": None,
        "card": False,
        "key": None,
        "toast": None,
        "rule": False,
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
    if re.search(r"\[badge\]", raw, re.IGNORECASE):
        result["badge"] = True
    if re.search(r"\[code\]", raw, re.IGNORECASE):
        result["code"] = True
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

    bg_match = re.search(r"\[bg:([#\w]+)\]", raw, re.IGNORECASE)
    if bg_match:
        result["bg"] = bg_match.group(1).lower()

    fg_match = re.search(r"\[fg:([#\w]+)\]", raw, re.IGNORECASE)
    if fg_match:
        result["fg"] = fg_match.group(1).lower()

    panel_match = re.search(r"\[panel:([^\]]+)\]", raw, re.IGNORECASE)
    if panel_match:
        result["panel"] = panel_match.group(1).strip()
    if re.search(r"\[card\]", raw, re.IGNORECASE):
        result["card"] = True
    key_match = re.search(r"\[key:([^\]]+)\]", raw, re.IGNORECASE)
    if key_match:
        result["key"] = key_match.group(1).strip()
    toast_match = re.search(r"\[toast(?::(success|info|warning|error))?\]", raw, re.IGNORECASE)
    if toast_match:
        result["toast"] = (toast_match.group(1) or "info").lower()
    if re.search(r"\[rule\]", raw, re.IGNORECASE):
        result["rule"] = True

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
        r"badge|"
        r"code|"
        r"list|"
        r"table|"
        r"progress:\d+|"
        r"spinner|"
        r"input:[^\]]+|"
        r"hr|"
        r"align:(?:left|center|right)|"
        r"padding:\d+|"
        r"width:\d+|"
        r"bg:[#\w]+|"
        r"fg:[#\w]+|"
        r"panel:[^\]]+|"
        r"card|"
        r"key:[^\]]+|"
        r"toast(?::(?:success|info|warning|error))?|"
        r"rule|"
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
    hex_match = re.search(r"\s+(#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6})\s*$", raw)
    if hex_match:
        color_code = color_to_ansi(hex_match.group(1))
        raw = raw[: hex_match.start()].strip()
        return color_code, raw
    color_match = re.search(r":(\w+):\s*$", raw)
    if color_match:
        color_name = color_match.group(1)
        if color_name in COLORS:
            color_code = COLORS[color_name]
        raw = raw[: color_match.start()].strip()
    return color_code, raw


def eval_builtins_in_string(text, memory, functions=None):
    pattern = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^()]*)\)")

    def split_args(args_str):
        args = []
        current = ""
        quote = None
        depth = 0
        for ch in args_str:
            if ch in ('"', "'"):
                quote = None if quote == ch else ch if quote is None else quote
                current += ch
            elif quote is None and ch in "([{":
                depth += 1
                current += ch
            elif quote is None and ch in ")]}":
                depth = max(0, depth - 1)
                current += ch
            elif ch == ',' and quote is None and depth == 0:
                args.append(current.strip())
                current = ""
            else:
                current += ch
        if current.strip():
            args.append(current.strip())
        return args

    def find_builtin_match(text):
        matches = []
        i = 0
        while i < len(text):
            if text[i] == '"':
                i += 1
                while i < len(text) and text[i] != '"':
                    i += 1
                i += 1
                continue
            m = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', text[i:])
            if not m:
                i += 1
                continue
            name_start = i + m.start(1)
            open_pos = i + m.end() - 1
            depth = 1
            close_pos = open_pos + 1
            while close_pos < len(text) and depth > 0:
                if text[close_pos] == '(':
                    depth += 1
                elif text[close_pos] == ')':
                    depth -= 1
                close_pos += 1
            if depth == 0:
                matches.append((name_start, close_pos, text[name_start:close_pos]))
            i = open_pos + 1
        if not matches:
            return None
        return min(matches, key=lambda m: m[1] - m[0])

    prev = None
    result = text
    while prev != result:
        prev = result
        match = find_builtin_match(result)
        if not match:
            break
        name_start, end, full_match = match
        name = result[name_start:result.index('(', name_start)].strip()
        args_str = result[result.index('(', name_start)+1:end-1]
        args = split_args(args_str)
        try:
            if functions and name in functions:
                replacement = str(call_user_function(name, args, memory, functions))
            else:
                replacement = str(builtin(name, args, memory))
            result = result[:name_start] + replacement + result[end:]
        except EasyError:
            pass
    return result


def parse_say_args(raw, memory, functions=None):
    raw = raw.strip()
    color_code, raw = parse_color(raw)
    component = parse_tags(raw)
    raw = strip_tags(raw)
    raw = eval_builtins_in_string(raw, memory, functions)
    value = parse_value(raw, memory)
    return interpolate_text(value, memory), component, color_code


def format_border(text, style_name="single", width=None, padding=1):
    lines = str(text).split("\n")
    width = width or max((len(strip_ansi(line)) for line in lines), default=0)
    tl, h, tr, v, bl, h2, br = BORDERS.get(style_name, BORDERS["single"])
    inner_width = width + padding * 2
    top = f"{tl}{h * (inner_width + 2)}{tr}"
    middle = [
        f"{v}{' ' * padding}{line}{' ' * max(0, width - len(strip_ansi(line)) + padding)} {v}"
        for line in lines
    ]
    bottom = f"{bl}{h2 * (inner_width + 2)}{br}"
    return [top, *middle, bottom]


def format_panel(text, title, width=None, padding=1):
    """Render a titled card for terminal dashboards and agent workspaces."""
    lines = str(text).split("\n")
    title = str(title or "PANEL").upper()
    content_width = max((len(strip_ansi(line)) for line in lines), default=0)
    width = max(width or content_width, content_width, len(title) + 4)
    top_fill = max(1, width - len(title) - 2)
    output = [f"╭─ {title} {'─' * top_fill}╮"]
    for line in lines:
        space = max(0, width - len(strip_ansi(line)) + padding)
        output.append(f"│{' ' * padding}{line}{' ' * space}│")
    output.append(f"╰{'─' * (width + padding * 2)}╯")
    return output


def format_chat(text, side, width=None):
    visible = strip_ansi(text)
    width = width or max(len(visible), 20)
    if side == "left":
        return [f"\u25b6 {text}"]
    return [f"{text} \u25c0"]


def format_sidebar(text, padding=1, width=None):
    visible = strip_ansi(text)
    width = width or max(len(visible), 20)
    inner_width = width + padding * 2
    top = f"\u252c{'─' * inner_width}\u252c"
    middle = f"\u2502{' ' * padding}{text}{' ' * padding}\u2502"
    bottom = f"\u2514{'─' * inner_width}\u2518"
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


def format_toast(text, kind):
    icon = {"success": "✓", "warning": "⚠", "error": "✕", "info": "●"}.get(kind, "●")
    return [f" {icon} {str(kind or 'info').upper():<7} {text}"]


def format_list(text, width=None):
    visible = strip_ansi(text)
    width = width or len(visible)
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


def format_row(left, right, left_width=28, total_width=96):
    """Render a durable two-pane workspace row for dashboards and coding UIs."""
    left_width = max(12, min(int(left_width), total_width - 16))
    right_width = total_width - left_width - 3
    left_lines = str(left).split("\n")
    right_lines = str(right).split("\n")
    height = max(len(left_lines), len(right_lines))
    output = [f"┌{'─' * left_width}┬{'─' * right_width}┐"]
    for index in range(height):
        left_line = left_lines[index] if index < len(left_lines) else ""
        right_line = right_lines[index] if index < len(right_lines) else ""
        output.append(f"│ {left_line[:left_width - 2]:<{left_width - 2}} │ {right_line[:right_width - 2]:<{right_width - 2}} │")
    output.append(f"└{'─' * left_width}┴{'─' * right_width}┘")
    return output


def render_table(rows):
    if not rows:
        return []
    columns = []
    for row in rows:
        parts = [p.strip() for p in row.split("|")]
        while len(columns) < len(parts):
            columns.append(0)
        for i, part in enumerate(parts):
            columns[i] = max(columns[i], len(strip_ansi(part)))
    result = []
    for row in rows:
        parts = [p.strip() for p in row.split("|")]
        while len(parts) < len(columns):
            parts.append("")
        formatted_parts = []
        for i, part in enumerate(parts):
            pad = max(0, columns[i] - len(strip_ansi(part)))
            formatted_parts.append(part + " " * pad)
        result.append(" | ".join(formatted_parts))
    return result


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
    if component["fg"]:
        color_code = color_to_ansi(component["fg"])
    if color_code:
        text = f"{color_code}{text}{RESET}"

    if component["bg"]:
        text = apply_bg(text, component["bg"])

    if component["styles"]:
        text = apply_styles(text, component["styles"])

    text = align_text(text, component["align"], component["width"])

    if component["alert"]:
        return format_alert(text)

    if component["toast"]:
        return format_toast(text, component["toast"])

    if component["rule"]:
        return format_hr(component["width"] or 40)

    if component["key"]:
        text = f"[ {component['key']} ]  {text}"

    if component["panel"]:
        return format_panel(text, component["panel"], component["width"], component["padding"])

    if component["card"]:
        return format_border(text, "rounded", component["width"], component["padding"])

    if component["badge"]:
        return [f"[ {text} ]"]

    if component["code"]:
        return format_border(text, "dotted", component["width"], component["padding"])

    if component["chat"]:
        return format_chat(text, component["chat"], component["width"])

    if component["sidebar"]:
        return format_sidebar(text, component["padding"], component["width"])

    if component["header"]:
        return format_header(text, component["width"])

    if component["footer"]:
        return format_footer(text, component["width"])

    if component["list"]:
        return format_list(text, component["width"])

    if component["hr"]:
        return format_hr(component["width"] or 40)

    if component["progress"] is not None:
        return format_progress(component["progress"], component["width"] or 30)

    if component["spinner"]:
        return format_spinner(0)

    if component["box"]:
        return format_border(text, component["box_style"], component["width"], component["padding"])

    if component["width"]:
        visible = strip_ansi(text)
        pad = max(0, component["width"] - len(visible))
        text = text + " " * pad

    return [text]


def parse_api_call_args(raw):
    raw = raw.strip()
    if not raw.startswith("[api-call]"):
        return None

    raw = raw[len("[api-call]"):].strip()
    if not (raw.startswith("<") and ">" in raw):
        raise EasyError("api-call needs <service>(...)")

    service = raw[1:raw.index(">")]
    rest = raw[raw.index(">") + 1:].strip()

    if not (rest.startswith("(") and rest.endswith(")")):
        raise EasyError("api-call params must be in parentheses")

    params_str = rest[1:-1]
    params = {}

    for pair in split_arguments(params_str):
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            params[key] = value[1:-1]
        else:
            params[key] = value

    return service, params


API_ROUTES = {
    "gemini": {
        "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "method": "POST",
        "headers": lambda key: {"Content-Type": "application/json", "x-goog-api-key": key},
        "body": lambda params: json.dumps({"contents": [{"parts": [{"text": params.get("prompt", "")}]}]}),
        "extract": lambda data: data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", ""),
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "method": "POST",
        "headers": lambda key: {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        "body": lambda params: json.dumps({"model": params.get("model", "gpt-3.5-turbo"), "messages": [{"role": "user", "content": params.get("prompt", "")}]}),
        "extract": lambda data: data.get("choices", [{}])[0].get("message", {}).get("content", ""),
    },
    "huggingface": {
        "url": "https://api-inference.huggingface.co/models/{model}",
        "method": "POST",
        "headers": lambda key: {"Authorization": f"Bearer {key}"},
        "body": lambda params: json.dumps({"inputs": params.get("prompt", "")}),
        "extract": lambda data: data[0].get("generated_text", "") if isinstance(data, list) else str(data),
    },
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "method": "POST",
        "headers": lambda key: {"Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
        "body": lambda params: json.dumps({"model": params.get("model", "claude-3-haiku-20240307"), "max_tokens": params.get("max_tokens", 1024), "messages": [{"role": "user", "content": params.get("prompt", "")}]}),
        "extract": lambda data: data.get("content", [{}])[0].get("text", ""),
    },
    "cohere": {
        "url": "https://api.cohere.ai/v1/generate",
        "method": "POST",
        "headers": lambda key: {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        "body": lambda params: json.dumps({"model": params.get("model", "command"), "prompt": params.get("prompt", ""), "max_tokens": params.get("max_tokens", 256)}),
        "extract": lambda data: data.get("generations", [{}])[0].get("text", ""),
    },
    "ollama": {
        "url": "http://localhost:11434/api/generate",
        "method": "POST",
        "headers": lambda key: {"Content-Type": "application/json"},
        "body": lambda params: json.dumps({"model": params.get("model", "llama3.2"), "prompt": params.get("prompt", ""), "stream": False}),
        "extract": lambda data: data.get("response", "") if isinstance(data, dict) else str(data),
    },
    "http": {
        "url": None,
        "method": "GET",
        "headers": lambda key: {},
        "body": lambda params: None,
        "extract": lambda data: json.dumps(data) if isinstance(data, (dict, list)) else str(data),
    },
}


def resolve_param(value, memory):
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value in memory:
        return str(memory[value])
    try:
        return str(int(value))
    except ValueError:
        return value


def resolve_api_value(value, memory):
    """Resolve variables and JSON literals passed to an api-call parameter."""
    if value in memory:
        return memory[value]
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


def api_call(service, params, memory):
    if service not in API_ROUTES:
        raise EasyError(f"unknown api service: {service}")

    route = API_ROUTES[service]
    if service not in {"http", "ollama"}:
        key_param = params.get("api-key") or params.get("api_key") or params.get("key")
        if not key_param:
            raise EasyError("api-call needs api-key param")

    api_key = None
    if service not in {"http", "ollama"}:
        api_key = resolve_param(str(key_param), memory)
        if not api_key:
            raise EasyError("api-key is empty")

    if service == "http":
        url = params.get("url")
        if not url:
            raise EasyError("http api-call needs url param")
        route = dict(route)
        route["url"] = url
        route["method"] = params.get("method", "GET").upper()
        supplied_headers = resolve_api_value(params.get("headers", "{}"), memory)
        if not isinstance(supplied_headers, dict):
            raise EasyError("http headers must be a JSON-style map")
        route["headers"] = lambda _key: {str(key): str(value) for key, value in supplied_headers.items()}
        if "json" in params:
            supplied_body = resolve_api_value(params["json"], memory)
            route["body"] = lambda _params: json.dumps(supplied_body)
            route["headers"] = lambda _key: {**{str(key): str(value) for key, value in supplied_headers.items()}, "Content-Type": "application/json"}
        elif "body" in params:
            supplied_body = resolve_api_value(params["body"], memory)
            route["body"] = lambda _params: json.dumps(supplied_body) if isinstance(supplied_body, (dict, list)) else str(supplied_body)
    elif service == "huggingface":
        model = params.get("model", "gpt2")
        route = dict(route)
        route["url"] = route["url"].format(model=model)

    url = route["url"]
    method = route["method"]
    headers = route["headers"](api_key)
    body = route["body"](params)

    req = urllib.request.Request(url, data=body.encode("utf-8") if body else None, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=int(params.get("timeout", 30))) as response:
            raw = response.read().decode("utf-8")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = raw
            return route["extract"](data)
    except urllib.error.HTTPError as e:
        raise EasyError(f"api error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise EasyError(f"api request failed: {e.reason}")


def request_data(url, method="GET", body=None, headers=None, timeout=20):
    """Perform a JSON/text HTTP request for METRIX programs."""
    headers = {str(key): str(value) for key, value in (headers or {}).items()}
    payload = None
    if body not in (None, ""):
        if isinstance(body, (dict, list)):
            headers.setdefault("Content-Type", "application/json")
            payload = json.dumps(body).encode("utf-8")
        else:
            payload = str(body).encode("utf-8")
    request = urllib.request.Request(str(url), data=payload, headers=headers, method=str(method).upper())
    try:
        with urllib.request.urlopen(request, timeout=int(timeout)) as response:
            raw = response.read().decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:300]
        raise EasyError(f"request failed ({error.code}): {detail or error.reason}")
    except urllib.error.URLError as error:
        raise EasyError(f"request failed: {error.reason}")


def builtin(name, args, memory):
    if name == "get":
        container = parse_value(args[0], memory) if args else {}
        key = parse_value(args[1], memory) if len(args) > 1 else ""
        default = parse_value(args[2], memory) if len(args) > 2 else ""
        if isinstance(container, dict):
            return container.get(str(key), default)
        if isinstance(container, (list, tuple)):
            try:
                return container[int(key)]
            except (ValueError, IndexError):
                return default
        return default
    if name == "keys":
        value = parse_value(args[0], memory) if args else {}
        return list(value.keys()) if isinstance(value, dict) else []
    if name == "values":
        value = parse_value(args[0], memory) if args else {}
        return list(value.values()) if isinstance(value, dict) else []
    if name == "count":
        value = parse_value(args[0], memory) if args else ""
        return len(value)
    if name == "title":
        return str(parse_value(args[0], memory) if args else "").title()
    if name == "slug":
        value = str(parse_value(args[0], memory) if args else "").lower().strip()
        return re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if name == "sort":
        value = parse_value(args[0], memory) if args else []
        return sorted(value) if isinstance(value, list) else value
    if name == "first":
        value = parse_value(args[0], memory) if args else []
        return value[0] if isinstance(value, (list, tuple, str)) and value else ""
    if name == "last":
        value = parse_value(args[0], memory) if args else []
        return value[-1] if isinstance(value, (list, tuple, str)) and value else ""
    if name == "reverse":
        value = parse_value(args[0], memory) if args else []
        if isinstance(value, str):
            return value[::-1]
        if isinstance(value, (list, tuple)):
            return list(reversed(value))
        return value
    if name == "unique":
        value = parse_value(args[0], memory) if args else []
        if not isinstance(value, list):
            return value
        result = []
        for item in value:
            if item not in result:
                result.append(item)
        return result
    if name == "slice":
        value = parse_value(args[0], memory) if args else ""
        start = int(parse_value(args[1], memory)) if len(args) > 1 else 0
        end = int(parse_value(args[2], memory)) if len(args) > 2 else None
        return value[start:end]
    if name == "index":
        value = parse_value(args[0], memory) if args else []
        item = parse_value(args[1], memory) if len(args) > 1 else ""
        try:
            return value.index(item)
        except (ValueError, AttributeError):
            return -1
    if name == "find":
        value = str(parse_value(args[0], memory) if args else "")
        query = str(parse_value(args[1], memory) if len(args) > 1 else "")
        return value.find(query)
    if name == "flatten":
        value = parse_value(args[0], memory) if args else []
        if not isinstance(value, list):
            return value
        return [child for item in value for child in (item if isinstance(item, list) else [item])]
    if name == "stringify":
        value = parse_value(args[0], memory) if args else None
        return json.dumps(value, ensure_ascii=False)
    if name == "number":
        value = str(parse_value(args[0], memory) if args else "0")
        try:
            return float(value) if "." in value else int(value)
        except ValueError:
            raise EasyError(f"number expects numeric text, got {value!r}")
    if name == "string":
        return str(parse_value(args[0], memory) if args else "")
    if name == "boolean":
        value = parse_value(args[0], memory) if args else False
        if isinstance(value, str):
            return value.strip().lower() not in {"", "0", "false", "no", "null", "none"}
        return bool(value)
    if name == "repeat":
        value = str(parse_value(args[0], memory) if args else "")
        times = int(parse_value(args[1], memory)) if len(args) > 1 else 1
        return value * max(0, times)
    if name == "pad":
        value = str(parse_value(args[0], memory) if args else "")
        width = int(parse_value(args[1], memory)) if len(args) > 1 else len(value)
        side = str(parse_value(args[2], memory) if len(args) > 2 else "right").lower()
        if side == "left":
            return value.rjust(width)
        if side == "center":
            return value.center(width)
        return value.ljust(width)
    if name == "urlencode":
        return urllib.parse.quote_plus(str(parse_value(args[0], memory) if args else ""))
    if name == "urldecode":
        return urllib.parse.unquote_plus(str(parse_value(args[0], memory) if args else ""))
    if name == "uuid":
        import uuid
        return str(uuid.uuid4())
    if name == "len":
        return len(parse_value(args[0], memory) if args else "")
    if name == "upper":
        return (parse_value(args[0], memory) if args else "").upper()
    if name == "lower":
        return (parse_value(args[0], memory) if args else "").lower()
    if name == "trim":
        return (parse_value(args[0], memory) if args else "").strip()
    if name == "split":
        text = parse_value(args[0], memory) if args else ""
        sep = parse_value(args[1], memory) if len(args) > 1 else " "
        return text.split(sep)
    if name == "join":
        parts = parse_value(args[0], memory) if args else []
        sep = parse_value(args[1], memory) if len(args) > 1 else " "
        if isinstance(parts, list):
            return sep.join(parts)
        raise EasyError("join expects a list")
    if name == "replace":
        text = parse_value(args[0], memory) if args else ""
        old = parse_value(args[1], memory) if len(args) > 1 else ""
        new = parse_value(args[2], memory) if len(args) > 2 else ""
        return text.replace(old, new)
    if name == "contains":
        text = parse_value(args[0], memory) if args else ""
        sub = parse_value(args[1], memory) if len(args) > 1 else ""
        return "true" if sub in text else "false"
    if name == "startswith":
        text = parse_value(args[0], memory) if args else ""
        sub = parse_value(args[1], memory) if len(args) > 1 else ""
        return "true" if text.startswith(sub) else "false"
    if name == "endswith":
        text = parse_value(args[0], memory) if args else ""
        sub = parse_value(args[1], memory) if len(args) > 1 else ""
        return "true" if text.endswith(sub) else "false"
    if name == "now":
        return datetime.datetime.now().isoformat()
    if name == "date":
        return datetime.date.today().isoformat()
    if name == "time":
        return datetime.datetime.now().strftime("%H:%M:%S")
    if name == "sleep":
        import time
        time.sleep(int(parse_value(args[0], memory)) if args else 1)
        return ""
    if name == "random":
        low = int(parse_value(args[0], memory)) if args else 0
        high = int(parse_value(args[1], memory) if len(args) > 1 else 100)
        return random.randint(low, high)
    if name == "math":
        expr = parse_value(args[0], memory) if args else ""
        try:
            math_globals = {"__builtins__": {}}
            math_locals = {"math": math}
            math_locals.update({k: getattr(math, k) for k in dir(math) if not k.startswith("_")})
            return str(eval(expr, math_globals, math_locals))
        except Exception as e:
            raise EasyError(f"math error: {e}")
    if name == "read":
        path = parse_value(args[0], memory) if args else ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    if name == "write":
        path = parse_value(args[0], memory) if args else ""
        content = parse_value(args[1], memory) if len(args) > 1 else ""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return "ok"
    if name == "append":
        path = parse_value(args[0], memory) if args else ""
        content = parse_value(args[1], memory) if len(args) > 1 else ""
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return "ok"
    if name == "exists":
        path = parse_value(args[0], memory) if args else ""
        return "true" if os.path.exists(path) else "false"
    if name == "delete":
        path = parse_value(args[0], memory) if args else ""
        os.remove(path)
        return "ok"
    if name == "listdir":
        path = parse_value(args[0], memory) if args else "."
        return "\n".join(os.listdir(path))
    if name == "exec":
        cmd = parse_value(args[0], memory) if args else ""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    if name == "env":
        var = parse_value(args[0], memory) if args else ""
        return os.environ.get(var, "")
    if name == "json":
        text = parse_value(args[0], memory) if args else ""
        return json.loads(text)
    if name == "base64":
        import base64
        text = parse_value(args[0], memory) if args else ""
        return base64.b64encode(text.encode()).decode()
    if name == "decode":
        import base64
        text = parse_value(args[0], memory) if args else ""
        return base64.b64decode(text.encode()).decode()
    if name == "hash":
        import hashlib
        text = parse_value(args[0], memory) if args else ""
        algo = parse_value(args[1], memory) if len(args) > 1 else "sha256"
        h = hashlib.new(algo)
        h.update(text.encode())
        return h.hexdigest()
    if name == "http":
        url = parse_value(args[0], memory) if args else ""
        method = parse_value(args[1], memory) if len(args) > 1 else "GET"
        result = request_data(url, method)
        return json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else result
    if name == "request":
        url = parse_value(args[0], memory) if args else ""
        method = parse_value(args[1], memory) if len(args) > 1 else "GET"
        body = parse_value(args[2], memory) if len(args) > 2 else None
        headers = parse_value(args[3], memory) if len(args) > 3 else {}
        timeout = parse_value(args[4], memory) if len(args) > 4 else 20
        if not isinstance(headers, dict):
            raise EasyError("request headers must be a JSON-style map")
        return request_data(url, method, body, headers, timeout)
    if name == "webhook":
        url = parse_value(args[0], memory) if args else ""
        payload = parse_value(args[1], memory) if len(args) > 1 else {}
        headers = parse_value(args[2], memory) if len(args) > 2 else {}
        if not isinstance(headers, dict):
            raise EasyError("webhook headers must be a JSON-style map")
        return request_data(url, "POST", payload, headers)
    if name == "download":
        url = parse_value(args[0], memory) if args else ""
        path = parse_value(args[1], memory) if len(args) > 1 else "download.txt"
        result = request_data(url)
        with open(path, "w", encoding="utf-8") as file:
            file.write(json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, (dict, list)) else str(result))
        return str(path)
    if name == "len":
        return len(parse_value(args[0], memory) if args else "")
    if name == "upper":
        return (parse_value(args[0], memory) if args else "").upper()
    if name == "lower":
        return (parse_value(args[0], memory) if args else "").lower()
    if name == "trim":
        return (parse_value(args[0], memory) if args else "").strip()
    if name == "split":
        text = parse_value(args[0], memory) if args else ""
        sep = parse_value(args[1], memory) if len(args) > 1 else " "
        return text.split(sep)
    if name == "join":
        parts = parse_value(args[0], memory) if args else []
        sep = parse_value(args[1], memory) if len(args) > 1 else " "
        if isinstance(parts, list):
            return sep.join(parts)
        raise EasyError("join expects a list")
    if name == "replace":
        text = parse_value(args[0], memory) if args else ""
        old = parse_value(args[1], memory) if len(args) > 1 else ""
        new = parse_value(args[2], memory) if len(args) > 2 else ""
        return text.replace(old, new)
    if name == "contains":
        text = parse_value(args[0], memory) if args else ""
        sub = parse_value(args[1], memory) if len(args) > 1 else ""
        return "true" if sub in text else "false"
    if name == "startswith":
        text = parse_value(args[0], memory) if args else ""
        sub = parse_value(args[1], memory) if len(args) > 1 else ""
        return "true" if text.startswith(sub) else "false"
    if name == "endswith":
        text = parse_value(args[0], memory) if args else ""
        sub = parse_value(args[1], memory) if len(args) > 1 else ""
        return "true" if text.endswith(sub) else "false"
    if name == "now":
        return datetime.datetime.now().isoformat()
    if name == "date":
        return datetime.date.today().isoformat()
    if name == "time":
        return datetime.datetime.now().strftime("%H:%M:%S")
    if name == "sleep":
        import time
        time.sleep(int(parse_value(args[0], memory)) if args else 1)
        return ""
    if name == "random":
        low = int(parse_value(args[0], memory)) if args else 0
        high = int(parse_value(args[1], memory) if len(args) > 1 else 100)
        return random.randint(low, high)
    if name == "math":
        expr = parse_value(args[0], memory) if args else ""
        try:
            math_globals = {"__builtins__": {}}
            math_locals = {"math": math}
            math_locals.update({k: getattr(math, k) for k in dir(math) if not k.startswith("_")})
            return str(eval(expr, math_globals, math_locals))
        except Exception as e:
            raise EasyError(f"math error: {e}")
    if name == "read":
        path = parse_value(args[0], memory) if args else ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    if name == "write":
        path = parse_value(args[0], memory) if args else ""
        content = parse_value(args[1], memory) if len(args) > 1 else ""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return "ok"
    if name == "append":
        path = parse_value(args[0], memory) if args else ""
        content = parse_value(args[1], memory) if len(args) > 1 else ""
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return "ok"
    if name == "exists":
        path = parse_value(args[0], memory) if args else ""
        return "true" if os.path.exists(path) else "false"
    if name == "delete":
        path = parse_value(args[0], memory) if args else ""
        os.remove(path)
        return "ok"
    if name == "listdir":
        path = parse_value(args[0], memory) if args else "."
        return "\n".join(os.listdir(path))
    if name == "exec":
        cmd = parse_value(args[0], memory) if args else ""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    if name == "env":
        var = parse_value(args[0], memory) if args else ""
        return os.environ.get(var, "")
    if name == "json":
        text = parse_value(args[0], memory) if args else ""
        return json.loads(text)
    if name == "base64":
        import base64
        text = parse_value(args[0], memory) if args else ""
        return base64.b64encode(text.encode()).decode()
    if name == "decode":
        import base64
        text = parse_value(args[0], memory) if args else ""
        return base64.b64decode(text.encode()).decode()
    if name == "hash":
        import hashlib
        text = parse_value(args[0], memory) if args else ""
        algo = parse_value(args[1], memory) if len(args) > 1 else "sha256"
        h = hashlib.new(algo)
        h.update(text.encode())
        return h.hexdigest()
    if name == "http":
        url = parse_value(args[0], memory) if args else ""
        method = parse_value(args[1], memory) if len(args) > 1 else "GET"
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req) as response:
            return response.read().decode()
    raise EasyError(f"unknown function: {name}")


def call_user_function(name, raw_args, memory, functions):
    params, body = functions[name]
    if len(raw_args) != len(params):
        raise EasyError(f"{name} expects {len(params)} argument(s), got {len(raw_args)}")
    local_memory = dict(memory)
    for param, raw_value in zip(params, raw_args):
        local_memory[param] = parse_value(raw_value, memory)
    try:
        run(body, local_memory, functions, allow_return=True)
    except ReturnSignal as signal:
        return signal.value
    return ""


def parse_builtin_call(line):
    line = line.strip()
    match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)$", line)
    if not match:
        return None
    name = match.group(1)
    args_str = match.group(2)
    args = []
    if args_str.strip():
        for arg in re.split(r",\s*", args_str):
            args.append(arg.strip())
    return name, args


KNOWN_COMMANDS = {
    "say", "set", "let", "ask", "select", "clear", "row", "add", "sub",
    "metrix", "if", "else", "for", "while", "func", "return",
}


def check_source(source):
    """Return static syntax issues without running files, requests, or commands."""
    issues = []
    lines = source.splitlines()
    previous_code = None
    block_indent = None

    for number, original in enumerate(lines, start=1):
        stripped = original.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "\t" in original[:len(original) - len(original.lstrip())]:
            issues.append(("error", number, "indentation uses a tab; use spaces"))
        indent = len(original) - len(original.lstrip(" "))
        if indent % 4:
            issues.append(("error", number, "indentation must be a multiple of four spaces"))
        if block_indent is not None:
            if indent <= block_indent:
                issues.append(("error", number, "expected an indented block after ':'"))
            block_indent = None

        quote = None
        stack = []
        pairs = {")": "(", "]": "[", "}": "{"}
        for char in stripped:
            if char in {'"', "'"}:
                quote = None if quote == char else char if quote is None else quote
            elif quote is None and char in "([{":
                stack.append(char)
            elif quote is None and char in ")]}":
                if not stack or stack.pop() != pairs[char]:
                    issues.append(("error", number, f"unmatched '{char}'"))
                    break
        else:
            if quote:
                issues.append(("error", number, "unterminated string"))
            elif stack:
                issues.append(("error", number, f"unclosed '{stack[-1]}'"))

        command = stripped.split(maxsplit=1)[0]
        is_assignment = re.match(r"[A-Za-z_][A-Za-z0-9_]*\s*=", stripped)
        is_call = re.match(r"[A-Za-z_][A-Za-z0-9_]*\s*\(", stripped)
        if command not in KNOWN_COMMANDS and not is_assignment and not is_call:
            issues.append(("error", number, f"unknown command '{command}'"))

        if command in {"if", "for", "while", "func", "else"}:
            if not stripped.endswith(":"):
                issues.append(("error", number, f"{command} block must end with ':'"))
            else:
                block_indent = indent
        if command == "else" and stripped != "else:":
            issues.append(("error", number, "else syntax is exactly: else:"))
        if command in {"set", "let", "add", "sub", "ask", "select"}:
            parts = stripped.split()
            if len(parts) < 2 or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", parts[1]):
                issues.append(("error", number, f"{command} needs a valid variable name"))
        if command == "row" and not re.fullmatch(r"row\s+.+?\s*\|\s*.+?(?:\s+\[left:\d+\])?", stripped):
            issues.append(("error", number, 'row syntax is: row "left" | "right" [left:28]'))
        if command == "metrix" and "[api-call]" in stripped:
            try:
                parsed = parse_api_call_args(stripped[len("metrix"):].strip())
                if parsed and parsed[0] not in API_ROUTES:
                    issues.append(("error", number, f"unknown API service '{parsed[0]}'"))
            except EasyError as error:
                issues.append(("error", number, str(error)))

        # Only inspect tags outside strings. JSON lists and literal keyboard
        # labels are valid program text, not UI tags.
        tag_source = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', stripped)
        for tag in re.findall(r"\[([^\]]+)\]", tag_source):
            if '"' in tag or "'" in tag:
                continue
            valid = (
                tag in {"box", "sidebar", "header", "footer", "alert", "badge", "code", "list", "table", "hr", "spinner", "card", "rule", "bold", "dim", "italic", "underline", "blink", "reverse", "strikethrough"}
                or re.fullmatch(r"box:(single|double|rounded|bold|dotted)", tag, re.IGNORECASE)
                or re.fullmatch(r"chat:(left|right)", tag, re.IGNORECASE)
                or re.fullmatch(r"progress:\d+", tag)
                or re.fullmatch(r"input:[^\]]+", tag)
                or re.fullmatch(r"align:(left|center|right)", tag, re.IGNORECASE)
                or re.fullmatch(r"(padding|width|left):\d+", tag)
                or re.fullmatch(r"(bg|fg):(?:#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}|[A-Za-z_]+)", tag)
                or re.fullmatch(r"panel:[^\]]+", tag, re.IGNORECASE)
                or re.fullmatch(r"key:[^\]]+", tag, re.IGNORECASE)
                or re.fullmatch(r"toast(?::(?:success|info|warning|error))?", tag, re.IGNORECASE)
                or tag == "api-call"
            )
            if not valid:
                issues.append(("error", number, f"unknown or invalid UI tag '[{tag}]'"))
        previous_code = (number, indent, stripped)

    if block_indent is not None:
        issues.append(("error", len(lines) or 1, "expected an indented block after ':'"))
    return issues


def run(source, memory=None, functions=None, allow_return=False):
    memory = {} if memory is None else memory
    functions = {} if functions is None else functions
    config = {}
    output = []
    spinner_frame = 0
    table_buffer = []

    lines = source.splitlines()
    line_number = 0

    def block_after(start, parent_indent):
        """Return the indented block after a control-flow line and its end."""
        block = []
        index = start
        while index < len(lines):
            candidate = lines[index]
            stripped_candidate = candidate.strip()
            indent = len(candidate) - len(candidate.lstrip())
            if stripped_candidate and indent <= parent_indent:
                break
            block.append(candidate)
            index += 1
        if not any(item.strip() for item in block):
            raise EasyError("expected an indented block")
        return textwrap.dedent("\n".join(block)), index

    while line_number < len(lines):
        original_line = lines[line_number]
        line = original_line.strip()
        indent = len(original_line) - len(original_line.lstrip())
        line_number += 1

        if not line or line.startswith("#"):
            continue

        if "=" in line and not line.startswith("[") and line.split()[0] not in ("say", "set", "let", "ask", "select", "clear", "row", "add", "sub", "metrix", "if", "for", "while", "func", "return"):
            if table_buffer:
                output.extend(render_table(table_buffer))
                table_buffer = []
            var_name, var_value = line.split("=", 1)
            var_name = var_name.strip()
            var_value = var_value.strip().strip('"')
            if var_name and var_value:
                memory[var_name] = var_value
                config[var_name] = var_value
            continue

        parts = line.split(maxsplit=2)
        command = parts[0]

        try:
            if command == "if":
                if not line.endswith(":"):
                    raise EasyError("if condition must end with ':'")
                condition = line[2:-1].strip()
                body, line_number = block_after(line_number, indent)
                else_body = None
                if line_number < len(lines) and lines[line_number].strip() == "else:":
                    else_indent = len(lines[line_number]) - len(lines[line_number].lstrip())
                    if else_indent != indent:
                        raise EasyError("else must align with its if")
                    else_body, line_number = block_after(line_number + 1, indent)
                selected = body if evaluate_condition(condition, memory) else else_body
                if selected:
                    output.extend(run(selected, memory, functions, allow_return))
                continue

            if command == "for":
                match = re.fullmatch(r"for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+):", line)
                if not match:
                    raise EasyError("for syntax is: for item in items:")
                name, expression = match.groups()
                body, line_number = block_after(line_number, indent)
                for value in iterable_value(expression, memory):
                    memory[name] = value
                    output.extend(run(body, memory, functions, allow_return))
                continue

            if command == "while":
                if not line.endswith(":"):
                    raise EasyError("while condition must end with ':'")
                condition = line[5:-1].strip()
                body, line_number = block_after(line_number, indent)
                iterations = 0
                while evaluate_condition(condition, memory):
                    iterations += 1
                    if iterations > 10_000:
                        raise EasyError("while loop exceeded 10,000 iterations")
                    output.extend(run(body, memory, functions, allow_return))
                continue

            if command == "func":
                match = re.fullmatch(r"func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*:", line)
                if not match:
                    raise EasyError("func syntax is: func name(arg1, arg2):")
                name, params_raw = match.groups()
                params = [item.strip() for item in params_raw.split(",") if item.strip()]
                if len(set(params)) != len(params) or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", item) for item in params):
                    raise EasyError("function parameters must be unique names")
                body, line_number = block_after(line_number, indent)
                functions[name] = (params, body)
                continue

            if command == "return":
                if not allow_return:
                    raise EasyError("return can only be used inside a function")
                raw_value = line[len("return"):].strip()
                value = parse_value(eval_builtins_in_string(raw_value, memory, functions), memory)
                raise ReturnSignal(value)

            if command == "row":
                match = re.fullmatch(r"row\s+(.+?)\s*\|\s*(.+?)(?:\s+\[left:(\d+)\])?$", line)
                if not match:
                    raise EasyError('row syntax is: row "left" | "right" [left:28]')
                left_raw, right_raw, left_width = match.groups()
                left = eval_builtins_in_string(str(parse_value(left_raw, memory)), memory, functions)
                right = eval_builtins_in_string(str(parse_value(right_raw, memory)), memory, functions)
                output.extend(format_row(left, right, int(left_width or 28)))
                continue

            builtin_call = parse_builtin_call(line)
            if builtin_call:
                if table_buffer:
                    output.extend(render_table(table_buffer))
                    table_buffer = []
                name, args = builtin_call
                result = call_user_function(name, args, memory, functions) if name in functions else builtin(name, args, memory)
                if result:
                    output.append(str(result))
                continue

            if command == "metrix":
                if table_buffer:
                    output.extend(render_table(table_buffer))
                    table_buffer = []
                if len(parts) < 2:
                    raise EasyError("metrix needs a subcommand")

                sub = parts[1]

                if sub.startswith("[api-call]"):
                    api_args = sub[len("[api-call]"):]
                    if len(parts) > 2:
                        api_args = api_args + " " + " ".join(parts[2:])
                    service, api_params = parse_api_call_args("[api-call]" + api_args)
                    resolved_params = {}
                    for k, v in api_params.items():
                        resolved_params[k] = resolve_param(v, memory)
                    result = api_call(service, resolved_params, memory)
                    memory["api_result"] = result
                    output.append(f"[API] {service}: {result[:200]}")
                    continue

                if sub == "[api-call]":
                    if len(parts) < 3:
                        raise EasyError("metrix [api-call] needs args")
                    service, api_params = parse_api_call_args(parts[2])
                    resolved_params = {}
                    for k, v in api_params.items():
                        resolved_params[k] = resolve_param(v, memory)
                    result = api_call(service, resolved_params, memory)
                    memory["api_result"] = result
                    output.append(f"[API] {service}: {result[:200]}")
                    continue

                raise EasyError(f"unknown metrix subcommand: {sub}")

            if command == "say":
                raw = line[4:]
                value, component, color_code = parse_say_args(raw, memory, functions)
                if component["table"]:
                    table_buffer.append(value)
                    continue
                if table_buffer:
                    output.extend(render_table(table_buffer))
                    table_buffer = []
                if component["spinner"]:
                    spinner_frame += 1
                    value = format_spinner(spinner_frame - 1)[0]
                output.extend(format_output(value, component, color_code))

            elif command in ("set", "let"):
                if table_buffer:
                    output.extend(render_table(table_buffer))
                    table_buffer = []
                if len(parts) != 3:
                    raise EasyError("set needs a name and value")
                resolved = eval_builtins_in_string(parts[2], memory, functions)
                memory[parts[1]] = parse_value(resolved, memory)

            elif command == "ask":
                if len(parts) != 3:
                    raise EasyError('ask syntax is: ask name "Prompt"')
                prompt = str(parse_value(parts[2], memory))
                memory[parts[1]] = input(f"{prompt} ")

            elif command == "select":
                match = re.fullmatch(r"select\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s+from\s+(.+)", line)
                if not match:
                    raise EasyError('select syntax is: select name "Prompt" from ["one", "two"]')
                name, prompt_raw, choices_raw = match.groups()
                prompt = interpolate_text(parse_value(prompt_raw, memory), memory)
                choices = parse_value(eval_builtins_in_string(choices_raw, memory, functions), memory)
                if not isinstance(choices, list) or not choices:
                    raise EasyError("select needs a non-empty list")
                print(prompt)
                for index, choice in enumerate(choices, start=1):
                    print(f"  {index}. {choice}")
                while True:
                    response = input("> ").strip()
                    if response.isdigit() and 1 <= int(response) <= len(choices):
                        memory[name] = choices[int(response) - 1]
                        break
                    print(f"Choose a number from 1 to {len(choices)}.")

            elif command == "clear":
                output.append("\033[2J\033[H")

            elif command in ("add", "sub"):
                if table_buffer:
                    output.extend(render_table(table_buffer))
                    table_buffer = []
                if len(parts) != 3:
                    raise EasyError(f"{command} needs a name and value")
                name = parts[1]
                current = memory.get(name, 0)
                change = parse_value(parts[2], memory)
                if not isinstance(current, int) or not isinstance(change, int):
                    raise EasyError(f"{command} only works with numbers")
                memory[name] = current + change if command == "add" else current - change

            else:
                if table_buffer:
                    output.extend(render_table(table_buffer))
                    table_buffer = []
                raise EasyError(f"unknown command: {command}")

        except EasyError as error:
            raise EasyError(f"line {line_number}: {error}")

    if table_buffer:
        output.extend(render_table(table_buffer))

    return output
