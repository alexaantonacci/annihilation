SIZE = 6


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
