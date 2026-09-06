# Easy

Easy is a tiny beginner-friendly coding language.

Example:

```easy
say "hello"
set score 10
add score 5
say score
```

Output:

```text
hello
15
```

## Commands

- `say "text"` prints text
- `say name` prints a variable
- `set name value` stores a value
- `add name value` adds to a number variable
- `sub name value` subtracts from a number variable

## Run It

Install Easy:

```bash
curl -fsSL https://raw.githubusercontent.com/dxn1-UBUNTU/easy-lang/main/install/install.sh | bash
```

Then run an Easy file:

```bash
easy run examples/hello.easy
```

Easy files can also run directly when they start with this line:

```easy
#!/usr/bin/env easy
```

Then:

```bash
chmod +x examples/hello.easy
./examples/hello.easy
```

For repo development:

```bash
python3 -m pip install -e .
easy run examples/hello.easy
easy check examples/hello.easy
easy repl
```

## Test It

```bash
python3 tests/smoke_test.py
```

## Editor

This repo includes VS Code settings, extension recommendations, and Easy command snippets.
