# METRIX

**METRIX** is a serious language for terminal workspaces, interactive tools, API clients, and agent-style interfaces. It puts TUI composition first without limiting the rest of your program.

Build dashboards, coding-agent workspaces, setup tools, API workflows, and full terminal products—not toy print scripts.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/dxn1-UBUNTU/METRIX/main/install/install.sh | bash
```

Then run METRIX from anywhere:

```bash
metrix run examples/agent_workspace.metrix
metrix edit examples/agent_workspace.metrix
metrix repl
```

## Build a terminal workspace

`row` composes two-pane screens, so you can create the session/file/chat layout familiar from modern coding agents.

```metrix
clear
say "METRIX AGENT  •  main  •  ollama / llama3.2" [header] :cyan:
row "SESSIONS\n› Build editor\n  API playground" | "You\nMake autocomplete feel instant." [left:28]
row "FILES\n  editor.py\n  interpreter.py" | "METRIX\nI updated the completion engine." [left:28]
say "Type a prompt…                         / commands   Enter send" [footer] :magenta:
```

Run the complete example with:

```bash
metrix run examples/agent_workspace.metrix
```

## Language features

- Terminal primitives: headers, footers, panes, boxes, chat bubbles, sidebars, tables, lists, alerts, progress, spinners, styles, and color.
- Data: JSON-style lists and maps plus `get`, `keys`, `values`, `count`, `sort`, `title`, and `slug`.
- Logic: `if` / `else`, `for`, `while`, and reusable `func` blocks with `return`.
- Interaction: `ask name "Prompt"` and `clear`.
- APIs: native calls to OpenAI, Anthropic, Gemini, Hugging Face, Cohere, and generic HTTP endpoints.
- System tools: file I/O, shell commands, environment reads, hashes, encoding, date/time, and math.

```metrix
func badge(label):
    return upper(label)

set total 0
for number in range(1, 4):
    add total number

if total == 6:
    say badge("ready") [box:rounded] :green:
```

## METRIX Studio

The built-in editor is designed for fast terminal development:

- Type `s` to open a live completion popup for `say`, `set`, and more.
- Use **Up/Down** to choose a completion, then **Tab** to insert it.
- **Ctrl+Space** opens completion manually.
- **Ctrl+S** saves, **Ctrl+Q** exits, **Ctrl+/** comments a line, and **F1** opens documentation.
- Completion understands syntax, components, colors, APIs, functions, snippets, and variables declared in the current file.

## Safety

METRIX can run commands, read environment variables, make web requests, and modify files. Treat unknown `.metrix` programs as code: inspect them before running them.

## Development

```bash
python3 tests/smoke_test.py
```
