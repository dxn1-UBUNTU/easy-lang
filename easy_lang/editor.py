import os
from prompt_toolkit import PromptSession
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Window, HSplit, VSplit, FormattedTextControl, Layout
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding.vi_state import InputMode, ViState
from prompt_toolkit.filters import Condition


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

EASY_COMPONENTS = [
    "[box]",
    "[box:double]",
    "[box:rounded]",
    "[box:bold]",
    "[chat:left]",
    "[chat:right]",
    "[sidebar]",
    "[header]",
    "[footer]",
    "[alert]",
    "[list]",
    "[table]",
    "[hr]",
    "[progress:50]",
    "[spinner]",
    "[input:prompt]",
    "[align:center]",
    "[bold]",
    "[dim]",
    "[underline]",
    "[italic]",
    "[reverse]",
    "[padding:2]",
    "[width:40]",
    "[bg:blue]",
]

EASY_DOCS = {
    "say": "say \"text\" [component] :color: - Print text to terminal",
    "set": "set name value - Store a value in a variable",
    "add": "add name value - Add to a number variable",
    "sub": "sub name value - Subtract from a number variable",
    "[box]": "[box] - Wrap text in a single-line box",
    "[box:double]": "[box:double] - Wrap text in a double-line box",
    "[box:rounded]": "[box:rounded] - Wrap text in a rounded box",
    "[box:bold]": "[box:bold] - Wrap text in a bold box",
    "[chat:left]": "[chat:left] - Left-aligned chat bubble",
    "[chat:right]": "[chat:right] - Right-aligned chat bubble",
    "[sidebar]": "[sidebar] - Vertical sidebar panel",
    "[header]": "[header] - Bold header bar",
    "[footer]": "[footer] - Bold footer bar",
    "[alert]": "[alert] - Warning/error alert line",
    "[list]": "[list] - Bullet list item",
    "[table]": "[table] - Table row",
    "[hr]": "[hr] - Horizontal rule",
    "[progress:50]": "[progress:50] - Progress bar (0-100)",
    "[spinner]": "[spinner] - Animated spinner",
    "[input:prompt]": "[input:prompt] - Text input prompt",
    "[align:center]": "[align:center] - Center align text",
    "[bold]": "[bold] - Bold text style",
    "[dim]": "[dim] - Dim text style",
    "[underline]": "[underline] - Underline text style",
    "[italic]": "[italic] - Italic text style",
    "[reverse]": "[reverse] - Reverse video style",
    "[padding:2]": "[padding:2] - Add padding inside box",
    "[width:40]": "[width:40] - Set component width",
    "[bg:blue]": "[bg:blue] - Set background color",
    ":green:": ":green: - Green foreground color",
    ":red:": ":red: - Red foreground color",
    ":blue:": ":blue: - Blue foreground color",
    ":yellow:": ":yellow: - Yellow foreground color",
    ":cyan:": ":cyan: - Cyan foreground color",
    ":magenta:": ":magenta: - Magenta foreground color",
    ":white:": ":white: - White foreground color",
    ":black:": ":black: - Black foreground color",
}


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
                yield Completion(kw, start_position=-len(word) or 0, display=kw, doc=EASY_DOCS.get(kw, ""))
            return

        parts = stripped.split()
        command = parts[0].lower() if parts else ""

        if command in ("say",):
            if lower_stripped.endswith(" ") or lower_stripped.lower().startswith("say "):
                for component in EASY_COMPONENTS:
                    yield Completion(component, start_position=-len(word) or 0, display=component, doc=EASY_DOCS.get(component, ""))
                for color in EASY_COLORS:
                    yield Completion(color, start_position=-len(word) or 0, display=color, doc=EASY_DOCS.get(color, ""))
                for var in self.variables:
                    yield Completion(var, start_position=-len(word) or 0, display=var, doc="Variable")

        if command == "set":
            if len(parts) == 2:
                yield Completion("value", start_position=-len(word) or 0, display="value", doc="Literal value or variable")
            elif len(parts) >= 3:
                for var in self.variables:
                    yield Completion(var, start_position=-len(word) or 0, display=var, doc="Variable")

        if command in ("add", "sub"):
            if len(parts) == 2:
                for var in self.variables:
                    yield Completion(var, start_position=-len(word) or 0, display=var, doc="Variable")
            elif len(parts) >= 3:
                for var in self.variables:
                    yield Completion(var, start_position=-len(word) or 0, display=var, doc="Variable")

        if not command or command not in set(EASY_KEYWORDS):
            for kw in EASY_KEYWORDS:
                if kw.startswith(word):
                    yield Completion(kw, start_position=-len(word), display=kw, doc=EASY_DOCS.get(kw, ""))


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

                component_found = False
                component_map = [
                    ("[box]", "class:component-box", 6),
                    ("[box:double]", "class:component-box", 12),
                    ("[box:rounded]", "class:component-box", 13),
                    ("[box:bold]", "class:component-box", 10),
                    ("[chat:left]", "class:component-chat", 11),
                    ("[chat:right]", "class:component-chat", 12),
                    ("[sidebar]", "class:component-sidebar", 9),
                    ("[header]", "class:component-header", 8),
                    ("[footer]", "class:component-footer", 8),
                    ("[alert]", "class:component-alert", 7),
                    ("[list]", "class:component-list", 6),
                    ("[table]", "class:component-table", 7),
                    ("[hr]", "class:component-hr", 4),
                    ("[progress:", "class:component-progress", 10),
                    ("[spinner]", "class:component-spinner", 9),
                    ("[input:", "class:component-input", 7),
                    ("[align:", "class:component-align", 7),
                    ("[padding:", "class:component-padding", 9),
                    ("[width:", "class:component-width", 7),
                    ("[bg:", "class:component-bg", 4),
                    ("[bold]", "class:style-bold", 6),
                    ("[dim]", "class:style-dim", 5),
                    ("[italic]", "class:style-italic", 8),
                    ("[underline]", "class:style-underline", 11),
                    ("[blink]", "class:style-blink", 7),
                    ("[reverse]", "class:style-reverse", 9),
                    ("[strikethrough]", "class:style-strikethrough", 15),
                ]
                for comp, style, length in component_map:
                    if line[i:i+length].lower() == comp:
                        tokens.append((style, comp if comp.startswith("[") else comp + "]"))
                        i += length
                        component_found = True
                        break
                    elif comp.startswith("[") and line[i:i+length].lower().startswith(comp[:-1]):
                        tokens.append((style, line[i:i+length]))
                        i += length
                        component_found = True
                        break
                if component_found:
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
    "line-number-active": "#ffff00",
    "comment": "#666666",
    "string": "#ffa500",
    "keyword": "#00ffff",
    "component-box": "#ff00ff",
    "component-chat": "#00ff00",
    "component-sidebar": "#ffff00",
    "component-header": "#0000ff",
    "component-footer": "#ff00ff",
    "component-alert": "#ff0000",
    "component-list": "#00ffff",
    "component-table": "#00ffff",
    "component-hr": "#888888",
    "component-progress": "#00ff00",
    "component-spinner": "#ffff00",
    "component-input": "#00ffff",
    "component-align": "#888888",
    "component-padding": "#888888",
    "component-width": "#888888",
    "component-bg": "#888888",
    "style-bold": "bold",
    "style-dim": "#666666",
    "style-italic": "italic",
    "style-underline": "underline",
    "style-blink": "blink",
    "style-reverse": "reverse",
    "style-strikethrough": "#666666",
    "color-green": "#00ff00",
    "color-red": "#ff0000",
    "color-blue": "#0000ff",
    "color-yellow": "#ffff00",
    "color-cyan": "#00ffff",
    "color-magenta": "#ff00ff",
    "color-white": "#ffffff",
    "color-black": "#000000",
    "completion-menu.completion": "bg:#000000 #ffffff",
    "completion-menu.completion.current": "bg:#444444 #ffffff",
    "completion-menu.meta.completion": "bg:#000000 #888888",
    "completion-menu.meta.completion.current": "bg:#444444 #ffffff",
    "scrollbar.background": "bg:#000000",
    "scrollbar.button": "bg:#888888",
    "toolbar": "bg:#000000 #ffffff",
    "toolbar.status": "bg:#000000 #ffff00",
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
        mode = "INSERT"
        if vi_state.input_mode == InputMode.NAVIGATION:
            mode = "NAV"
        elif vi_state.input_mode == InputMode.REPLACE:
            mode = "REPLACE"
        return [("class:status", f" Easy Editor | {path} | {mode} | Ln {buffer.document.cursor_position_row + 1}, Col {buffer.document.cursor_position_col + 1} | Tab/Arrows Autocomplete | Ctrl+S Save | Ctrl+Q Quit | Ctrl+/ Comment ")]

    def get_toolbar():
        return [("class:toolbar", " Easy Lang Editor | Components: [box] [chat:left] [header] [sidebar] [footer] [alert] [list] [table] [progress:50] [spinner] | Colors: :green: :red: :blue: :cyan: | Styles: [bold] [dim] [underline] [italic] ")]

    extract_variables()
    completer = EasyCompleter(sorted(variables))

    def on_text_changed(_):
        extract_variables()
        completer.variables = sorted(variables)
        line_numbers_control.text = get_line_numbers()
        statusbar_control.text = get_statusbar()

    line_numbers_control = FormattedTextControl(get_line_numbers)
    editor_control = BufferControl(buffer=buffer, lexer=lexer, completer=completer, complete_while_typing=True)
    statusbar_control = FormattedTextControl(get_statusbar)
    toolbar_control = FormattedTextControl(get_toolbar)

    root_container = HSplit([
        Window(content=toolbar_control, height=1, style="class:toolbar"),
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

    @kb.add("c-slash")
    def comment(_):
        doc = buffer.document
        line = doc.current_line
        if line.strip().startswith("#"):
            new_line = line.replace("#", "", 1)
        else:
            new_line = "#" + line
        buffer.delete_line_below_cursor()
        buffer.insert_line_above()
        buffer.insert_text(new_line)

    @kb.add("tab")
    def tab_complete(_):
        from prompt_toolkit.key_binding.vi_state import ViState
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_next()
        else:
            app.current_buffer.start_completion(select_first=False)

    @kb.add("right")
    def right_complete(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_next()
        else:
            buffer.cursor_right()

    @kb.add("left")
    def left_complete(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_previous()
        else:
            buffer.cursor_left()

    @kb.add("up")
    def up_complete(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_previous()
        else:
            buffer.cursor_up()

    @kb.add("down")
    def down_complete(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_next()
        else:
            buffer.cursor_down()

    @kb.add("c-space")
    def trigger_completion(_):
        from prompt_toolkit.application import get_app
        get_app().current_buffer.start_completion(select_first=False)

    from prompt_toolkit.application import Application
    from prompt_toolkit.vi_state import ViState
    global vi_state
    vi_state = ViState()

    application = Application(
        layout=Layout(root_container, focused_element=editor_control),
        key_bindings=kb,
        style=style,
        full_screen=True,
        mouse_support=True,
        after_render=on_text_changed,
        vi_mode=True,
    )

    on_text_changed(None)
    application.run()
