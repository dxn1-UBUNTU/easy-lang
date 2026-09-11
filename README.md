# METRIX

**METRIX** is a serious language for terminal workspaces, interactive tools, API clients, and agent-style interfaces. It puts TUI composition first without limiting the rest of your program.

Build dashboards, coding-agent workspaces, setup tools, API workflows, and full terminal products—not toy print scripts.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/dxn1-UBUNTU/METRIX/main/install/install.sh | bash
```

Then run METRIX from anywhere:

```bash
m run examples/agent_workspace.met
m edit examples/agent_workspace.met
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
m run examples/agent_workspace.met
```

## Language features

- Terminal primitives: headers, footers, panes, boxes, chat bubbles, sidebars, tables, lists, alerts, badges, code panels, progress, spinners, styles, and color.
- Data: JSON-style lists and maps plus `get`, `keys`, `values`, `count`, `sort`, `title`, `slug`, `first`, `last`, `reverse`, `unique`, `slice`, `index`, `find`, and `flatten`.
- Conversion and utilities: `stringify`, `number`, `string`, `boolean`, `repeat`, `pad`, URL encoding/decoding, hashes, Base64, UUIDs, and math.
- Logic: `if` / `else`, `for`, `while`, and reusable `func` blocks with `return`.
- Interaction: `ask name "Prompt"`, `select name "Prompt" from ["one", "two"]`, and `clear`.
- APIs: native calls to OpenAI-compatible endpoints, Anthropic, Gemini, Hugging Face, Cohere, Ollama, and configurable generic HTTP requests with headers and a body.
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

- The recommendation popup stays live while you type. It never modifies code by itself.
- Use **Up/Down** to choose a completion, then press **Tab** to insert that one choice.
- **Ctrl+S** saves, **Ctrl+Q** exits, **Ctrl+/** comments a line, and **F1** opens documentation.
- **F5** runs the current program into an in-editor preview panel; **Ctrl+P** closes it.
- **F6** trims trailing whitespace, while the status bar tracks saved versus unsaved changes.
- A permanent **METRIX Explorer** shows functions, state, API calls, UI sections, and simple static diagnostics beside the source.
- Completion is a browseable language catalogue (90+ commands, components, colors, APIs, built-ins, snippets, variables, and functions declared in the current file), filtered as you type.

## Safety

METRIX can run commands, read environment variables, make web requests, and modify files. Treat unknown `.met` programs as code: inspect them before running them.

## Development

```bash
python3 tests/smoke_test.py
```
