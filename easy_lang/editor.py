import os
from prompt_toolkit import PromptSession
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Window, HSplit, VSplit, FormattedTextControl, Layout
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style


EASY_KEYWORDS = [
    "say",
    "set",
    "add",
    "sub",
]

EASY_COLORS = [
    ":green:",
    ":red:",
    ":blue:",
    ":yellow:",
    ":cyan:",
    ":magenta:",
    ":white:",
    ":black:",
]


class EasyCompleter(Completer):
    def __init__(self, variables=None):
        self.variables = variables or []

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor(WORD=True)
        line = document.current_line
        stripped = line.strip()
        lower_stripped = stripped.lower()

        if not stripped:
            for kw in EASY_KEYWORDS:
                yield Completion(kw, start_position=-len(word) or 0)
            return

        parts = stripped.split()
        command = parts[0].lower() if parts else ""

        if command in ("say",):
            if lower_stripped.endswith(" ") or lower_stripped.lower().startswith("say "):
                if "[box]" not in stripped and not any(stripped.endswith(c) for c in EASY_COLORS):
                    yield Completion("[box]", start_position=-len(word) or 0)
                for color in EASY_COLORS:
                    yield Completion(color, start_position=-len(word) or 0)
                for var in self.variables:
                    yield Completion(var, start_position=-len(word) or 0)

        if command == "set":
            if len(parts) == 2:
                yield Completion("value", start_position=-len(word) or 0)
            elif len(parts) >= 3:
                for var in self.variables:
                    yield Completion(var, start_position=-len(word) or 0)

        if command in ("add", "sub"):
            if len(parts) == 2:
                for var in self.variables:
                    yield Completion(var, start_position=-len(word) or 0)
            elif len(parts) >= 3:
                for var in self.variables:
                    yield Completion(var, start_position=-len(word) or 0)

        if not command or command not in set(EASY_KEYWORDS):
            for kw in EASY_KEYWORDS:
                if kw.startswith(word):
                    yield Completion(kw, start_position=-len(word))


class EasyLexer(Lexer):
    def lex_document(self, document):
        def get_line(lineno):
            if lineno >= len(document.lines):
                return []

            line = document.lines[lineno]
            tokens = []

            if line.startswith("#"):
                tokens.append(("class:comment", line))
                return tokens

            i = 0
            while i < len(line):
                if line[i].isspace():
                    j = i
                    while j < len(line) and line[j].isspace():
                        j += 1
                    tokens.append(("", line[i:j]))
                    i = j
                    continue

                if line[i] == '"':
                    j = i + 1
                    while j < len(line) and line[j] != '"':
                        j += 1
                    if j < len(line):
                        j += 1
                    tokens.append(("class:string", line[i:j]))
                    i = j
                    continue

                if line[i] == "#":
                    tokens.append(("class:comment", line[i:]))
                    break

                color_found = False
                color_map = [
                    (":green:", "class:color-green", 7),
                    (":red:", "class:color-red", 5),
                    (":blue:", "class:color-blue", 6),
                    (":yellow:", "class:color-yellow", 7),
                    (":cyan:", "class:color-cyan", 6),
                    (":magenta:", "class:color-magenta", 9),
                    (":white:", "class:color-white", 7),
                    (":black:", "class:color-black", 7),
                ]
                for color, style, length in color_map:
                    if line[i:i+length] == color:
                        tokens.append((style, color))
                        i += length
                        color_found = True
                        break
                if color_found:
                    continue

                if line[i:i+6] == "[box]":
                    tokens.append(("class:box", "[box]"))
                    i += 6
                    continue

                j = i
                while j < len(line) and not line[j].isspace() and line[j] != '"' and line[j] != ":" and line[j] != "[":
                    j += 1
                word = line[i:j]
                if word in EASY_KEYWORDS:
                    tokens.append(("class:keyword", word))
                else:
                    tokens.append(("", word))
                i = j

            return tokens

        return get_line


style = Style.from_dict({
    "status": "bg:#000000 #ffffff",
    "line-number": "#888888",
    "comment": "#666666",
    "string": "#ffa500",
    "keyword": "#00ffff",
    "box": "#ff00ff",
    "color-green": "#00ff00",
    "color-red": "#ff0000",
    "color-blue": "#0000ff",
    "color-yellow": "#ffff00",
    "color-cyan": "#00ffff",
    "color-magenta": "#ff00ff",
    "color-white": "#ffffff",
    "color-black": "#000000",
})


def edit_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = ""

    buffer = Buffer()
    buffer.text = text

    lexer = EasyLexer()
    variables = set()

    def extract_variables():
        nonlocal variables
        variables = set()
        for line in buffer.text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) >= 2 and parts[0] == "set":
                variables.add(parts[1])

    def get_line_numbers():
        lines = buffer.text.splitlines()
        line_count = len(lines)
        current_line = buffer.document.cursor_position_row
        result = []
        for i in range(1, line_count + 1):
            if i == current_line + 1:
                result.append(("class:line-number-active", f"{i:3d} "))
            else:
                result.append(("class:line-number", f"{i:3d} "))
        return result

    def get_statusbar():
        return [("class:status", f" Easy Editor | {path} | Ln {buffer.document.cursor_position_row + 1}, Col {buffer.document.cursor_position_col + 1} | Ctrl+S Save | Ctrl+Q Quit ")]

    extract_variables()
    completer = EasyCompleter(sorted(variables))

    def on_text_changed(_):
        extract_variables()
        completer.variables = sorted(variables)
        line_numbers_control.text = get_line_numbers()
        statusbar_control.text = get_statusbar()

    line_numbers_control = FormattedTextControl(get_line_numbers)
    editor_control = BufferControl(buffer=buffer, lexer=lexer)
    statusbar_control = FormattedTextControl(get_statusbar)

    root_container = HSplit([
        VSplit([
            Window(content=line_numbers_control, width=4, style="class:line-number"),
            Window(content=editor_control, wrap_lines=True),
        ]),
        Window(content=statusbar_control, height=1, style="class:status"),
    ])

    kb = KeyBindings()

    @kb.add("c-s")
    def save(_):
        with open(path, "w", encoding="utf-8") as f:
            f.write(buffer.text)
        on_text_changed(None)

    @kb.add("c-q")
    def quit(_):
        from prompt_toolkit.application import get_app
        get_app().exit()

    from prompt_toolkit.application import Application
    application = Application(
        layout=Layout(root_container, focused_element=editor_control),
        key_bindings=kb,
        style=style,
        full_screen=True,
        mouse_support=True,
        after_render=on_text_changed,
    )

    application.run()
