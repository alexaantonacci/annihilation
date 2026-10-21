import pytest

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


def test_setup_has_ten_pieces():
    board = Board()
    board.setup()
    assert len(board.pieces) == 10
    matter = [piece for piece in board.pieces if piece.side == "M"]
    antimatter = [piece for piece in board.pieces if piece.side == "A"]
    assert len(matter) == 5
    assert len(antimatter) == 5


def test_setup_squares():
    board = Board()
    board.setup()
    expected = [
        ("M", "mu", (0, 1)),
        ("M", "t", (0, 2)),
        ("M", "W", (0, 3)),
        ("M", "e", (1, 1)),
        ("M", "e", (1, 4)),
        ("A", "mu", (5, 1)),
        ("A", "t", (5, 2)),
        ("A", "W", (5, 3)),
        ("A", "e", (4, 1)),
        ("A", "e", (4, 4)),
    ]
    for side, kind, pos in expected:
        piece = board.get(pos)
        assert piece is not None, f"no piece on {pos}"
        assert piece.side == side, f"wrong side on {pos}"
        assert piece.kind == kind, f"wrong kind on {pos}"


def test_setup_empty_middle():
    board = Board()
    board.setup()
    for row in (2, 3):
        for col in range(6):
            assert board.get((row, col)) is None, f"{(row, col)} should be empty"


def test_moves_top_quark():
    board = Board()
    board.setup()
    piece = board.get((0, 2))
    assert set(board.moves(piece)) == {(1, 2)}


def test_moves_electron_b2():
    board = Board()
    board.setup()
    piece = board.get((1, 1))
    assert set(board.moves(piece)) == {(0, 0), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)}


def test_moves_electron_e2():
    board = Board()
    board.setup()
    piece = board.get((1, 4))
    assert set(board.moves(piece)) == {
        (0, 4), (0, 5), (1, 3), (1, 5), (2, 3), (2, 4), (2, 5)
    }


def test_moves_muon():
    board = Board()
    board.setup()
    piece = board.get((0, 1))
    assert set(board.moves(piece)) == {(0, 0), (1, 0), (1, 2), (2, 3)}


def test_moves_W():
    board = Board()
    board.setup()
    piece = board.get((0, 3))
    assert set(board.moves(piece)) == {(1, 5), (2, 2), (2, 4)}


def test_exclusion_same_side_electrons():
    board = Board()
    electron = Piece(side="M", kind="e", pos=(2, 2))
    board.pieces.append(electron)
    board.pieces.append(Piece(side="M", kind="e", pos=(2, 4)))
    assert set(board.moves(electron)) == {(1, 1), (1, 2), (2, 1), (3, 1), (3, 2)}


def test_exclusion_enemy_electron_ok():
    board = Board()
    electron = Piece(side="M", kind="e", pos=(2, 2))
    board.pieces.append(electron)
    board.pieces.append(Piece(side="A", kind="e", pos=(2, 4)))
    assert (2, 3) in board.moves(electron)


def test_exclusion_different_kinds_ok():
    board = Board()
    muon = Piece(side="M", kind="mu", pos=(2, 2))
    board.pieces.append(muon)
    board.pieces.append(Piece(side="M", kind="e", pos=(2, 4)))
    assert (2, 3) in board.moves(muon)


def test_targets_worked_example():
    board = Board()
    muon = Piece(side="M", kind="mu", pos=(2, 2))
    board.pieces.append(muon)
    board.pieces.append(Piece(side="A", kind="e", pos=(4, 0)))
    board.pieces.append(Piece(side="A", kind="t", pos=(4, 2)))
    assert {p.pos for p in board.targets(muon)} == {(4, 0), (4, 2)}


def test_targets_blocked_by_friend():
    board = Board()
    muon = Piece(side="M", kind="mu", pos=(2, 2))
    board.pieces.append(muon)
    board.pieces.append(Piece(side="M", kind="e", pos=(3, 2)))
    board.pieces.append(Piece(side="A", kind="t", pos=(4, 2)))
    assert (4, 2) not in {p.pos for p in board.targets(muon)}


def test_targets_W_jumps():
    board = Board()
    w_boson = Piece(side="M", kind="W", pos=(0, 3))
    board.pieces.append(w_boson)
    board.pieces.append(Piece(side="M", kind="e", pos=(1, 3)))
    board.pieces.append(Piece(side="M", kind="e", pos=(1, 4)))
    board.pieces.append(Piece(side="A", kind="e", pos=(2, 4)))
    assert {p.pos for p in board.targets(w_boson)} == {(2, 4)}


def test_targets_ignore_exclusion():
    board = Board()
    electron = Piece(side="M", kind="e", pos=(2, 2))
    board.pieces.append(electron)
    board.pieces.append(Piece(side="M", kind="e", pos=(2, 4)))
    board.pieces.append(Piece(side="A", kind="e", pos=(3, 3)))
    assert (3, 3) in {p.pos for p in board.targets(electron)}


def test_targets_start_position():
    board = Board()
    board.setup()
    for piece in board.pieces:
        assert {p.pos for p in board.targets(piece)} == set(), f"{piece.pos} should have no targets"


def test_move_legal():
    board = Board()
    board.setup()
    top = board.get((0, 2))
    board.move(top, (1, 2))
    assert top.pos == (1, 2)
    assert board.get((1, 2)) is top
    assert board.get((0, 2)) is None


def test_move_illegal():
    board = Board()
    board.setup()
    top = board.get((0, 2))
    with pytest.raises(ValueError):
        board.move(top, (3, 2))
    assert top.pos == (0, 2)


def test_annihilate_removes_both():
    board = Board()
    matter_e = Piece(side="M", kind="e", pos=(2, 2))
    anti_e = Piece(side="A", kind="e", pos=(3, 3))
    board.pieces.append(matter_e)
    board.pieces.append(anti_e)
    removed = board.annihilate(matter_e, anti_e)
    assert matter_e not in board.pieces
    assert anti_e not in board.pieces
    assert matter_e in removed
    assert anti_e in removed


def test_burst_kills_fermions_spares_bosons():
    board = Board()
    muon = Piece(side="M", kind="mu", pos=(2, 2))
    anti_mu = Piece(side="A", kind="mu", pos=(4, 2))
    w_boson = Piece(side="A", kind="W", pos=(5, 3))
    board.pieces.append(muon)
    board.pieces.append(anti_mu)
    board.pieces.append(Piece(side="A", kind="e", pos=(5, 1)))
    board.pieces.append(w_boson)
    board.pieces.append(Piece(side="M", kind="e", pos=(3, 3)))
    removed = board.annihilate(muon, anti_mu)
    assert {p.pos for p in removed} == {(2, 2), (4, 2), (5, 1), (3, 3)}
    assert w_boson in board.pieces


def test_no_burst_without_pair():
    board = Board()
    muon = Piece(side="M", kind="mu", pos=(2, 2))
    anti_t = Piece(side="A", kind="t", pos=(4, 2))
    bystander = Piece(side="M", kind="e", pos=(3, 3))
    board.pieces.append(muon)
    board.pieces.append(anti_t)
    board.pieces.append(bystander)
    removed = board.annihilate(muon, anti_t)
    assert {p.pos for p in removed} == {(2, 2), (4, 2)}
    assert bystander in board.pieces


def test_cooper_pair_counts_as_electron_pair():
    board = Board()
    positron = Piece(side="A", kind="e", pos=(2, 3))
    pair = Piece(side="M", kind="cp", pos=(1, 2), lives=2)
    bystander = Piece(side="A", kind="mu", pos=(0, 2))
    board.pieces.append(positron)
    board.pieces.append(pair)
    board.pieces.append(bystander)
    board.annihilate(positron, pair)
    assert bystander not in board.pieces
    assert pair.kind == "e"


def test_burst_no_chain():
    board = Board()
    matter_e = Piece(side="M", kind="e", pos=(1, 1))
    anti_e = Piece(side="A", kind="e", pos=(2, 2))
    near_mu = Piece(side="A", kind="mu", pos=(3, 3))
    far_mu = Piece(side="M", kind="mu", pos=(4, 4))
    board.pieces.append(matter_e)
    board.pieces.append(anti_e)
    board.pieces.append(near_mu)
    board.pieces.append(far_mu)
    board.annihilate(matter_e, anti_e)
    assert near_mu not in board.pieces
    assert far_mu in board.pieces


def test_annihilate_out_of_range():
    board = Board()
    board.setup()
    matter_t = board.get((0, 2))
    anti_t = board.get((5, 2))
    with pytest.raises(ValueError):
        board.annihilate(matter_t, anti_t)
    assert len(board.pieces) == 10


def test_cooper_pair_target_loses_life():
    board = Board()
    cp = Piece(side="A", kind="cp", pos=(2, 2), lives=2)
    matter_e = Piece(side="M", kind="e", pos=(1, 1))
    anti_mu = Piece(side="A", kind="mu", pos=(3, 3))
    board.pieces.append(cp)
    board.pieces.append(matter_e)
    board.pieces.append(anti_mu)
    removed = board.annihilate(matter_e, cp)
    assert matter_e not in board.pieces
    assert board.get((2, 2)) is cp
    assert cp.kind == "e"
    assert cp.lives == 1
    assert anti_mu not in board.pieces
    assert cp not in removed


def test_cooper_pair_attacker_loses_life():
    board = Board()
    cp = Piece(side="M", kind="cp", pos=(2, 2), lives=2)
    anti_e = Piece(side="A", kind="e", pos=(3, 2))
    board.pieces.append(cp)
    board.pieces.append(anti_e)
    removed = board.annihilate(cp, anti_e)
    assert anti_e not in board.pieces
    assert board.get((2, 2)) is cp
    assert cp.kind == "e"
    assert cp.lives == 1
    assert cp not in removed


def test_bell_link_partner_removed():
    board = Board()
    matter_e = Piece(side="M", kind="e", pos=(2, 2))
    anti_e = Piece(side="A", kind="e", pos=(3, 3))
    linked_mu = Piece(side="A", kind="mu", pos=(5, 5))
    bystander = Piece(side="A", kind="e", pos=(4, 5))
    board.pieces.append(matter_e)
    board.pieces.append(anti_e)
    board.pieces.append(linked_mu)
    board.pieces.append(bystander)
    board.links.append((anti_e, linked_mu))
    removed = board.annihilate(matter_e, anti_e)
    assert linked_mu not in board.pieces
    assert linked_mu in removed
    assert bystander in board.pieces


def test_bell_link_via_burst():
    board = Board()
    matter_e = Piece(side="M", kind="e", pos=(1, 1))
    anti_e = Piece(side="A", kind="e", pos=(2, 2))
    anti_mu = Piece(side="A", kind="mu", pos=(3, 3))
    linked_w = Piece(side="A", kind="W", pos=(5, 0))
    board.pieces.append(matter_e)
    board.pieces.append(anti_e)
    board.pieces.append(anti_mu)
    board.pieces.append(linked_w)
    board.links.append((anti_mu, linked_w))
    removed = board.annihilate(matter_e, anti_e)
    assert anti_mu not in board.pieces
    assert linked_w not in board.pieces
    assert linked_w in removed


def test_bell_link_cleared():
    board = Board()
    matter_e = Piece(side="M", kind="e", pos=(2, 2))
    anti_e = Piece(side="A", kind="e", pos=(3, 3))
    linked_mu = Piece(side="A", kind="mu", pos=(5, 5))
    board.pieces.append(matter_e)
    board.pieces.append(anti_e)
    board.pieces.append(linked_mu)
    link = (anti_e, linked_mu)
    board.links.append(link)
    board.annihilate(matter_e, anti_e)
    assert link not in board.links


def test_bell_link_chain():
    board = Board()
    matter_e = Piece(side="M", kind="e", pos=(2, 2))
    anti_e = Piece(side="A", kind="e", pos=(3, 3))
    anti_mu = Piece(side="A", kind="mu", pos=(5, 0))
    anti_w = Piece(side="A", kind="W", pos=(0, 5))
    board.pieces.append(matter_e)
    board.pieces.append(anti_e)
    board.pieces.append(anti_mu)
    board.pieces.append(anti_w)
    first_link = (anti_e, anti_mu)
    second_link = (anti_mu, anti_w)
    board.links.append(second_link)
    board.links.append(first_link)
    removed = board.annihilate(matter_e, anti_e)
    assert anti_mu not in board.pieces
    assert anti_w not in board.pieces
    assert anti_mu in removed
    assert anti_w in removed
    assert first_link not in board.links
    assert second_link not in board.links


def test_winner_none_at_start():
    board = Board()
    board.setup()
    assert board.winner("M") is None


def test_winner_antitop_gone():
    board = Board()
    board.setup()
    board.pieces.remove(board.get((5, 2)))
    assert board.winner("M") == "M"


def test_winner_top_gone():
    board = Board()
    board.setup()
    board.pieces.remove(board.get((0, 2)))
    assert board.winner("A") == "A"


def test_winner_both_gone():
    board = Board()
    board.setup()
    board.pieces.remove(board.get((0, 2)))
    board.pieces.remove(board.get((5, 2)))
    assert board.winner("M") == "A"
    assert board.winner("A") == "M"


def test_score_start():
    board = Board()
    board.setup()
    assert board.score("M") == 8
    assert board.score("A") == 8


def test_score_values():
    board = Board()
    board.pieces.append(Piece(side="M", kind="cp", pos=(0, 0)))
    board.pieces.append(Piece(side="M", kind="W", pos=(0, 1)))
    board.pieces.append(Piece(side="M", kind="mu", pos=(0, 2)))
    board.pieces.append(Piece(side="M", kind="e", pos=(0, 3)))
    board.pieces.append(Piece(side="M", kind="t", pos=(0, 4)))
    assert board.score("M") == 9


def test_bell_link_stale_partner():
    board = Board()
    matter_e = Piece(side="M", kind="e", pos=(2, 2))
    anti_e = Piece(side="A", kind="e", pos=(3, 3))
    gone_mu = Piece(side="A", kind="mu", pos=(5, 5))
    board.pieces.append(matter_e)
    board.pieces.append(anti_e)
    link = (anti_e, gone_mu)
    board.links.append(link)
    removed = board.annihilate(matter_e, anti_e)
    assert gone_mu not in removed
    assert link not in board.links
