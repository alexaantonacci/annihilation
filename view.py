from board import Board, LABELS, SIZE
from pieces import Piece


def square_name(pos):
    row, col = pos
    return "abcdef"[col] + str(row + 1)


def show_with_marks(board, marks):
    for row in range(SIZE - 1, -1, -1):
        cells = []
        for col in range(SIZE):
            piece = board.get((row, col))
            if piece is not None:
                cells.append(LABELS.get((piece.side, piece.kind), piece.kind))
            elif (row, col) in marks:
                cells.append("*")
            else:
                cells.append(".")
        print(str(row + 1) + "  " + " ".join(cell.ljust(3) for cell in cells))
    print("   " + " ".join(letter.ljust(3) for letter in "abcdef"))


print("=== 1. Starting board ===")
board = Board()
board.setup()
board.show()

print()
print("=== 2. Legal moves of each matter piece ===")
for piece in board.pieces:
    if piece.side == "M":
        moves = sorted(square_name(pos) for pos in board.moves(piece))
        print(piece.kind.ljust(3), "on", square_name(piece.pos) + ":", ", ".join(moves))

print()
print("=== 3. Matter muon's moves marked with * ===")
muon = board.get((0, 1))
show_with_marks(board, board.moves(muon))

print()
print("=== 4. Worked example: targets of the muon on c3 ===")
example = Board()
example_muon = Piece(side="M", kind="mu", pos=(2, 2))
example.pieces.append(example_muon)
example.pieces.append(Piece(side="A", kind="e", pos=(4, 0)))
example.pieces.append(Piece(side="A", kind="t", pos=(4, 2)))
example.show()
targets = sorted(square_name(target.pos) for target in example.targets(example_muon))
print("Muon on c3 can target:", ", ".join(targets))
