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

For a full-color dashboard example, run:

```bash
m run examples/nexus_dashboard.met
```

## TUI design system

METRIX screens are ordinary terminal output, but the primitives compose into product-quality layouts. Use named terminal colors or 24-bit hex colors with `[fg:#RRGGBB]`, `[bg:#RRGGBB]`, or a trailing `#RRGGBB`.

```metrix
say "NEXUS CONTROL PLANE" [header] [width:72] [bg:#101828] [fg:#7dd3fc]
say "Database migration completed" [toast:success] [fg:#4ade80]
say "REQUESTS\n12,842 requests · P95 124 ms" [panel:Live traffic] [width:42] [bg:#172033] [fg:#e2e8f0]
say "Open command palette" [key:Ctrl+K] [fg:#fbbf24]
say "" [rule] [width:72]
```

Available layout primitives include `row`, `[panel:TITLE]`, `[card]`, `[box:*]`, headers/footers, chat bubbles, lists, tables, badges, code panels, progress bars, toasts, shortcut hints, dividers, alignment, padding, widths, styles, and foreground/background colors.

## Requests and APIs

Use `request` for flexible text or JSON HTTP calls; it supports method, body, headers, and timeout. `webhook` posts JSON, while `download` saves a remote response to a file.

```metrix
set payload {"event": "deploy", "status": "ready"}
set headers {"Authorization": "Bearer token", "X-Project": "metrix"}
set response request("https://api.example.com/events", "POST", payload, headers, 15)
say stringify(response) [code] [width:72]

# Native provider call (Ollama is local; other supported providers include OpenAI,
# Anthropic, Gemini, Cohere, Hugging Face, and generic HTTP.)
metrix [api-call]<ollama>(model="llama3.2", prompt="Write a one-line release note")
```

Generic API calls can send headers and JSON safely without shelling out:

```metrix
metrix [api-call]<http>(url="https://api.example.com/items", method=POST, headers={"Authorization":"Bearer token"}, json={"name":"METRIX"}, timeout=15)
say api_result [panel:Response] [width:72]
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

## Checking code

`m check app.met` is static: it does **not** execute code, call APIs, write files, or run shell commands. It reports line-level errors for malformed control blocks, indentation, broken strings/brackets, invalid UI tags, unknown commands, invalid API providers, and malformed rows. `m run` performs the same preflight check before execution.

## Safety

METRIX can run commands, read environment variables, make web requests, and modify files. Treat unknown `.met` programs as code: inspect them before running them.

## Development

```bash
python3 tests/smoke_test.py
```
