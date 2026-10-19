from pieces import Piece


def test_make_piece():
    electron = Piece(side="matter", kind="e", pos=(1, 1))
    assert electron.lives == 1
    assert electron.fork is None
