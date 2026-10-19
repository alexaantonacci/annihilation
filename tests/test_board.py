from board import Board, on_board
from pieces import Piece


def test_make_piece():
    electron = Piece(side="matter", kind="e", pos=(1, 1))
    assert electron.lives == 1
    assert electron.fork is None


def test_on_board():
    assert on_board((0, 0))
    assert on_board((5, 5))
    assert not on_board((6, 0))
    assert not on_board((0, 6))
    assert not on_board((-1, 3))


def test_get_finds_piece():
    board = Board()
    electron = Piece(side="matter", kind="e", pos=(1, 1))
    board.pieces.append(electron)
    assert board.get((1, 1)) is electron


def test_get_empty_square():
    board = Board()
    electron = Piece(side="matter", kind="e", pos=(1, 1))
    board.pieces.append(electron)
    assert board.get((3, 3)) is None
