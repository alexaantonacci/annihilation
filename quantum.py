import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from pieces import Piece

POWERUPS = ['Interference', 'Cooper Pair', 'Teleport', 'Bell Link']

sim = AerSimulator()
seed = None


def set_seed(s):
    global seed
    seed = s


def run_once(qc):
    global seed
    result = sim.run(transpile(qc, sim), shots=1, memory=True, seed_simulator=seed).result()
    if seed is not None:
        seed = seed + 1
    return result.get_memory()[0]


def counts(qc, shots=1024):
    return sim.run(transpile(qc, sim), shots=shots, seed_simulator=seed).result().get_counts()


def fork_circuit(fixed=None):
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    # Interference: fixed=0 gives HH = I (target A), fixed=1 gives HZH = X (target B)
    if fixed == 0:
        qc.h(0)
    if fixed == 1:
        qc.z(0)
        qc.h(0)
    qc.measure(0, 0)
    return qc


def fork_measure(fixed=None):
    qc = fork_circuit(fixed)
    return int(run_once(qc)), qc


def qrng_circuit():
    qc = QuantumCircuit(2, 2)
    qc.h([0, 1])
    qc.measure([0, 1], [0, 1])
    return qc


def qrng_draw():
    qc = qrng_circuit()
    return int(run_once(qc), 2), qc


def bell_circuit():
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def bell_pair():
    qc = bell_circuit()
    return run_once(qc), qc


def teleport_circuit(theta, phi):
    qc = QuantumCircuit(3, 1)
    qc.u(theta, phi, 0, 2)
    qc.barrier()
    qc.h(1)
    qc.cx(1, 0)
    qc.cx(2, 1)
    qc.h(2)
    qc.cx(1, 0)
    qc.cz(2, 0)
    qc.barrier()
    qc.u(-theta, 0, -phi, 0)
    qc.measure(0, 0)
    return qc


def teleport(theta=None, phi=None):
    if theta is None:
        theta = np.random.uniform(0, np.pi)
    if phi is None:
        phi = np.random.uniform(0, 2*np.pi)
    qc = teleport_circuit(theta, phi)
    return run_once(qc) == '0', qc


def dist(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def remove_piece(board, piece):
    # assumes board.get reads from board.pieces and piece.pos
    for i in range(len(board.pieces)):
        if board.pieces[i] is piece:
            board.pieces.pop(i)
            break
    new_links = []
    for link in board.links:
        if link[0] is not piece and link[1] is not piece:
            new_links.append(link)
    board.links = new_links


def apply_interference(piece, choice):
    if piece.fork is None:
        raise ValueError('That piece has no active fork.')
    if choice == 'A' or choice == 0:
        piece.fork_fixed = 0
    elif choice == 'B' or choice == 1:
        piece.fork_fixed = 1
    else:
        raise ValueError('Choose A or B.')


def make_cooper_pair(board, e1, e2, square):
    if e1 is e2 or e1.kind != 'e' or e2.kind != 'e':
        raise ValueError('A Cooper pair needs two different electrons.')
    if e1.side != e2.side:
        raise ValueError('Both electrons must be on your side.')
    if e1.fork is not None or e2.fork is not None:
        raise ValueError('An electron with an active fork cannot pair.')
    if dist(e1.pos, e2.pos) > 2:
        raise ValueError('The electrons must be within 2 squares of each other.')
    if square != e1.pos and square != e2.pos:
        raise ValueError('Place the Cooper pair on one of the two electrons squares.')
    remove_piece(board, e1)
    remove_piece(board, e2)
    cp = Piece(e1.side, 'cp', square, lives=2)
    board.pieces.append(cp)
    return cp


def teleport_piece(board, piece, dest):
    r, c = dest
    if r < 0 or r > 5 or c < 0 or c > 5:
        raise ValueError('That square is off the board.')
    if board.get(dest) is not None:
        raise ValueError('That square is occupied.')
    friend = False
    for p in board.pieces:
        if p is not piece and p.side == piece.side and dist(p.pos, dest) == 1:
            friend = True
    if not friend:
        raise ValueError('Teleport needs an empty square next to another of your pieces.')
    if board.breaks_exclusion(piece, dest):
        raise ValueError('That square breaks Pauli exclusion.')
    piece.pos = dest
    return teleport()


def add_link(board, p1, p2, player=None):
    if p1 is p2:
        raise ValueError('Choose two different pieces.')
    if p1.kind == 't' or p2.kind == 't':
        raise ValueError('A top quark cannot be linked.')
    if p1.side != p2.side:
        raise ValueError('Both pieces must be on the same side.')
    if player is not None and p1.side == player:
        raise ValueError('Bell Link must target enemy pieces.')
    if dist(p1.pos, p2.pos) > 3:
        raise ValueError('The pieces must be within 3 squares of each other.')
    for a, b in board.links:
        if (a is p1 and b is p2) or (a is p2 and b is p1):
            raise ValueError('Those pieces are already linked.')
    board.links.append((p1, p2))
