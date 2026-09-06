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

Easy Lang removes all of that. It gives you `[box]`, `[chat]`, `[sidebar]`, `[header]`, `[footer]`, and `[alert]` out of the box so you can focus on the interface, not the implementation.

## Components

### Box

```easy
say "hello world" [box] :green:
```

Output:

```text
┌──────────────┐
│ hello world  │
└──────────────┘
```

### Chat

Left or right aligned chat bubbles.

```easy
say "user: hello" [chat:left] :cyan:
say "bot: hi there" [chat:right] :green:
```

### Sidebar

A vertical sidebar panel.

```easy
say "status: online" [sidebar] :yellow:
```

### Header

A bold header bar.

```easy
say "My App" [header] :cyan:
```

### Footer

A bold footer bar.

```easy
say "v1.0.0" [footer] :magenta:
```

### Alert

A warning or error alert.

```easy
say "disk full" [alert] :red:
say "check complete" [alert] :green:
```

## Colors

All components support colors:

- `:green:`
- `:red:`
- `:blue:`
- `:yellow:`
- `:cyan:`
- `:magenta:`
- `:white:`
- `:black:`

## Full Example

```easy
say "Chat Demo" [header] :cyan:
say "user: hello" [chat:left] :cyan:
say "bot: hi there" [chat:right] :green:
say "status: online" [sidebar] :yellow:
say "warning: low disk" [alert] :red:
say "main content here" [box] :white:
say "footer info" [footer] :magenta:
```

## Variables

```easy
set name "Easy Lang"
say name [box] :cyan:

set score 0
add score 10
sub score 3
say score [box] :yellow:
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

Autocomplete knows Easy syntax: keywords, components, colors, and variables as you define them.

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
