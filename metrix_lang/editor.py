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
from prompt_toolkit.formatted_text import HTML, to_formatted_text
from prompt_toolkit.key_binding.vi_state import InputMode, ViState
from prompt_toolkit.filters import Condition
from prompt_toolkit.search import SearchState
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.menus import CompletionsMenu

from metrix_lang.interpreter import EasyError, run, strip_ansi


EASY_KEYWORDS = [
    "say",
    "row",
    "set",
    "let",
    "ask",
    "select",
    "clear",
    "add",
    "sub",
    "metrix",
    "if",
    "for",
    "while",
    "func",
    "return",
]

EASY_METHODS = [
    "len",
    "upper",
    "lower",
    "trim",
    "split",
    "join",
    "replace",
    "contains",
    "startswith",
    "endswith",
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
    "[box:dotted]",
    "[chat:left]",
    "[chat:right]",
    "[sidebar]",
    "[header]",
    "[footer]",
    "[alert]",
    "[badge]",
    "[code]",
    "[list]",
    "[table]",
    "[hr]",
    "[progress:50]",
    "[spinner]",
    "[input:prompt]",
    "[align:center]",
    "[align:left]",
    "[align:right]",
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
    "get(",
    "keys(",
    "values(",
    "count(",
    "title(",
    "slug(",
    "sort(",
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
    "json(",
    "hash(",
    "base64(",
    "decode(",
    "http(",
    "first(",
    "last(",
    "reverse(",
    "unique(",
    "slice(",
    "index(",
    "find(",
    "flatten(",
    "stringify(",
    "number(",
    "string(",
    "boolean(",
    "repeat(",
    "pad(",
    "urlencode(",
    "urldecode(",
    "uuid(",
]

EASY_API_SERVICES = [
    "gemini",
    "openai",
    "huggingface",
    "anthropic",
    "cohere",
    "ollama",
    "http",
    "get",
    "keys",
    "values",
    "count",
    "title",
    "slug",
    "sort",
]

EASY_HTTP_METHODS = [
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
    "HEAD",
    "OPTIONS",
]

EASY_MATH_FUNCTIONS = [
    "sqrt",
    "pow",
    "abs",
    "min",
    "max",
    "round",
    "sum",
    "floor",
    "ceil",
    "log",
    "exp",
    "sin",
    "cos",
    "tan",
    "pi",
    "e",
]

EASY_HASH_ALGOS = [
    "md5",
    "sha1",
    "sha256",
    "sha512",
]

EASY_SNIPPETS = {
    "say": 'say "$1"',
    "row": 'row "$1" | "$2" [left:28]',
    "set": 'set $1 "$2"',
    "let": 'let $1 "$2"',
    "ask": 'ask $1 "$2"',
    "select": 'select $1 "$2" from ["one", "two"]',
    "clear": "clear",
    "if": "if $1:\n    $2",
    "for": "for $1 in $2:\n    $3",
    "while": "while $1:\n    $2",
    "func": "func $1($2):\n    $3",
    "metrix": 'metrix [api-call]<$1>($2)',
    "[box]": "[box] $1",
    "[box:double]": "[box:double] $1",
    "[box:rounded]": "[box:rounded] $1",
    "[box:bold]": "[box:bold] $1",
    "[chat:left]": "[chat:left] $1",
    "[chat:right]": "[chat:right] $1",
    "[sidebar]": "[sidebar] $1",
    "[header]": "[header] $1",
    "[footer]": "[footer] $1",
    "[alert]": "[alert] $1",
    "[list]": "[list] $1",
    "[table]": "[table] $1",
    "[progress:50]": "[progress:50] $1",
    "[spinner]": "[spinner] $1",
    "[input:prompt]": "[input:prompt] $1",
    "[align:center]": "[align:center] $1",
    "[padding:2]": "[padding:2] $1",
    "[width:40]": "[width:40] $1",
    "[bg:blue]": "[bg:blue] $1",
    "[bold]": "[bold] $1",
    "[dim]": "[dim] $1",
    "[italic]": "[italic] $1",
    "[underline]": "[underline] $1",
    "[reverse]": "[reverse] $1",
    "[strikethrough]": "[strikethrough] $1",
    ":green:": ":green: $1",
    ":red:": ":red: $1",
    ":blue:": ":blue: $1",
    ":yellow:": ":yellow: $1",
    ":cyan:": ":cyan: $1",
    ":magenta:": ":magenta: $1",
    ":white:": ":white: $1",
    ":black:": ":black: $1",
    "len(": 'len($1)',
    "upper(": 'upper($1)',
    "lower(": 'lower($1)',
    "trim(": 'trim($1)',
    "split(": 'split($1, $2)',
    "join(": 'join($1, $2)',
    "replace(": 'replace($1, $2, $3)',
    "math(": 'math("$1")',
    "random(": 'random($1, $2)',
    "read(": 'read("$1")',
    "write(": 'write("$1", "$2")',
    "http(": 'http("$1", $2)',
}

EASY_DOCS = {
    "say": "say \"text\" [component] :color: - Print text to terminal",
    "row": "row left | right [left:28] - Render a two-pane workspace row",
    "set": "set name value - Store a value in a variable",
    "let": "let name value - Alias for set",
    "ask": "ask name \"Prompt\" - Read input into a variable",
    "select": "select name \"Prompt\" from [items] - Choose from a list",
    "clear": "clear - Clear the terminal before rendering the next view",
    "add": "add name value - Add to a number variable",
    "sub": "sub name value - Subtract from a number variable",
    "metrix": "metrix [api-call]<service>(...) - Call external services",
    "if": "if condition - Conditional block",
    "for": "for item in list - Loop over items",
    "while": "while condition - Loop while condition is true",
    "func": "func name(args) - Define a function",
    "return": "return value - Return from function",
    "[box]": "[box] - Wrap text in a single-line box",
    "[box:double]": "[box:double] - Wrap text in a double-line box",
    "[box:rounded]": "[box:rounded] - Wrap text in a rounded box",
    "[box:bold]": "[box:bold] - Wrap text in a bold box",
    "[box:dotted]": "[box:dotted] - Wrap text in a dotted box",
    "[chat:left]": "[chat:left] - Left-aligned chat bubble",
    "[chat:right]": "[chat:right] - Right-aligned chat bubble",
    "[sidebar]": "[sidebar] - Vertical sidebar panel",
    "[header]": "[header] - Bold header bar",
    "[footer]": "[footer] - Bold footer bar",
    "[alert]": "[alert] - Warning/error alert line",
    "[badge]": "[badge] - Compact label for status and metadata",
    "[code]": "[code] - Dotted code/output panel",
    "[list]": "[list] - Bullet list item",
    "[table]": "[table] - Table row",
    "[hr]": "[hr] - Horizontal rule",
    "[progress:50]": "[progress:50] - Progress bar (0-100)",
    "[spinner]": "[spinner] - Animated spinner",
    "[input:prompt]": "[input:prompt] - Text input prompt",
    "[align:center]": "[align:center] - Center align text",
    "[align:left]": "[align:left] - Left align text",
    "[align:right]": "[align:right] - Right align text",
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
    "get(": "get(data, key, default) - Read a map key or list item",
    "keys(": "keys(map) - List map keys",
    "values(": "values(map) - List map values",
    "count(": "count(value) - Count items or characters",
    "title(": "title(text) - Title-case text",
    "slug(": "slug(text) - Convert text to a URL-friendly slug",
    "sort(": "sort(list) - Sort a list",
    "first(": "first(list) - Get the first item, or empty text",
    "last(": "last(list) - Get the last item, or empty text",
    "reverse(": "reverse(value) - Reverse a list or string",
    "unique(": "unique(list) - Remove duplicate list items",
    "slice(": "slice(value, start, end) - Take part of a list or string",
    "index(": "index(list, item) - Position of an item, or -1",
    "find(": "find(text, query) - Position of text, or -1",
    "flatten(": "flatten(list) - Flatten one level of nested lists",
    "stringify(": "stringify(value) - Encode data as JSON text",
    "number(": "number(value) - Convert text to a number",
    "string(": "string(value) - Convert any value to text",
    "boolean(": "boolean(value) - Convert a value to true or false",
    "repeat(": "repeat(text, times) - Repeat text",
    "pad(": "pad(text, width, side) - Pad text left, right, or center",
    "urlencode(": "urlencode(text) - URL encode text",
    "urldecode(": "urldecode(text) - Decode URL text",
    "uuid(": "uuid() - Make a random UUID",
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


def fuzzy_score_vscode(query, candidate):
    q = query.lower()
    c = candidate.lower()
    # Empty input is a browse state: show all options instead of an empty menu.
    if not q:
        return 1
    if q == c:
        return 100
    if c.startswith(q):
        return 90
    qlen = len(q)
    clen = len(c)
    if qlen > clen:
        q_idx = 0
        consecutive = 0
        max_consecutive = 0
        score = 0
        for i, ch in enumerate(c):
            if q_idx < qlen and ch == q[q_idx]:
                score += 1
                q_idx += 1
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0
        if q_idx != qlen:
            return 0
        score = score * 2 + max_consecutive * 5
        if c.find(q) != -1:
            score += 10
        return score
    q_idx = 0
    consecutive = 0
    max_consecutive = 0
    score = 0
    for i, ch in enumerate(c):
        if q_idx < qlen and ch == q[q_idx]:
            score += 1
            q_idx += 1
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0
    if q_idx != qlen:
        return 0
    score = score * 2 + max_consecutive * 5
    if c.find(q) != -1:
        score += 10
    return score


COMPLETION_KINDS = {
    "keyword": "keyword",
    "component": "component",
    "color": "color",
    "builtin": "function",
    "variable": "variable",
    "snippet": "snippet",
}


class EasyCompleter(Completer):
    def __init__(self, variables=None, functions=None):
        self.variables = variables or []
        self.functions = functions or []

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor(WORD=True)
        line = document.current_line
        stripped = line.strip()
        lower_word = word.lower()

        if not stripped:
            # A new line is the command palette.  Show the full language
            # catalogue, not merely a handful of starter keywords.
            candidates = (
                [(item, "keyword") for item in EASY_KEYWORDS]
                + [(item, "component") for item in EASY_COMPONENTS]
                + [(item, "color") for item in EASY_COLORS]
                + [(item, "builtin") for item in EASY_BUILTINS]
            )
            scored = [(fuzzy_score_vscode(lower_word, item), item, kind) for item, kind in candidates]
            for score, item, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                if score > 0:
                    yield Completion(item, start_position=-len(word) or 0, display=item, display_meta=EASY_DOCS.get(item, ""), style="bg:#1e1e1e #ffffff")
            return

        if word.endswith("."):
            method_name = word[:-1].lower()
            candidates = [(m, "method") for m in EASY_METHODS]
            if not method_name:
                for method, kind in candidates:
                    yield Completion(method, start_position=-1, display=method, display_meta=EASY_DOCS.get(method, f"String method: {method}()"), style="bg:#1e1e1e #ffffff")
                return
            scored = [(fuzzy_score_vscode(method_name, m), m, kind) for m, kind in candidates]
            for score, method, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                if score > 0:
                    yield Completion(method, start_position=-len(method_name) or 0, display=method, display_meta=EASY_DOCS.get(method, f"String method: {method}()"), style="bg:#1e1e1e #ffffff")
            if not any(True for _ in []):
                for method, kind in candidates:
                    yield Completion(method, start_position=-len(method_name) or 0, display=method, display_meta=EASY_DOCS.get(method, f"String method: {method}()"), style="bg:#1e1e1e #ffffff")
            return

        if word == '"' or word == "'":
            candidates = [(v, "variable") for v in self.variables] + [(b, "builtin") for b in EASY_BUILTINS]
            for cand, kind in candidates:
                doc = EASY_DOCS.get(cand, "Variable" if cand in self.variables else "")
                yield Completion(cand, start_position=0, display=cand, display_meta=doc, style="bg:#1e1e1e #ffffff")
            return

        prefix = line[:document.cursor_position_col]
        parts = prefix.split()
        command = parts[0].lower() if parts else ""
        after_command = prefix[len(command):].strip() if command else ""

        if command == "say":
            if after_command or line.lower().startswith("say "):
                candidates = [(c, "component" if c.startswith("[") else "color" if c.startswith(":") else "variable") for c in (EASY_COMPONENTS + EASY_COLORS + list(self.variables))]
                scored = [(fuzzy_score_vscode(lower_word, c), c, kind) for c, kind in candidates]
                for score, cand, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                    if score > 0:
                        doc = EASY_DOCS.get(cand, "Variable" if cand in self.variables else "")
                        yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta=doc, style="bg:#1e1e1e #ffffff")
                return

        if command == "set":
            if after_command or line.lower().startswith("set "):
                candidates = [("value", "snippet")] + [(v, "variable") for v in self.variables]
                scored = [(fuzzy_score_vscode(lower_word, c), c, kind) for c, kind in candidates]
                for score, cand, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                    if score > 0:
                        doc = "Literal value or variable" if cand == "value" else "Variable"
                        yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta=doc, style="bg:#1e1e1e #ffffff")
                return

        if command in ("add", "sub"):
            if after_command or line.lower().startswith(f"{command} "):
                candidates = [(v, "variable") for v in self.variables]
                scored = [(fuzzy_score_vscode(lower_word, c), c, kind) for c, kind in candidates]
                for score, cand, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                    if score > 0:
                        yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta="Variable", style="bg:#1e1e1e #ffffff")
                return

        if command == "for":
            if after_command or line.lower().startswith("for "):
                candidates = [("item", "snippet")] + [(v, "variable") for v in self.variables]
                scored = [(fuzzy_score_vscode(lower_word, c), c, kind) for c, kind in candidates]
                for score, cand, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                    if score > 0:
                        doc = "Loop variable" if cand == "item" else "Variable"
                        yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta=doc, style="bg:#1e1e1e #ffffff")
                return

        if command == "if":
            if after_command or line.lower().startswith("if "):
                candidates = ["condition"]
                scored = [(fuzzy_score_vscode(lower_word, c), c, "keyword") for c in candidates]
                for score, cand, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                    if score > 0:
                        yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta="Condition expression", style="bg:#1e1e1e #ffffff")
                return

        if command == "while":
            if after_command or line.lower().startswith("while "):
                candidates = ["condition"]
                scored = [(fuzzy_score_vscode(lower_word, c), c, "keyword") for c in candidates]
                for score, cand, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                    if score > 0:
                        yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta="Condition expression", style="bg:#1e1e1e #ffffff")
                return

        if command == "func":
            if after_command or line.lower().startswith("func "):
                candidates = [("name", "snippet")]
                scored = [(fuzzy_score_vscode(lower_word, c), c, kind) for c, kind in candidates]
                for score, cand, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                    if score > 0:
                        yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta="Function name", style="bg:#1e1e1e #ffffff")
                return

        if command == "return":
            if after_command or line.lower().startswith("return "):
                candidates = [("value", "snippet")] + [(v, "variable") for v in self.variables]
                scored = [(fuzzy_score_vscode(lower_word, c), c, kind) for c, kind in candidates]
                for score, cand, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                    if score > 0:
                        doc = "Return value" if cand == "value" else "Variable"
                        yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta=doc, style="bg:#1e1e1e #ffffff")
                return

        if command == "metrix":
            if after_command or line.lower().startswith("metrix "):
                sub = parts[1].lower() if len(parts) > 1 else ""
                if sub.startswith("[api"):
                    angle_index = prefix.find("<")
                    if angle_index != -1 and ">" not in prefix[angle_index:]:
                        candidates = [(s, "api") for s in EASY_API_SERVICES]
                        for service, kind in candidates:
                            yield Completion(service, start_position=-len(word) or 0, display=service, display_meta="API service", style="bg:#1e1e1e #ffffff")
                    else:
                        yield Completion("[api-call]", start_position=-len(word) or 0, display="[api-call]", display_meta="Call an AI API", style="bg:#1e1e1e #ffffff")
                else:
                    yield Completion("[api-call]", start_position=-len(word) or 0, display="[api-call]", display_meta="Call an AI API", style="bg:#1e1e1e #ffffff")
                return

        if stripped.startswith(":") and not stripped.endswith(":"):
            candidates = [(c, "color") for c in EASY_COLORS]
            scored = [(fuzzy_score_vscode(lower_word, c), c, kind) for c, kind in candidates]
            for score, cand, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                if score > 0:
                    yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta=EASY_DOCS.get(cand, ""), style="bg:#1e1e1e #ffffff")
            return

        if stripped.startswith("[") and not stripped.endswith("]"):
            candidates = [(c, "component") for c in EASY_COMPONENTS]
            scored = [(fuzzy_score_vscode(lower_word, c), c, kind) for c, kind in candidates]
            for score, cand, kind in sorted(scored, key=lambda item: item[0], reverse=True):
                if score > 0:
                    yield Completion(cand, start_position=-len(word) or 0, display=cand, display_meta=EASY_DOCS.get(cand, ""), style="bg:#1e1e1e #ffffff")
            return

        if stripped.startswith("math("):
            candidates = [(f, "math") for f in EASY_MATH_FUNCTIONS]
            for func, kind in candidates:
                yield Completion(func, start_position=-len(word) or 0, display=func, display_meta=f"Math function: {func}()", style="bg:#1e1e1e #ffffff")
            return

        if stripped.startswith("hash("):
            candidates = [(a, "hash") for a in EASY_HASH_ALGOS]
            for algo, kind in candidates:
                yield Completion(algo, start_position=-len(word) or 0, display=algo, display_meta=f"Hash algorithm: {algo}", style="bg:#1e1e1e #ffffff")
            return

        if stripped.startswith("http("):
            candidates = [(m, "http") for m in EASY_HTTP_METHODS]
            for method, kind in candidates:
                yield Completion(method, start_position=-len(word) or 0, display=method, display_meta=f"HTTP method: {method}", style="bg:#1e1e1e #ffffff")
            return

        all_options = (
            [(kw, "keyword") for kw in EASY_KEYWORDS]
            + [(name + "(", "function") for name in self.functions]
            + [(c, "component" if c.startswith("[") else "color" if c.startswith(":") else "builtin") for c in (EASY_COMPONENTS + EASY_COLORS + EASY_BUILTINS)]
            + [(v, "variable") for v in self.variables]
        )
        scored = [(fuzzy_score_vscode(lower_word, opt), opt, kind) for opt, kind in all_options]
        seen = set()
        for score, opt, kind in sorted(scored, key=lambda item: item[0], reverse=True):
            if opt not in seen and score > 0:
                seen.add(opt)
                yield Completion(opt, start_position=-len(word) or 0, display=opt, display_meta=EASY_DOCS.get(opt, ""), style="bg:#1e1e1e #ffffff")

        snippet_candidates = []
        for trigger, snippet_text in EASY_SNIPPETS.items():
            snippet_candidates.append((trigger, snippet_text, "snippet"))

        scored_snippets = [(fuzzy_score_vscode(lower_word, trigger), trigger, snippet_text, kind) for trigger, snippet_text, kind in snippet_candidates]
        for score, trigger, snippet_text, kind in sorted(scored_snippets, reverse=True):
            if trigger not in seen and score > 0:
                seen.add(trigger)
                yield Completion(trigger, start_position=-len(word) or 0, display=trigger, display_meta=f"snippet: {snippet_text}", style="bg:#1e1e1e #ffffff")


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
                    ("[badge]", "class:component-alert", 7),
                    ("[code]", "class:component-box", 6),
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
    "preview": "bg:#111827 #d1fae5",
})


def edit_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = ""

    lexer = EasyLexer()
    variables = set()
    functions = set()

    # Completion is refreshed by our text-change handler. Keeping Prompt
    # Toolkit's own auto-completion off prevents it from ever committing the
    # highlighted item while the user is still typing.
    buffer = Buffer(complete_while_typing=False)
    buffer.text = text
    saved_text = [text]
    buffer.auto_suggest = AutoSuggestFromHistory()

    def extract_variables():
        nonlocal variables, functions
        variables = set()
        functions = set()
        for line in buffer.text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) >= 2 and parts[0] in {"set", "let"}:
                variables.add(parts[1])
            if stripped.startswith("func "):
                match = re.match(r"func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", stripped)
                if match:
                    functions.add(match.group(1))

    extract_variables()
    completer = EasyCompleter(sorted(variables), sorted(functions))
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
        doc = completion_metadata(completion)
        if not doc:
            return []
        lines = doc.splitlines()
        return [("class:toolbar", f" {lines[0]}" + (f"\n {' '.join(lines[1:])}" if len(lines) > 1 else ""))]

    def completion_metadata(completion):
        """Prompt Toolkit may provide display metadata as formatted fragments."""
        value = getattr(completion, "display_meta", None) or ""
        return "".join(fragment[1] for fragment in to_formatted_text(value))

    def get_outline():
        """A lightweight explorer that makes large METRIX files navigable."""
        items = [("class:toolbar", " METRIX EXPLORER\n")]
        diagnostics = []
        for number, source_line in enumerate(buffer.text.splitlines(), start=1):
            stripped = source_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("func "):
                items.append(("class:keyword", f" ƒ  {stripped[5:].rstrip(':')}\n"))
            elif stripped.startswith(("set ", "let ")):
                parts = stripped.split()
                if len(parts) > 1:
                    items.append(("class:line-number", f" ◇  {parts[1]}\n"))
            elif stripped.startswith("metrix [api-call]"):
                items.append(("class:component-chat", f" ◉  API call · line {number}\n"))
            elif stripped.startswith(("row ", "say ")) and any(tag in stripped for tag in ("[header]", "[footer]", "[sidebar]", "[chat:")):
                items.append(("class:component-box", f" ▣  UI · line {number}\n"))
            if stripped.split()[0] in {"if", "for", "while", "func"} and not stripped.endswith(":"):
                diagnostics.append(f" ! line {number}: expected ':'")
        if diagnostics:
            items.append(("class:error", "\n DIAGNOSTICS\n"))
            items.extend(("class:error", f"{line}\n") for line in diagnostics[:5])
        else:
            items.append(("class:line-number", "\n ✓ no static issues\n"))
        return items

    BUILTIN_SIGNATURES = {
        "len": "len(text)",
        "upper": "upper(text)",
        "lower": "lower(text)",
        "trim": "trim(text)",
        "split": "split(text, sep)",
        "join": "join(list, sep)",
        "replace": "replace(text, old, new)",
        "contains": "contains(text, sub)",
        "startswith": "startswith(text, sub)",
        "endswith": "endswith(text, sub)",
        "math": 'math("expr")',
        "random": "random(min, max)",
        "now": "now()",
        "date": "date()",
        "time": "time()",
        "sleep": "sleep(seconds)",
        "read": "read(path)",
        "write": "write(path, content)",
        "append": "append(path, content)",
        "exists": "exists(path)",
        "delete": "delete(path)",
        "listdir": "listdir(path)",
        "exec": "exec(command)",
        "env": "env(variable)",
        "hash": "hash(text, algo)",
        "base64": "base64(text)",
        "decode": "decode(base64_text)",
        "http": "http(url, method)",
        "first": "first(list)",
        "last": "last(list)",
        "reverse": "reverse(value)",
        "unique": "unique(list)",
        "slice": "slice(value, start, end)",
        "index": "index(list, item)",
        "find": "find(text, query)",
        "flatten": "flatten(list)",
        "stringify": "stringify(value)",
        "number": "number(value)",
        "string": "string(value)",
        "boolean": "boolean(value)",
        "repeat": "repeat(text, times)",
        "pad": "pad(text, width, side)",
        "urlencode": "urlencode(text)",
        "urldecode": "urldecode(text)",
        "uuid": "uuid()",
    }

    def get_signature_help():
        cursor = buffer.document.cursor_position
        text = buffer.text
        line_start = buffer.document.cursor_position_row
        line = buffer.document.current_line
        col = buffer.document.cursor_position_col

        for builtin_name in BUILTIN_SIGNATURES:
            if builtin_name not in line:
                continue
            idx = line.find(builtin_name)
            while idx != -1:
                if idx <= col <= idx + len(builtin_name) + 1:
                    open_pos = line.find("(", idx)
                    if open_pos != -1 and col > open_pos:
                        close_pos = line.find(")", open_pos)
                        if close_pos == -1 or col <= close_pos + 1:
                            sig = BUILTIN_SIGNATURES[builtin_name]
                            if close_pos == -1 or col <= close_pos + 1:
                                return f"{builtin_name}(...)"
                idx = line.find(builtin_name, idx + 1)
        return None

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
            if completion:
                metadata = completion_metadata(completion)
                if metadata:
                    completion_info = f" | {metadata}"
        signature_info = get_signature_help() or ""
        if signature_info:
            completion_info = f" | {signature_info}{completion_info}"
        changed = "● unsaved" if buffer.text != saved_text[0] else "✓ saved"
        return [("class:status", f" METRIX Studio | {changed} | {path} | {mode} | Ln {line}/{total}, Col {col}{completion_info} | ↑↓ Select · Tab Accept · F5 Preview · Ctrl+S Save · Ctrl+Q Quit ")]

    def get_toolbar():
        return [("class:toolbar", " METRIX | say set ask clear add sub row metrix if for while func | [box] [chat] [sidebar] [header] [footer] [alert] [list] [table] [progress] [spinner] | :green: :red: :blue: :cyan: | get keys values count title slug sort ")]

    extract_variables()
    completer.variables = sorted(variables)
    completer.functions = sorted(functions)
    buffer.completer = completer

    def on_text_changed(_):
        extract_variables()
        completer.variables = sorted(variables)
        completer.functions = sorted(functions)
        line_numbers_control.text = get_line_numbers()
        statusbar_control.text = get_statusbar()
        if docs_visible[0]:
            docs_control.text = get_doc_text()
        # Keep the recommendation box live, exactly like an editor.  Crucially
        # select_first=False means it is only a visual recommendation: it
        # cannot alter source until the user explicitly presses Tab.
        if buffer.document.current_line.lstrip().startswith("#"):
            buffer.complete_state = None
            return
        try:
            buffer.start_completion(select_first=False)
        except RuntimeError:
            # Prompt Toolkit can reject a refresh while the application is
            # shutting down; the editor should still be able to save/exit.
            pass

    buffer.on_text_changed += on_text_changed

    line_numbers_control = FormattedTextControl(get_line_numbers)
    outline_control = FormattedTextControl(get_outline)
    editor_kwargs = {
        "buffer": buffer,
        "lexer": lexer,
    }
    if "completer" in BufferControl.__init__.__code__.co_varnames:
        editor_kwargs["completer"] = completer
    if "complete_while_typing" in BufferControl.__init__.__code__.co_varnames:
        # We refresh in on_text_changed above so we can force no auto-accept
        # consistently across Prompt Toolkit versions.
        editor_kwargs["complete_while_typing"] = False
    editor_control = BufferControl(**editor_kwargs)
    statusbar_control = FormattedTextControl(get_statusbar)
    toolbar_control = FormattedTextControl(get_toolbar)

    root_container = HSplit([
        Window(content=toolbar_control, height=1, style="class:toolbar"),
        VSplit([
            Window(content=line_numbers_control, width=5, style="class:line-number"),
            Window(content=editor_control, wrap_lines=True),
            Window(width=1, char="│", style="class:line-number"),
            Window(content=outline_control, width=30, style="class:toolbar", wrap_lines=True),
        ]),
        Window(content=statusbar_control, height=1, style="class:status"),
    ])

    docs_visible = [False]
    preview_visible = [False]
    preview_text = [" Preview will appear here. Press F5 to run the current program."]

    docs_control = FormattedTextControl(get_doc_text)
    docs_window = Window(content=docs_control, height=Dimension(min=0, preferred=8), style="class:toolbar")

    preview_control = FormattedTextControl(lambda: preview_text[0])
    preview_window = ConditionalContainer(
        Window(content=preview_control, height=Dimension(min=3, preferred=9), style="class:preview", wrap_lines=True),
        filter=Condition(lambda: preview_visible[0]),
    )
    # Keep the status bar at the bottom while allowing an on-demand live preview.
    root_container = HSplit([
        Window(content=toolbar_control, height=1, style="class:toolbar"),
        VSplit([
            Window(content=line_numbers_control, width=5, style="class:line-number"),
            Window(content=editor_control, wrap_lines=True),
            Window(width=1, char="│", style="class:line-number"),
            Window(content=outline_control, width=30, style="class:toolbar", wrap_lines=True),
        ]),
        preview_window,
        Window(content=statusbar_control, height=1, style="class:status"),
    ])
    root_container = FloatContainer(
        root_container,
        floats=[
            Float(
                # A spacer keeps the menu one row below the cursor instead of
                # covering the code currently being typed.
                content=HSplit([
                    Window(height=1),
                    CompletionsMenu(max_height=12, scroll_offset=1, display_arrows=True),
                ]),
                xcursor=True,
                ycursor=True,
            ),
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
            saved_text[0] = buffer.text
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
        state = app.current_buffer.complete_state
        if state and state.completions:
            # VS Code behaviour: Tab accepts the highlighted completion.  The
            # old implementation only moved the highlight, so users could see
            # a suggestion but had no single-key way to insert it.
            completion = state.current_completion or state.completions[0]
            app.current_buffer.apply_completion(completion)
            docs_control.text = get_doc_text()
        elif not buffer.document.current_line.strip():
            buffer.insert_text("    ")
        else:
            buffer.start_completion(select_first=True)

    @kb.add("s-tab")
    def shift_tab(_):
        from prompt_toolkit.application import get_app
        app = get_app()
        if app.current_buffer.complete_state:
            app.current_buffer.complete_previous()
            docs_control.text = get_doc_text()

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
    @kb.add("c-h")
    def backspace(_):
        buffer.delete_before_cursor()

    @kb.add("(")
    def insert_paren(_):
        buffer.insert_text("()")
        buffer.cursor_left()

    @kb.add("[")
    def insert_bracket(_):
        buffer.insert_text("[]")
        buffer.cursor_left()

    @kb.add("{")
    def insert_brace(_):
        buffer.insert_text("{}")
        buffer.cursor_left()

    @kb.add("\"")
    def insert_double_quote(_):
        buffer.insert_text("\"\"")
        buffer.cursor_left()

    @kb.add("'")
    def insert_single_quote(_):
        buffer.insert_text("''")
        buffer.cursor_left()

    @kb.add(")")
    def close_paren(_):
        if buffer.document.current_char == ")":
            buffer.cursor_right()
        else:
            buffer.insert_text(")")

    @kb.add("]")
    def close_bracket(_):
        if buffer.document.current_char == "]":
            buffer.cursor_right()
        else:
            buffer.insert_text("]")

    @kb.add("}")
    def close_brace(_):
        if buffer.document.current_char == "}":
            buffer.cursor_right()
        else:
            buffer.insert_text("}")

    @kb.add("<")
    def insert_angle(_):
        buffer.insert_text("<>")
        buffer.cursor_left()

    @kb.add(">")
    def close_angle(_):
        if buffer.document.current_char == ">":
            buffer.cursor_right()
        else:
            buffer.insert_text(">")

    @kb.add("f1")
    def show_docs(_):
        docs_visible[0] = True
        docs_control.text = get_doc_text()

    @kb.add("f5")
    def preview(_):
        try:
            lines = [strip_ansi(line) for line in run(buffer.text)]
            preview_text[0] = " METRIX Preview\n\n" + ("\n".join(lines) if lines else "(no output)")
        except EasyError as error:
            preview_text[0] = f" METRIX Preview Error\n\n{error}"
        preview_visible[0] = True
        from prompt_toolkit.application import get_app
        get_app().invalidate()

    @kb.add("c-p")
    def hide_preview(_):
        preview_visible[0] = False

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
        editing_mode=EditingMode.EMACS,
    )

    # Populate the persistent chooser on launch too, then let actual edits
    # refresh it. Running this from after_render would create a redraw loop.
    application.run(pre_run=lambda: on_text_changed(None))
