import numpy as np
import pytest

import quantum as q
from board import Board


@pytest.fixture
def board():
    b = Board()
    b.setup()
    return b


@pytest.fixture(autouse=True)
def seeded():
    q.set_seed(1234)
    yield
    q.set_seed(None)


def test_fork_plain_is_fifty_fifty():
    c = q.counts(q.fork_circuit(), shots=4000)
    assert 0.46 < c.get('0', 0) / 4000 < 0.54


@pytest.mark.parametrize('fixed', [0, 1])
def test_fork_fixed_is_certain(fixed):
    assert q.counts(q.fork_circuit(fixed), shots=500) == {str(fixed): 500}
    for _ in range(20):
        assert q.fork_measure(fixed)[0] == fixed


def test_qrng_is_uniform():
    c = q.counts(q.qrng_circuit(), shots=8000)
    for key in ['00', '01', '10', '11']:
        assert 0.22 < c.get(key, 0) / 8000 < 0.28
    i, qc = q.qrng_draw()
    assert 0 <= i <= 3


def test_bell_pair_always_agrees():
    c = q.counts(q.bell_circuit(), shots=2000)
    assert set(c) <= {'00', '11'}
    bits, qc = q.bell_pair()
    assert bits in ['00', '11']


def test_teleport_delivers_state():
    for _ in range(15):
        theta = np.random.uniform(0, np.pi)
        phi = np.random.uniform(0, 2*np.pi)
        assert q.counts(q.teleport_circuit(theta, phi), shots=200) == {'0': 200}
    ok, qc = q.teleport()
    assert ok


def test_interference_fixes_fork(board):
    mu = board.get((0, 1))
    with pytest.raises(ValueError):
        q.apply_interference(mu, 'A')
    mu.fork = ('target A', 'target B')
    q.apply_interference(mu, 'B')
    assert mu.fork_fixed == 1
    for _ in range(20):
        assert q.fork_measure(mu.fork_fixed)[0] == 1
    with pytest.raises(ValueError):
        q.apply_interference(mu, 'C')


def test_cooper_pair_forms(board):
    e1 = board.get((1, 1))
    e2 = board.get((1, 4))
    with pytest.raises(ValueError, match='within 2'):
        q.make_cooper_pair(board, e1, e2, e1.pos)
    board.move(e2, (1, 3))
    q.add_link(board, e1, board.get((0, 1)))
    cp = q.make_cooper_pair(board, e1, e2, (1, 3))
    assert board.get((1, 3)) is cp
    assert board.get((1, 1)) is None
    assert cp.kind == 'cp' and cp.lives == 2 and cp.side == 'M'
    assert board.links == []


def test_cooper_pair_rejects_bad_input(board):
    e1 = board.get((1, 1))
    with pytest.raises(ValueError):
        q.make_cooper_pair(board, e1, board.get((0, 1)), e1.pos)
    with pytest.raises(ValueError):
        q.make_cooper_pair(board, e1, board.get((4, 1)), e1.pos)


def test_teleport_piece(board):
    mu = board.get((0, 1))
    ok, qc = q.teleport_piece(board, mu, (0, 4))
    assert ok
    assert board.get((0, 4)) is mu
    assert board.get((0, 1)) is None


def test_teleport_keeps_fork(board):
    mu = board.get((0, 1))
    mu.fork = ('A', 'B')
    q.teleport_piece(board, mu, (0, 4))
    assert mu.fork == ('A', 'B')


def test_teleport_rejects_bad_squares(board):
    mu = board.get((0, 1))
    e1 = board.get((1, 1))
    with pytest.raises(ValueError, match='occupied'):
        q.teleport_piece(board, mu, (0, 2))
    with pytest.raises(ValueError, match='next to'):
        q.teleport_piece(board, mu, (3, 0))
    with pytest.raises(ValueError, match='exclusion'):
        q.teleport_piece(board, e1, (2, 5))
    with pytest.raises(ValueError, match='off the board'):
        q.teleport_piece(board, mu, (6, 0))


def test_bell_link(board):
    ep = board.get((4, 1))
    mup = board.get((5, 1))
    q.add_link(board, ep, mup, player='M')
    assert len(board.links) == 1
    with pytest.raises(ValueError, match='already'):
        q.add_link(board, mup, ep, player='M')


def test_bell_link_rejects_bad_input(board):
    ep = board.get((4, 1))
    with pytest.raises(ValueError, match='top quark'):
        q.add_link(board, ep, board.get((5, 2)), player='M')
    with pytest.raises(ValueError, match='enemy'):
        q.add_link(board, ep, board.get((5, 1)), player='A')
    mu = board.get((0, 1))
    e2 = board.get((1, 4))
    board.move(e2, (1, 5))
    with pytest.raises(ValueError, match='within 3'):
        q.add_link(board, mu, e2, player='A')
