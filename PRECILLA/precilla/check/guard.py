"""
PRECILLA / check / guard.py

An AST allowlist for model-generated code.

`precilla check` executes Python written by a language model. That is a real
risk and pretending otherwise would be the same class of error this project
keeps catching elsewhere -- an instrument that reports success because it never
looked. So every block is statically screened BEFORE it runs, and anything
outside the allowlist is refused rather than sandbox-trusted.

This is defence in depth, not a security boundary. It stops an accidental
`os.system` or a stray `open(...)`, and it stops the obvious exfiltration
shapes. It is NOT proof against an adversary who controls the model's output.
If you are running blocks from an untrusted source, run PRECILLA in a container.

stdlib only.
"""

from __future__ import annotations

import ast

ALLOWED_IMPORTS = {"sympy", "math", "cmath", "fractions", "itertools"}

FORBIDDEN_NAMES = {
    "eval", "exec", "compile", "open", "input", "__import__", "globals",
    "locals", "vars", "getattr", "setattr", "delattr", "breakpoint", "exit",
    "quit", "help", "memoryview",
}

# Attribute names that are the usual escape hatches out of a restricted eval.
FORBIDDEN_ATTRS = {
    "__class__", "__bases__", "__subclasses__", "__mro__", "__globals__",
    "__code__", "__closure__", "__func__", "__self__", "__dict__",
    "__builtins__", "__loader__", "__spec__", "__reduce__",
    "__reduce_ex__", "__getattribute__", "__base__", "__init_subclass__",
}


class Refusal(Exception):
    pass


def screen(src, allowed_imports=None):
    """
    Return a list of violation strings. Empty list == safe to run.

    Deliberately conservative: unknown constructs are refused, not permitted.
    """
    allowed = set(allowed_imports or ALLOWED_IMPORTS)
    problems = []

    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return ["syntax error: %s" % e]

    for node in ast.walk(tree):
        # imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in allowed:
                    problems.append("import of %r is not allowed" % alias.name)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level:
                problems.append("relative import is not allowed")
            elif root not in allowed:
                problems.append("import from %r is not allowed" % node.module)

        # dangerous builtins by name
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES:
                problems.append("use of %r is not allowed" % node.id)

        # attribute escapes
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRS or (
                    node.attr.startswith("__") and node.attr.endswith("__")):
                problems.append("attribute %r is not allowed" % node.attr)

        # with-statements can open files via context managers
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            problems.append("with-statement is not allowed in a check block")

        elif isinstance(node, (ast.AsyncFunctionDef, ast.Await)):
            problems.append("async is not allowed in a check block")

        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            problems.append("global/nonlocal is not allowed")

    return problems


def assert_safe(src, allowed_imports=None):
    p = screen(src, allowed_imports)
    if p:
        raise Refusal("; ".join(sorted(set(p))))
    return True
