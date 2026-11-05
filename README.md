# expression parser and interpreter
# expr-interpreter

A small expression parser and interpreter written in pure Python. It turns text like `x = 3 * (2 + 4)` into tokens, builds an abstract syntax tree (AST), and evaluates it. There are no dependencies.

Built to be easy to read and extend, so it works well as a learning project for lexers, recursive descent parsers, and tree-walking interpreters.

## Features

- Arithmetic with correct precedence: `+ - * / % ^`
- Right-associative exponentiation (`2^3^2 = 512`) and `-2^2 = -4`
- Parentheses and unary `+` / `-`
- Variables and assignment (`x = 5`), which persist across lines in the REPL
- Built-in constants (`pi`, `e`) and functions (`sin`, `cos`, `tan`, `sqrt`, `abs`, `log`, `exp`, `floor`, `ceil`, `min`, `max`, `pow`, `round`)
- Clear errors with character positions: `LexError`, `ParseError`, `EvalError`

## Requirements

Python 3.10 or newer (uses `match` statements).

## Getting started

```bash
git clone https://github.com/<your-username>/expr-interpreter.git
cd expr-interpreter
python expr.py
```

### REPL example

```
> 1 + 2 * 3
7
> -2^2
-4
> x = 3 * (2 + 4)
18
> sqrt(x^2) + 1
19
> max(1, x, 5) % 4
2
> 1 / 0
Error: Division by zero
```

### Use as a library

```python
from expr import Interpreter

it = Interpreter()
it.run("x = 3 * (2 + 4)")   # 18.0
it.run("sqrt(x^2) + 1")     # 19.0
```

## Syntax reference

| Operator | Meaning | Precedence | Associativity |
|---|---|---|---|
| `+` `-` | add, subtract | lowest | left |
| `*` `/` `%` | multiply, divide, modulo | | left |
| `-` `+` (prefix) | negate, identity | | right |
| `^` | power | highest | right |

Formal grammar:

```
statement := IDENT '=' expr | expr
expr      := term   (('+' | '-') term)*
term      := unary  (('*' | '/' | '%') unary)*
unary     := '-' unary | '+' unary | power
power     := primary ('^' unary)?
primary   := NUMBER | IDENT '(' [expr (',' expr)*] ')' | IDENT | '(' expr ')'
```

## How it works

```
source text -> tokenize() -> Parser (recursive descent) -> AST -> Interpreter
```

1. **Lexer** splits the input into tokens using one regex with named groups.
2. **Parser** has one method per grammar rule. Precedence comes from how the rules nest.
3. **Interpreter** walks the AST recursively and computes the value.

## Project structure

```
expr-interpreter/
├── expr.py        # lexer, parser, AST, interpreter, REPL
├── test_expr.py   # unit tests
├── README.md
├── LICENSE
└── .gitignore
```

## Running the tests

```bash
python -m unittest -v
```

## Extending

- **New function:** add an entry to `Interpreter.functions`.
- **New operator:** add a rule in `Parser` and a case in `Interpreter._binary`.

## Limitations

- All numbers are floats.
- No user-defined functions, conditionals, or comparison operators yet.

## Roadmap

- [ ] Comparison and logical operators
- [ ] `if` expressions
- [ ] User-defined functions
- [ ] Packaging with `pyproject.toml`

## Contributing

Issues and pull requests are welcome. Please add a test for any new behavior.

## License

MIT, see [LICENSE](LICENSE).
