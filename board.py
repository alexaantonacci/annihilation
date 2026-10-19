from pieces import Piece

SIZE = 6

LABELS = {
    ("M", "mu"): "mu-",
    ("M", "t"): "t",
    ("M", "W"): "W-",
    ("M", "e"): "e-",
    ("A", "mu"): "mu+",
    ("A", "t"): "T",
    ("A", "W"): "W+",
    ("A", "e"): "e+",
}

ORTHOGONAL = [(1, 0), (-1, 0), (0, 1), (0, -1)]
ALL_EIGHT = ORTHOGONAL + [(1, 1), (1, -1), (-1, 1), (-1, -1)]
KNIGHT = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]


def on_board(pos):
    row, col = pos
    return 0 <= row < SIZE and 0 <= col < SIZE


def is_fermion(piece):
    return piece.kind in ("t", "e", "mu")


def adjacent(a, b):
    if a == b:
        return False
    row_a, col_a = a
    row_b, col_b = b
    return abs(row_a - row_b) <= 1 and abs(col_a - col_b) <= 1


class Board:
    def __init__(self):
        self.pieces = []
        self.links = []

    def get(self, pos):
        for piece in self.pieces:
            if piece.pos == pos:
                return piece 
        return None

    def setup(self):
        self.pieces = [
            Piece("M", "mu", (0, 1)),
            Piece("M", "t", (0, 2)),
            Piece("M", "W", (0, 3)),
            Piece("M", "e", (1, 1)),
            Piece("M", "e", (1, 4)),
            Piece("A", "mu", (5, 1)),
            Piece("A", "t", (5, 2)),
            Piece("A", "W", (5, 3)),
            Piece("A", "e", (4, 1)),
            Piece("A", "e", (4, 4)),
        ]

    def show(self):
        for row in range(SIZE - 1, -1, -1):
            cells = []
            for col in range(SIZE):
                piece = self.get((row, col))
                if piece is None:
                    cells.append(".")
                else:
                    cells.append(LABELS.get((piece.side, piece.kind), piece.kind))
            print(str(row + 1) + "  " + " ".join(cell.ljust(3) for cell in cells))
        print("   " + " ".join(letter.ljust(3) for letter in "abcdef"))

    def is_free(self, pos):
        return on_board(pos) and self.get(pos) is None

    def reachable(self, piece):
        row, col = piece.pos
        result = []
        if piece.kind == "t":
            steps = ORTHOGONAL
        elif piece.kind in ("e", "cp"):
            steps = ALL_EIGHT
        elif piece.kind == "W":
            steps = KNIGHT
        elif piece.kind == "mu":
            for dr, dc in ALL_EIGHT:
                one = (row + dr, col + dc)
                if on_board(one):
                    result.append(one)
                    if self.get(one) is None:
                        two = (row + 2 * dr, col + 2 * dc)
                        if on_board(two):
                            result.append(two)
            return result
        else:
            return result
        for dr, dc in steps:
            if on_board((row + dr, col + dc)):
                result.append((row + dr, col + dc))
        return result

    def moves(self, piece):
        result = [dest for dest in self.reachable(piece) if self.get(dest) is None]
        if is_fermion(piece):
            result = [dest for dest in result if not self.breaks_exclusion(piece, dest)]
        return result

    def targets(self, piece):
        result = []
        for dest in self.reachable(piece):
            other = self.get(dest)
            if other is not None and other.side != piece.side:
                result.append(other)
        return result

    def move(self, piece, pos):
        if pos not in self.moves(piece):
            raise ValueError(f"{piece.kind} on {piece.pos} cannot move to {pos}: illegal square")
        piece.pos = pos

    def annihilate(self, attacker, target):
        if target not in self.targets(attacker):
            raise ValueError(f"{attacker.kind} on {attacker.pos} cannot annihilate the piece on {target.pos}")
        self.pieces.remove(attacker)
        self.pieces.remove(target)
        removed = [attacker, target]
        for piece in list(self.pieces):
            if is_fermion(piece) and adjacent(piece.pos, target.pos):
                self.pieces.remove(piece)
                removed.append(piece)
        return removed

    def breaks_exclusion(self, piece, dest):
        for other in self.pieces:
            if other is piece:
                continue
            if other.side == piece.side and other.kind == piece.kind and adjacent(dest, other.pos):
                return True
        return False
