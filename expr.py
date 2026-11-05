"""
A small expression parser and interpreter.

Pipeline:  source text -> tokenize() -> Parser -> AST -> Interpreter

Grammar (lowest to highest precedence):
    statement := IDENT '=' expr | expr
    expr      := term   (('+' | '-') term)*
    term      := unary  (('*' | '/' | '%') unary)*
    unary     := '-' unary | '+' unary | power
    power     := primary ('^' unary)?          # right-associative
    primary   := NUMBER | IDENT '(' [expr (',' expr)*] ')' | IDENT | '(' expr ')'

Note: -2^2 == -4 because unary minus binds looser than '^'.
"""

import math
import re
from dataclasses import dataclass


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------
class ExprError(Exception):
    """Base class for all errors raised by this module."""


class LexError(ExprError):
    pass


class ParseError(ExprError):
    pass


class EvalError(ExprError):
    pass


# --------------------------------------------------------------------------
# Lexer
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Token:
    kind: str    # NUMBER, IDENT, OP, LPAREN, RPAREN, COMMA, EOF
    value: str
    pos: int


TOKEN_RE = re.compile(
    r"""
    (?P<WS>\s+)
  | (?P<NUMBER>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)
  | (?P<IDENT>[A-Za-z_][A-Za-z_0-9]*)
  | (?P<OP>[-+*/%^=])
  | (?P<LPAREN>\()
  | (?P<RPAREN>\))
  | (?P<COMMA>,)
    """,
    re.VERBOSE,
)


def tokenize(text: str) -> list[Token]:
    tokens, pos = [], 0
    while pos < len(text):
        m = TOKEN_RE.match(text, pos)
        if not m:
            raise LexError(f"Unexpected character {text[pos]!r} at position {pos}")
        if m.lastgroup != "WS":
            tokens.append(Token(m.lastgroup, m.group(), pos))
        pos = m.end()
    tokens.append(Token("EOF", "", pos))
    return tokens


# --------------------------------------------------------------------------
# AST
# --------------------------------------------------------------------------
@dataclass
class Number:
    value: float

@dataclass
class Variable:
    name: str

@dataclass
class UnaryOp:
    op: str
    operand: "Node"

@dataclass
class BinaryOp:
    op: str
    left: "Node"
    right: "Node"

@dataclass
class Call:
    name: str
    args: list

@dataclass
class Assign:
    name: str
    value: "Node"

Node = Number | Variable | UnaryOp | BinaryOp | Call | Assign


# --------------------------------------------------------------------------
# Parser (recursive descent)
# --------------------------------------------------------------------------
class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0

    # -- helpers --
    @property
    def cur(self) -> Token:
        return self.tokens[self.i]

    def advance(self) -> Token:
        tok = self.cur
        self.i += 1
        return tok

    def match_op(self, *ops: str) -> Token | None:
        if self.cur.kind == "OP" and self.cur.value in ops:
            return self.advance()
        return None

    def expect(self, kind: str) -> Token:
        if self.cur.kind != kind:
            raise ParseError(
                f"Expected {kind} but found {self.cur.kind} "
                f"{self.cur.value!r} at position {self.cur.pos}"
            )
        return self.advance()

    # -- grammar rules --
    def parse(self) -> Node:
        node = self.statement()
        if self.cur.kind != "EOF":
            raise ParseError(f"Unexpected {self.cur.value!r} at position {self.cur.pos}")
        return node

    def statement(self) -> Node:
        nxt = self.tokens[self.i + 1]
        if self.cur.kind == "IDENT" and nxt.kind == "OP" and nxt.value == "=":
            name = self.advance().value
            self.advance()  # '='
            return Assign(name, self.expr())
        return self.expr()

    def expr(self) -> Node:
        node = self.term()
        while tok := self.match_op("+", "-"):
            node = BinaryOp(tok.value, node, self.term())
        return node

    def term(self) -> Node:
        node = self.unary()
        while tok := self.match_op("*", "/", "%"):
            node = BinaryOp(tok.value, node, self.unary())
        return node

    def unary(self) -> Node:
        if tok := self.match_op("-", "+"):
            return UnaryOp(tok.value, self.unary())
        return self.power()

    def power(self) -> Node:
        base = self.primary()
        if self.match_op("^"):
            return BinaryOp("^", base, self.unary())  # right-assoc
        return base

    def primary(self) -> Node:
        tok = self.cur
        if tok.kind == "NUMBER":
            self.advance()
            return Number(float(tok.value))
        if tok.kind == "IDENT":
            self.advance()
            if self.cur.kind == "LPAREN":
                self.advance()
                args = []
                if self.cur.kind != "RPAREN":
                    args.append(self.expr())
                    while self.cur.kind == "COMMA":
                        self.advance()
                        args.append(self.expr())
                self.expect("RPAREN")
                return Call(tok.value, args)
            return Variable(tok.value)
        if tok.kind == "LPAREN":
            self.advance()
            node = self.expr()
            self.expect("RPAREN")
            return node
        raise ParseError(
            f"Unexpected {tok.kind if tok.kind == 'EOF' else repr(tok.value)} "
            f"at position {tok.pos}"
        )


def parse(text: str) -> Node:
    return Parser(tokenize(text)).parse()


# --------------------------------------------------------------------------
# Interpreter (tree-walking)
# --------------------------------------------------------------------------
class Interpreter:
    def __init__(self):
        self.variables: dict[str, float] = {"pi": math.pi, "e": math.e}
        self.functions = {
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "sqrt": math.sqrt, "abs": abs, "log": math.log,
            "exp": math.exp, "floor": math.floor, "ceil": math.ceil,
            "min": min, "max": max, "pow": math.pow, "round": round,
        }

    def run(self, text: str) -> float:
        return self.eval(parse(text))

    def eval(self, node: Node) -> float:
        match node:
            case Number(value):
                return value
            case Variable(name):
                if name not in self.variables:
                    raise EvalError(f"Undefined variable {name!r}")
                return self.variables[name]
            case Assign(name, value):
                result = self.eval(value)
                self.variables[name] = result
                return result
            case UnaryOp(op, operand):
                v = self.eval(operand)
                return -v if op == "-" else v
            case BinaryOp(op, left, right):
                return self._binary(op, self.eval(left), self.eval(right))
            case Call(name, args):
                fn = self.functions.get(name)
                if fn is None:
                    raise EvalError(f"Undefined function {name!r}")
                try:
                    return fn(*[self.eval(a) for a in args])
                except (TypeError, ValueError) as ex:
                    raise EvalError(f"Error calling {name}(): {ex}") from None
        raise EvalError(f"Unknown node {node!r}")

    @staticmethod
    def _binary(op: str, a: float, b: float) -> float:
        try:
            match op:
                case "+": return a + b
                case "-": return a - b
                case "*": return a * b
                case "/": return a / b
                case "%": return a % b
                case "^": return a ** b
        except ZeroDivisionError:
            raise EvalError("Division by zero") from None
        except OverflowError:
            raise EvalError("Numeric overflow") from None
        raise EvalError(f"Unknown operator {op!r}")


# --------------------------------------------------------------------------
# REPL / demo
# --------------------------------------------------------------------------
def fmt(x: float) -> str:
    return str(int(x)) if isinstance(x, float) and x.is_integer() else str(x)


def repl():
    interp = Interpreter()
    print("Expression REPL. Try: x = 3 * (2 + 4), sqrt(x^2), -2^2. Ctrl-D to quit.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        try:
            print(fmt(interp.run(line)))
        except ExprError as ex:
            print(f"Error: {ex}")


if __name__ == "__main__":
    repl()