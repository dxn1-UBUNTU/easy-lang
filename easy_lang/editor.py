import os
import re
from prompt_toolkit import PromptSession
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Window, HSplit, VSplit, FormattedTextControl, Layout, FloatContainer, Float
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding.vi_state import InputMode, ViState
from prompt_toolkit.filters import Condition
from prompt_toolkit.search import SearchState
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.widgets import TextArea


EASY_KEYWORDS = [
    "say",
    "set",
    "add",
    "sub",
    "easy",
    "if",
    "for",
    "while",
    "func",
    "return",
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
    ":bright_black:",
    ":bright_red:",
    ":bright_green:",
    ":bright_yellow:",
    ":bright_blue:",
    ":bright_magenta:",
    ":bright_cyan:",
    ":bright_white:",
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

EASY_BUILTINS = [
    "len(",
    "upper(",
    "lower(",
    "trim(",
    "split(",
    "join(",
    "replace(",
    "contains(",
    "startswith(",
    "endswith(",
    "math(",
    "random(",
    "now(",
    "date(",
    "time(",
    "sleep(",
    "read(",
    "write(",
    "append(",
    "exists(",
    "delete(",
    "listdir(",
    "exec(",
    "env(",
    "hash(",
    "base64(",
    "decode(",
    "http(",
]

EASY_DOCS = {
    "say": "say \"text\" [component] :color: - Print text to terminal",
    "set": "set name value - Store a value in a variable",
    "add": "add name value - Add to a number variable",
    "sub": "sub name value - Subtract from a number variable",
    "easy": "easy [api-call]<service>(...) - Call external services",
    "if": "if condition - Conditional block",
    "for": "for item in list - Loop over items",
    "while": "while condition - Loop while condition is true",
    "func": "func name(args) - Define a function",
    "return": "return value - Return from function",
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
    "len(": "len(text) - Get string length",
    "upper(": "upper(text) - Convert to uppercase",
    "lower(": "lower(text) - Convert to lowercase",
    "trim(": "trim(text) - Remove whitespace",
    "split(": "split(text, sep) - Split string into list",
    "join(": "join(list, sep) - Join list into string",
    "replace(": "replace(text, old, new) - Replace substring",
    "contains(": "contains(text, sub) - Check if text contains substring",
    "startswith(": "startswith(text, sub) - Check if text starts with substring",
    "endswith(": "endswith(text, sub) - Check if text ends with substring",
    "math(": "math(\"expr\") - Evaluate math expression",
    "random(": "random(min, max) - Random number",
    "now(": "now() - Current ISO timestamp",
    "date(": "date() - Current date YYYY-MM-DD",
    "time(": "time() - Current time HH:MM:SS",
    "sleep(": "sleep(seconds) - Pause execution",
    "read(": "read(path) - Read file contents",
    "write(": "write(path, content) - Write to file",
    "append(": "append(path, content) - Append to file",
    "exists(": "exists(path) - Check if file exists",
    "delete(": "delete(path) - Delete file",
    "listdir(": "listdir(path) - List directory contents",
    "exec(": "exec(command) - Execute shell command",
    "env(": "env(variable) - Get environment variable",
    "hash(": "hash(text, algo) - Hash text",
    "base64(": "base64(text) - Encode to base64",
    "decode(": "decode(base64_text) - Decode from base64",
    "http(": "http(url, method) - Make HTTP request",
}


def fuzzy_score(query, candidate):
    query = query.lower()
    candidate = candidate.lower()
    if query == candidate:
        return 100
    if candidate.startswith(query):
        return 80
    if query in candidate:
        return 60
    score = 0
    qi = 0
    for ch in candidate:
        if qi < len(query) and ch == query[qi]:
            score += 10
            qi += 1
    return score if qi == len(query) else 0


class EasyCompleter(Completer):
    def __init__(self, variables=None):
        self.variables = variables or []

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor(WORD=True)
        line = document.current_line
        stripped = line.strip()
        lower_word = word.lower()

        if not stripped:
            scored = [(fuzzy_score(lower_word, kw), kw) for kw in EASY_KEYWORDS]
            for score, kw in sorted(scored, reverse=True):
                if score > 0:
                    yield Completion(kw, start_position=-len(word) or 0, display=kw, display_meta=EASY_DOCS.get(kw, ""), style="bg:#1e1e1e #ffffff")
            return

        parts = stripped.split()
        command = parts[0].lower() if parts else ""

        if command in ("say",):
            if stripped.lower().endswith(" ") or stripped.lower().startswith("say "):
                candidates = EASY_COMPONENTS + EASY_COLORS + list(self.variables)
                scored = [(fuzzy_score(lower_word, c), c) for c in candidates]
                for score, cand in sorted(scored, reverse=True):
                    if score > 0:
                        doc = EASY_DOCS.get(cand, "Variable" if cand in self.variables else "")
                        yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta=doc, style="bg:#1e1e1e #ffffff")
                return

        if command == "set":
            candidates = ["value"] + list(self.variables)
            scored = [(fuzzy_score(lower_word, c), c) for c in candidates]
            for score, cand in sorted(scored, reverse=True):
                if score > 0:
                    doc = "Literal value or variable" if cand == "value" else "Variable"
                    yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta=doc, style="bg:#1e1e1e #ffffff")
            return

        if command in ("add", "sub"):
            candidates = list(self.variables)
            scored = [(fuzzy_score(lower_word, c), c) for c in candidates]
            for score, cand in sorted(scored, reverse=True):
                if score > 0:
                    yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta="Variable", style="bg:#1e1e1e #ffffff")
            return

        if command == "easy":
            if len(parts) >= 2:
                sub = parts[1].lower()
                if sub.startswith("[api"):
                    yield Completion("[api-call]", start_position=-len(word) or 0, display="[api-call]", display_meta="Call an AI API", style="bg:#1e1e1e #ffffff")
                return

        all_options = EASY_KEYWORDS + EASY_COMPONENTS + EASY_COLORS + EASY_BUILTINS
        scored = [(fuzzy_score(lower_word, opt), opt) for opt in all_options]
        seen = set()
        for score, opt in sorted(scored, reverse=True):
            if opt not in seen and score > 0:
                seen.add(opt)
                yield Completion(opt, start_position=-len(word) or 0, display=opt, display_meta=EASY_DOCS.get(opt, ""), style="bg:#1e1e1e #ffffff")


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
    "status": "bg:#1e1e1e #ffffff",
    "line-number": "#858585",
    "line-number-active": "#ffffff",
    "comment": "#6a9955",
    "string": "#ce9178",
    "keyword": "#569cd6",
    "component-box": "#c586c0",
    "component-chat": "#4ec9b0",
    "component-sidebar": "#dcdcaa",
    "component-header": "#4fc1ff",
    "component-footer": "#c586c0",
    "component-alert": "#f44747",
    "component-list": "#4ec9b0",
    "component-table": "#4ec9b0",
    "component-hr": "#858585",
    "component-progress": "#4ec9b0",
    "component-spinner": "#dcdcaa",
    "component-input": "#4ec9b0",
    "component-align": "#858585",
    "component-padding": "#858585",
    "component-width": "#858585",
    "component-bg": "#858585",
    "style-bold": "bold",
    "style-dim": "#858585",
    "style-italic": "italic",
    "style-underline": "underline",
    "style-blink": "blink",
    "style-reverse": "reverse",
    "style-strikethrough": "#858585",
    "color-green": "#4ec9b0",
    "color-red": "#f44747",
    "color-blue": "#569cd6",
    "color-yellow": "#dcdcaa",
    "color-cyan": "#4ec9b0",
    "color-magenta": "#c586c0",
    "color-white": "#ffffff",
    "color-black": "#858585",
    "completion-menu.completion": "bg:#252526 #ffffff",
    "completion-menu.completion.current": "bg:#094771 #ffffff",
    "completion-menu.meta.completion": "bg:#252526 #858585",
    "completion-menu.meta.completion.current": "bg:#094771 #ffffff",
    "scrollbar.background": "bg:#1e1e1e",
    "scrollbar.button": "bg:#858585",
    "toolbar": "bg:#1e1e1e #cccccc",
    "toolbar.status": "bg:#1e1e1e #ffffff",
    "error": "#f44747",
    "warning": "#dcdcaa",
})


def edit_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = ""

    lexer = EasyLexer()
    variables = set()

    buffer = Buffer(complete_while_typing=True)
    buffer.text = text
    buffer.auto_suggest = AutoSuggestFromHistory()

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

    extract_variables()
    completer = EasyCompleter(sorted(variables))
    buffer.completer = completer

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

    def get_doc_text():
        if not buffer.complete_state:
            return []
        completion = buffer.complete_state.current_completion
        if not completion:
            return []
        doc = getattr(completion, "display_meta", None) or ""
        if not doc:
            return []
        lines = doc.splitlines()
        return [("class:toolbar", f" {lines[0]}" + (f"\n {' '.join(lines[1:])}" if len(lines) > 1 else ""))]

    def get_statusbar():
        mode = "INSERT"
        if vi_state.input_mode == InputMode.NAVIGATION:
            mode = "NAV"
        elif vi_state.input_mode == InputMode.REPLACE:
            mode = "REPLACE"
        line = buffer.document.cursor_position_row + 1
        col = buffer.document.cursor_position_col + 1
        total = len(buffer.text.splitlines())
        completion_info = ""
        if buffer.complete_state:
            completion = buffer.complete_state.current_completion
            if completion and getattr(completion, "display_meta", None):
                completion_info = f" | {completion.display_meta}"
        return [("class:status", f" Easy Editor | {path} | {mode} | Ln {line}/{total}, Col {col}{completion_info} | Tab Complete | Ctrl+S Save | Ctrl+Q Quit | Ctrl+/ Comment | F1 Docs ")]

    def get_toolbar():
        return [("class:toolbar", " Easy Lang | say set add sub easy if for while func return | [box] [chat] [sidebar] [header] [footer] [alert] [list] [table] [progress] [spinner] | :green: :red: :blue: :cyan: | len upper lower trim split join replace math random now date time read write exec env hash base64 http ")]

    extract_variables()
    completer = EasyCompleter(sorted(variables))

    def on_text_changed(_):
        extract_variables()
        completer.variables = sorted(variables)
        line_numbers_control.text = get_line_numbers()
        statusbar_control.text = get_statusbar()
        if docs_visible[0]:
            docs_control.text = get_doc_text()
        if not buffer.complete_state:
            buffer.start_completion(select_first=False)

    buffer.on_text_changed += on_text_changed

    line_numbers_control = FormattedTextControl(get_line_numbers)
    editor_kwargs = {
        "buffer": buffer,
        "lexer": lexer,
    }
    if "completer" in BufferControl.__init__.__code__.co_varnames:
        editor_kwargs["completer"] = completer
    if "complete_while_typing" in BufferControl.__init__.__code__.co_varnames:
        editor_kwargs["complete_while_typing"] = True
    editor_control = BufferControl(**editor_kwargs)
    statusbar_control = FormattedTextControl(get_statusbar)
    toolbar_control = FormattedTextControl(get_toolbar)

    root_container = HSplit([
        Window(content=toolbar_control, height=1, style="class:toolbar"),
        VSplit([
            Window(content=line_numbers_control, width=5, style="class:line-number"),
            Window(content=editor_control, wrap_lines=True),
        ]),
        Window(content=statusbar_control, height=1, style="class:status"),
    ])

    docs_visible = [False]

    docs_control = FormattedTextControl(get_doc_text)
    docs_window = Window(content=docs_control, height=Dimension(min=0, preferred=8), style="class:toolbar")
    root_container = FloatContainer(
        root_container,
        floats=[
            Float(
                content=docs_window,
                xcursor=True,
                ycursor=True,
                transparent=True,
            )
        ],
    )

    kb = KeyBindings()

    @kb.add("c-s")
    def save(_):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(buffer.text)
            on_text_changed(None)
        except Exception as e:
            print(f"Error saving: {e}", file=sys.stderr)

    @kb.add("c-q")
    def quit(_):
        from prompt_toolkit.application import get_app
        get_app().exit()

    @kb.add("c-_")
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
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_next()
            docs_control.text = get_doc_text()
        else:
            buffer.insert_text("    ")

    @kb.add("s-tab")
    def shift_tab(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_previous()
            docs_control.text = get_doc_text()
        else:
            buffer.start_completion(select_first=False)

    @kb.add("right")
    def right_complete(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_next()
            docs_control.text = get_doc_text()
        else:
            buffer.cursor_right()

    @kb.add("left")
    def left_complete(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_previous()
            docs_control.text = get_doc_text()
        else:
            buffer.cursor_left()

    @kb.add("up")
    def up_complete(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_previous()
            docs_control.text = get_doc_text()
        else:
            buffer.cursor_up()

    @kb.add("down")
    def down_complete(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_next()
            docs_control.text = get_doc_text()
        else:
            buffer.cursor_down()

    @kb.add("backspace")
    def backspace(_):
        buffer.delete_before_cursor()

    @kb.add("backspace")
    def backspace(_):
        buffer.delete_before_cursor()

    @kb.add("c-space")
    def trigger_completion(_):
        from prompt_toolkit.application import get_app
        get_app().current_buffer.start_completion(select_first=False)

    @kb.add("f1")
    def show_docs(_):
        docs_visible[0] = True
        docs_control.text = get_doc_text()

    @kb.add("c-h")
    def hide_docs(_):
        docs_visible[0] = False
        docs_control.text = get_doc_text()

    @kb.add("escape")
    def hide_docs_escape(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if docs_visible[0]:
            docs_visible[0] = False
            docs_control.text = get_doc_text()
        elif app.current_buffer.complete_state:
            app.current_buffer.complete_state = None

    @kb.add("enter")
    def smart_enter(_):
        doc = buffer.document
        line = doc.current_line
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            buffer.insert_text("\n")
            return
        indent = len(line) - len(stripped)
        buffer.insert_text("\n" + " " * indent)
        if stripped.endswith(":"):
            buffer.insert_text("    ")

    @kb.add("c-z")
    def undo(_):
        buffer.undo()

    @kb.add("c-y")
    def redo(_):
        buffer.redo()

    @kb.add("c-d")
    def delete_line(_):
        doc = buffer.document
        start = doc.get_start_of_line_position()
        end = doc.get_end_of_line_position()
        buffer.delete(start, end + 1)

    @kb.add("c-a")
    def select_all(_):
        buffer.selection.set_document(buffer.document)

    @kb.add("c-c")
    def copy(_):
        data = buffer.selection.copy()
        if data:
            from prompt_toolkit.clipboard import Clipboard
            clipboard = Clipboard()
            clipboard.set_data(data)

    @kb.add("c-v")
    def paste(_):
        from prompt_toolkit.clipboard import Clipboard
        clipboard = Clipboard()
        data = clipboard.get_data()
        if data:
            buffer.insert_text(data)

    @kb.add("c-x")
    def cut(_):
        data = buffer.selection.copy()
        if data:
            buffer.delete_selection()
            from prompt_toolkit.clipboard import Clipboard
            clipboard = Clipboard()
            clipboard.set_data(data)

    from prompt_toolkit.application import Application
    from prompt_toolkit.key_binding.vi_state import ViState
    from prompt_toolkit.enums import EditingMode
    global vi_state
    vi_state = ViState()

    application = Application(
        layout=Layout(root_container, focused_element=editor_control),
        key_bindings=kb,
        style=style,
        full_screen=True,
        mouse_support=True,
        after_render=on_text_changed,
        editing_mode=EditingMode.EMACS,
    )

    on_text_changed(None)
    application.run()
