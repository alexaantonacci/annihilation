import random

import pytest

import quantum as q
from board import Board
from game import GameState, parse_square, square_name
from pieces import Piece


@pytest.fixture(autouse=True)
def seeded():
    q.set_seed(1234)
    yield
    q.set_seed(None)


def custom_game(*pieces, **kwargs):
    """A game on a hand-made board. Both tops are added out of the way."""
    board = Board()
    board.pieces.append(Piece("M", "t", (0, 5)))
    board.pieces.append(Piece("A", "t", (5, 5)))
    board.pieces.extend(pieces)
    return GameState(board=board, **kwargs)


def snapshot(game):
    return (
        [(p.side, p.kind, p.pos, p.lives, p.fork_fixed) for p in game.board.pieces],
        len(game.board.links), game.turn, dict(game.turn_count),
        {s: list(h) for s, h in game.hands.items()}, game.phase, game.offer,
    )


def test_squares():
    assert parse_square("a1") == (0, 0)
    assert parse_square("F6") == (5, 5)
    assert square_name((1, 4)) == "e2"
    for bad in ("g1", "a7", "a", "a10"):
        with pytest.raises(ValueError):
            parse_square(bad)


def test_new_game():
    game = GameState()
    assert len(game.board.pieces) == 10
    assert game.turn == "M"
    assert game.phase == "action"
    assert game.turn_count == {"M": 1, "A": 0}
    assert not game.over


def test_move_passes_turn():
    game = GameState()
    game.command("move c1 c2")
    assert game.board.get((1, 2)).kind == "t"
    assert game.turn == "A"


@pytest.mark.parametrize("text", [
    "", "dance", "move c1", "move c1 c4", "move c6 c5", "move a3 a4",
    "move z9 a1", "attack c1 c6", "fork b1 a1 b2", "keep 1", "power teleport b1 e1",
    "power", "power warp b1 e1", "pass now",
])
def test_bad_command_changes_nothing(text):
    game = GameState()
    before = snapshot(game)
    with pytest.raises(ValueError):
        game.command(text)
    assert snapshot(game) == before


def test_attack_single_target():
    game = custom_game(Piece("M", "e", (2, 2)), Piece("A", "e", (3, 3)))
    game.command("attack c3 d4")
    assert game.board.get((2, 2)) is None
    assert game.board.get((3, 3)) is None
    assert game.turn == "A"


def test_attack_with_two_targets_asks_for_fork():
    game = custom_game(Piece("M", "e", (2, 2)), Piece("A", "e", (3, 3)), Piece("A", "W", (3, 1)))
    before = snapshot(game)
    with pytest.raises(ValueError, match="fork"):
        game.command("attack c3 d4")
    assert snapshot(game) == before


def setup_fork(fixed):
    mu = Piece("M", "mu", (2, 2))
    ea = Piece("A", "e", (4, 0))
    wb = Piece("A", "W", (2, 4))
    game = custom_game(mu, ea, wb, Piece("A", "mu", (5, 2)))
    game.command("fork c3 a5 e3")
    assert mu.fork == (ea, wb)
    assert game.turn == "A"
    game.hands["A"] = ["Interference"]
    game.command(f"power interference c3 {fixed}")
    assert mu.fork_fixed == "ab".index(fixed)
    assert game.turn == "A"
    return game, mu, ea, wb


def test_fork_hits_at_start_of_next_turn():
    game, mu, ea, wb = setup_fork("b")
    game.command("move c6 c5")
    assert wb not in game.board.pieces
    assert ea in game.board.pieces
    assert mu.fork is None
    assert game.turn == "M"
    assert game.phase == "action"


def test_fork_miss_loses_whole_turn():
    game, mu, ea, wb = setup_fork("b")
    game.command("move e3 d5")
    assert game.turn == "A"
    assert game.turn_count == {"M": 2, "A": 2}
    assert wb in game.board.pieces
    assert mu.fork is None


def test_fork_miss_loses_power_up_draw():
    game, mu, ea, wb = setup_fork("a")
    game.turn_count["M"] = 2
    game.command("move a5 a6")
    assert game.turn == "A"
    assert game.turn_count["M"] == 3
    assert game.hands["M"] == []
    assert game.phase == "action"


def test_fork_on_top_wins():
    mu = Piece("M", "mu", (2, 2))
    top = Piece("A", "t", (4, 2))
    board = Board()
    board.pieces += [Piece("M", "t", (0, 5)), mu, top, Piece("A", "W", (4, 0))]
    game = GameState(board=board)
    game.command("fork c3 c5 a5")
    game.hands["A"] = ["Interference"]
    game.command("power interference c3 a")
    game.command("move a5 b3")
    assert game.over and game.winner == "M"


def test_draw_schedule_and_hand_limit():
    game = GameState()
    moves = ["move c1 c2", "move c6 c5", "move c2 c1", "move c5 c6"]
    for text in moves:
        game.command(text)
    assert game.turn == "M" and game.turn_count["M"] == 3
    assert game.phase == "draw"
    assert len(game.offer) == 2 and set(game.offer) <= set(q.POWERUPS)
    with pytest.raises(ValueError):
        game.command("move c1 c2")
    first = game.offer[0]
    game.command("keep 1")
    assert game.hands["M"] == [first]
    assert game.phase == "action"
    game.command("move c1 c2")
    assert game.phase == "draw"
    game.command("skip")
    assert game.hands["A"] == []
    game.command("move c6 c5")
    assert game.phase == "action"
    game.command("move c2 c1")
    game.command("move c5 c6")
    game.command("keep 2")
    assert len(game.hands["M"]) == 2
    game.command("move c1 c2")
    game.command("skip")
    game.command("move c6 c5")
    game.command("move c2 c1")
    game.command("move c5 c6")
    assert game.turn_count["M"] == 7 and game.phase == "draw"
    with pytest.raises(ValueError, match="full"):
        game.command("keep 1")
    old, kept = list(game.hands["M"]), game.offer[0]
    game.command("keep 1 drop 1")
    assert game.hands["M"] == [old[1], kept]


def test_teleport_uses_the_action():
    game = GameState()
    game.hands["M"] = ["Teleport"]
    game.command("power teleport b1 e1")
    assert game.board.get((0, 4)).kind == "mu"
    assert game.hands["M"] == []
    assert game.turn == "A"


def test_free_power_ups_keep_the_turn():
    game = GameState()
    game.hands["M"] = ["Bell Link", "Cooper Pair"]
    with pytest.raises(ValueError, match="enemy"):
        game.command("power bell b2 b1")
    game.command("power bell b5 b6")
    assert len(game.board.links) == 1
    game.command("move e2 d2")
    game.hands["M"] = ["Cooper Pair"]
    game.command("move c6 c5")
    game.command("power cooper b2 d2 d2")
    cp = game.board.get((1, 3))
    assert cp.kind == "cp" and cp.lives == 2
    assert game.turn == "M" and game.hands["M"] == []


def test_only_one_power_up_per_turn():
    game = GameState()
    game.hands["M"] = ["Bell Link", "Teleport"]
    with pytest.raises(ValueError, match="enemy"):
        game.command("power bell b2 b1")
    game.command("power bell b5 b6")
    assert not any(c.startswith("power ") for c in game.legal_commands())
    before = snapshot(game)
    with pytest.raises(ValueError, match="already"):
        game.command("power teleport b1 e1")
    assert snapshot(game) == before
    game.command("move c1 c2")
    game.command("move c6 c5")
    assert not game.power_used
    game.command("power teleport b1 e1")
    assert game.board.get((0, 4)).kind == "mu"
    assert game.turn == "A"


def test_free_power_up_then_one_action():
    game = GameState()
    game.hands["M"] = ["Bell Link"]
    game.command("power bell b5 b6")
    assert game.turn == "M"
    game.command("move c1 c2")
    assert game.turn == "A"


def test_pass_is_always_legal():
    game = GameState()
    assert "pass" in game.legal_commands()
    before = [(p.side, p.kind, p.pos) for p in game.board.pieces]
    game.command("pass")
    assert game.turn == "A"
    assert [(p.side, p.kind, p.pos) for p in game.board.pieces] == before
    game.hands["A"] = ["Bell Link"]
    game.command("power bell b2 e2")
    assert "pass" in game.legal_commands()
    game.command("pass")
    assert game.turn == "M"
    with pytest.raises(ValueError):
        game.command("pass b2")


def test_use_is_an_alias_for_power():
    game = GameState()
    game.hands["M"] = ["Teleport"]
    game.command("use teleport b1 e1")
    assert game.board.get((0, 4)).kind == "mu"
    assert game.turn == "A"


def test_legal_commands_use_power():
    game = GameState()
    game.hands["M"] = ["Teleport"]
    options = game.legal_commands()
    assert "power teleport b1 e1" in options
    assert not any(c.startswith("use ") for c in options)


def test_power_up_not_in_hand():
    game = GameState()
    with pytest.raises(ValueError, match="no Teleport"):
        game.command("power teleport b1 e1")


def test_cooper_pair_needs_two_hits():
    cp = Piece("A", "cp", (3, 3), lives=2)
    game = custom_game(Piece("M", "e", (2, 2)), Piece("M", "W", (1, 2)), cp)
    game.command("attack c3 d4")
    assert game.board.get((3, 3)) is cp
    assert cp.kind == "e" and cp.lives == 1
    assert game.board.get((2, 2)) is None
    game.command("move f6 f5")
    game.command("attack c2 d4")
    assert cp not in game.board.pieces
    assert game.board.get((3, 3)) is None


def test_fork_still_hits_cooper_pair_after_first_hit():
    mu = Piece("M", "mu", (2, 2))
    cp = Piece("A", "cp", (4, 2), lives=2)
    game = custom_game(mu, cp, Piece("A", "W", (4, 0)), Piece("M", "W", (5, 3)))
    game.command("fork c3 c5 a5")
    mu.fork_fixed = 0
    # the cp attacks, survives as the same object with kind 'e', then the fork measures
    game.command("attack c5 d6")
    assert cp.kind == "e" and cp.lives == 1
    assert any("hit" in line for line in game.log)
    assert cp not in game.board.pieces
    assert mu not in game.board.pieces
    assert game.turn == "M"


def test_bell_partner_removed_with_target():
    me = Piece("M", "e", (2, 2))
    mw = Piece("M", "W", (0, 0))
    ae = Piece("A", "e", (3, 3))
    game = custom_game(me, mw, ae, Piece("M", "mu", (1, 0)))
    game.command("move a2 a3")
    game.hands["A"] = ["Bell Link"]
    game.command("power bell c3 a1")
    game.command("attack d4 c3")
    assert me not in game.board.pieces
    assert mw not in game.board.pieces
    assert game.board.links == []


def test_bell_partner_removed_by_burst():
    burned = Piece("M", "mu", (1, 3))
    partner = Piece("M", "W", (0, 0))
    game = custom_game(Piece("M", "e", (1, 2)), burned, partner, Piece("A", "e", (3, 1)))
    game.command("move c2 c3")
    game.hands["A"] = ["Bell Link"]
    game.command("power bell d2 a1")
    removed_before = len(game.board.pieces)
    game.command("attack b4 c3")
    assert burned not in game.board.pieces
    assert partner not in game.board.pieces
    assert len(game.board.pieces) == removed_before - 4
    assert game.board.links == []


def test_top_destroyed_wins():
    game = custom_game(Piece("M", "e", (4, 4)))
    game.command("attack e5 f6")
    assert game.over and game.winner == "M"
    with pytest.raises(ValueError):
        game.command("move a1 a2")


def test_round_limit_draw():
    game = GameState(rounds=1)
    game.command("move c1 c2")
    assert not game.over
    game.command("move c6 c5")
    assert game.over and game.winner is None


def test_round_limit_score_wins():
    game = custom_game(Piece("M", "W", (0, 0)), rounds=1)
    game.command("move a1 b3")
    game.command("move f6 f5")
    assert game.over and game.winner == "M"


def test_status_and_show(capsys):
    game = GameState()
    game.show()
    out = capsys.readouterr().out
    assert "Matter to play" in out and "Score  M 8 : A 8" in out


@pytest.mark.parametrize("seed", range(5))
def test_full_random_game_runs_to_the_end(seed):
    q.set_seed(seed)
    rng = random.Random(seed)
    game = GameState()
    for _ in range(2000):
        if game.over:
            break
        options = game.legal_commands()
        assert options
        game.command(rng.choice(options))
    assert game.over
    assert game.turn_count["A"] <= 20
