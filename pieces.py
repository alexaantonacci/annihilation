from dataclasses import dataclass


@dataclass
class Piece:
    side: str
    kind: str
    pos: tuple
    lives: int = 1
    fork: tuple | None = None
    fork_fixed: int | None = None
