"""Safe recursive-descent parser for FOLIO's Unicode FOL annotations.

One nonempty uninterpreted domain; no unique-name or closed-world assumptions.
Precedence (low to high): equivalence, implication, or/xor, and, negation.
Quantifiers scope over the following unary expression (use parentheses for bodies).
"""
import re
import z3


class FormulaError(ValueError):
    pass


class FormulaParser:
    def __init__(self):
        self.domain = z3.DeclareSort('Entity')
        self.symbols = {}

    def parse(self, text):
        if not isinstance(text, str) or not text.strip():
            raise FormulaError('Expected a nonempty formula string')
        text = text.replace('⟷', '↔').replace('⟶', '→')
        self.tokens = re.findall(r"\s+|[^\W\d][\w’']*(?:\.\d+[\w’']*)*|[∀∃¬∧∨⊕→↔=≠(),.]|.", text)
        self.tokens = [t for t in self.tokens if not t.isspace()]
        self.pos = 0
        result = self.expression(0, {})
        if self.pos != len(self.tokens):
            raise FormulaError(f'Unexpected token {self.tokens[self.pos]!r}')
        return result

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self, expected=None):
        token = self.peek()
        if token is None or (expected is not None and token != expected):
            raise FormulaError(f'Expected {expected or "token"}, got {token!r}')
        self.pos += 1
        return token

    def name(self):
        token = self.take()
        if not re.fullmatch(r"[^\W\d][\w’']*(?:\.\d+[\w’']*)*", token):
            raise FormulaError(f'Invalid identifier {token!r}')
        return token

    def symbol(self, name, arity, predicate):
        signature = (arity, predicate)
        if name in self.symbols:
            old, value = self.symbols[name]
            if old != signature:
                raise FormulaError(f'Inconsistent signature for {name}')
            return value
        if arity == 0:
            value = z3.Bool(name) if predicate else z3.Const(name, self.domain)
        else:
            value = z3.Function(name, *([self.domain] * arity),
                                z3.BoolSort() if predicate else self.domain)
        self.symbols[name] = (signature, value)
        return value

    def term(self, env):
        name = self.name()
        if self.peek() == '(':
            args = self.arguments(env)
            return self.symbol(name, len(args), False)(*args)
        if name in env:
            return env[name]
        # FOLIO uses x/y/z (and indexed variants) as variables.
        if name in ('x', 'y', 'z'):
            raise FormulaError(f'Unbound variable {name}')
        return self.symbol(name, 0, False)

    def arguments(self, env):
        self.take('(')
        args = [self.term(env)]
        while self.peek() == ',':
            self.take(',')
            args.append(self.term(env))
        self.take(')')
        return args

    def unary(self, env):
        token = self.peek()
        if token == '¬':
            self.take()
            return z3.Not(self.unary(env))
        if token in ('∀', '∃'):
            self.take()
            name = self.name()
            variable = z3.Const(name, self.domain)
            if self.peek() == '.':
                self.take()
            body = self.unary(dict(env, **{name: variable}))
            return (z3.ForAll if token == '∀' else z3.Exists)([variable], body)
        if token == '(':
            self.take()
            value = self.expression(0, env)
            self.take(')')
            return value
        start = self.pos
        name = self.name()
        args = self.arguments(env) if self.peek() == '(' else None
        if self.peek() in ('=', '≠'):
            self.pos = start
            left = self.term(env)
            op = self.take()
            right = self.term(env)
            return left == right if op == '=' else left != right
        if name in env:
            raise FormulaError('Individual used as a proposition')
        symbol = self.symbol(name, len(args) if args else 0, True)
        return symbol(*args) if args else symbol

    def expression(self, minimum, env):
        left = self.unary(env)
        precedence = {'↔': 0, '→': 1, '∨': 2, '⊕': 2, '∧': 3}
        while self.peek() in precedence and precedence[self.peek()] >= minimum:
            op = self.take()
            right = self.expression(precedence[op] + (0 if op == '→' else 1), env)
            left = {'↔': lambda: left == right,
                    '→': lambda: z3.Implies(left, right),
                    '∨': lambda: z3.Or(left, right),
                    '⊕': lambda: z3.Xor(left, right),
                    '∧': lambda: z3.And(left, right)}[op]()
        return left
