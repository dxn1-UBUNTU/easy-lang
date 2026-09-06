# Easy Lang

Easy Lang is a tiny language built for one thing: **making beautiful terminal UIs**.

Instead of wrestling with ANSI escape codes, box-drawing characters, and color mappings, you just write what you want:

```easy
say "hello world" [box] :green:
```

Output:

```text
┌──────────────┐
│ hello world  │
└──────────────┘
```

That's it. No libraries, no setup, just beautiful TUIs.

## Why

Building TUIs in the terminal usually means:

- Memorizing ANSI color codes
- Manually calculating box widths
- Fighting with terminal compatibility

Easy Lang removes all of that. It gives you `[box]` and `:color:` out of the box so you can focus on the interface, not the implementation.

## Syntax

### `say`

Print text to the terminal.

```easy
say "hello"
say "world" [box]
say "error" :red:
say "success" [box] :green:
```

### Variables

Store and reuse values.

```easy
set name "Easy Lang"
say name [box] :cyan:

set score 0
add score 10
sub score 3
say score [box] :yellow:
```

### Colors

- `:green:`
- `:red:`
- `:blue:`
- `:yellow:`
- `:cyan:`
- `:magenta:`
- `:white:`
- `:black:`

### Boxes

Add `[box]` to any `say` command to wrap text in a clean border.

```easy
say "stats" [box] :cyan:
say "level 1" [box]
```

## Examples

### Greeting

```easy
say "hello world" [box] :green:
```

### Scoreboard

```easy
set score 0
add score 10
say score [box] :yellow:
```

### Status panel

```easy
say "System Status" [box] :cyan:
say "Online" [box] :green:
say "CPU: 42%" [box]
say "MEM: 1.2GB" [box]
```

## Install

Install Easy like a real language:

```bash
curl -fsSL https://raw.githubusercontent.com/dxn1-UBUNTU/easy-lang/main/install/install.sh | bash
```

Or use the universal installer:

```bash
easy install dxn1-UBUNTU/easy-lang
```

## Run

```bash
easy run examples/hello.easy
```

Or just:

```bash
easy examples/hello.easy
```

## Edit

Easy ships with a terminal editor that has real syntax highlighting and autocomplete while you type.

```bash
easy edit examples/hello.easy
```

- **Ctrl+S** to save
- **Ctrl+Q** to quit

Autocomplete knows Easy syntax: keywords, `[box]`, colors, and variables as you define them.

## Direct execution

Easy files can run directly:

```easy
#!/usr/bin/env easy
say "hello world" [box] :green:
```

```bash
chmod +x app.easy
./app.easy
```

## Development

```bash
git clone https://github.com/dxn1-UBUNTU/easy-lang.git
cd easy-lang
python3 -m pip install -e .
easy run examples/tui_demo.easy
easy edit examples/tui_demo.easy
easy check examples/tui_demo.easy
easy repl
```

## Test

```bash
python3 tests/smoke_test.py
```

## Install Anything

`easy install` works as a universal installer.

```bash
# System packages
easy install git
easy install gh
easy install curl

# Python packages
easy install flask
easy install requests

# npm packages
easy install typescript
easy install prettier

# GitHub repos
easy install dxn1-UBUNTU/easy-lang
easy install https://github.com/cli/cli
```

Easy auto-detects the best installer for the target.
