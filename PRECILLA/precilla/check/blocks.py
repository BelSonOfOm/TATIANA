"""
PRECILLA / check / blocks.py

Pull checkable equation blocks out of a derivation draft.

The PROMPT.md output contract asks the model to emit, for every equation:

    ```python
    # EQ-7
    lhs = ...
    rhs = ...
    assert simplify(lhs - rhs) == 0
    ```

This module finds those, and -- just as importantly -- finds the equations that
have NO block. An unchecked equation is not a neutral absence; it is the most
likely place for the error to be, because it is the step the model could not
render mechanically.

stdlib only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

_FENCE_RE = re.compile(
    r"```(?P<lang>python|py|sympy)?[ \t]*\n(?P<body>.*?)```",
    re.S | re.I)

# Accept EQ-n and D-n. The first real draft numbered its DERIVATIONS D1..D6
# and its EQUATIONS EQ-1..EQ-12, cross-linking them only once ("# EQ-10 / D1").
# Demanding one convention found 1 block out of 5. The label is bookkeeping;
# refusing to read a valid check because of its name is an instrument defect.
_EQ_TAG_RE = re.compile(r"#\s*((?:EQ|D)[-_ ]?\d+[a-z]?)", re.I)

# Equation labels used in prose: "EQ-7", "(EQ 12)", "eq-3b"
_EQ_MENTION_RE = re.compile(r"\b(EQ|D)[-_ ]?(\d+[a-z]?)\b")

_UNCHECKED_RE = re.compile(r"\[UNCHECKED\]", re.I)


@dataclass
class Block:
    eq: str
    source: str
    line: int
    lang: str = "python"
    aliases: list = field(default_factory=list)
    declared_unchecked: bool = False

    def to_dict(self):
        return asdict(self)


def _line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def find_blocks(text):
    """Fenced code blocks carrying an EQ tag."""
    out = []
    for m in _FENCE_RE.finditer(text):
        body = m.group("body")
        tag = _EQ_TAG_RE.search(body)
        if not tag:
            continue
        # "# EQ-10 / D1" -- record both, key on the first.
        aliases = [_norm(t) for t in _EQ_TAG_RE.findall(body[:200])]
        out.append(Block(
            eq=_norm(tag.group(1)),
            aliases=aliases,
            source=body,
            line=_line_of(text, m.start()),
            lang=(m.group("lang") or "python").lower(),
            declared_unchecked=bool(_UNCHECKED_RE.search(body)),
        ))
    return out


def _norm(label):
    m = re.match(r"\s*(EQ|D)[-_ ]?(\d+[a-z]?)", label, re.I)
    return ("%s-%s" % (m.group(1).upper(), m.group(2).lower())) if m \
        else label.upper()


def find_mentions(text):
    """Every EQ-n referenced anywhere in the prose."""
    seen = []
    for m in _EQ_MENTION_RE.finditer(text):
        lab = "%s-%s" % (m.group(1).upper(), m.group(2).lower())
        if lab not in seen:
            seen.append(lab)
    return seen


def audit(text):
    """
    Which equations are claimed, which are checkable, which are neither.

    `unchecked` is the interesting output. It is the list of steps the model
    asserted but could not mechanise.
    """
    blocks = find_blocks(text)
    have = set()
    for b in blocks:
        have.add(b.eq)
        have.update(b.aliases or [])
    mentioned = find_mentions(text)
    declared = {b.eq for b in blocks if b.declared_unchecked}

    missing = [e for e in mentioned if e not in have]
    return {
        "n_mentioned": len(mentioned),
        "n_blocks": len(blocks),
        "mentioned": mentioned,
        "checkable": sorted(have - declared),
        "declared_unchecked": sorted(declared),
        "missing_block": missing,
        "coverage": (round((len(have) - len(declared)) / len(mentioned), 3)
                     if mentioned else None),
        "blocks": [b.to_dict() for b in blocks],
    }
