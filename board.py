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

    def moves(self, piece):
        row, col = piece.pos
        result = []
        if piece.kind == "t":
            for dr, dc in ORTHOGONAL:
                if self.is_free((row + dr, col + dc)):
                    result.append((row + dr, col + dc))
        elif piece.kind in ("e", "cp"):
            for dr, dc in ALL_EIGHT:
                if self.is_free((row + dr, col + dc)):
                    result.append((row + dr, col + dc))
        elif piece.kind == "mu":
            for dr, dc in ALL_EIGHT:
                one = (row + dr, col + dc)
                if self.is_free(one):
                    result.append(one)
                    two = (row + 2 * dr, col + 2 * dc)
                    if self.is_free(two):
                        result.append(two)
        elif piece.kind == "W":
            for dr, dc in KNIGHT:
                if self.is_free((row + dr, col + dc)):
                    result.append((row + dr, col + dc))
        return result
