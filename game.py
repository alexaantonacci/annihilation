import quantum as Q
from board import Board, LABELS, SIZE

ROUNDS = 20
HAND_SIZE = 2
NAMES = {"M": "Matter", "A": "Antimatter"}
CARDS = {
    "interference": "Interference",
    "cooper": "Cooper Pair",
    "teleport": "Teleport",
    "bell": "Bell Link",
}


def other(side):
    return "A" if side == "M" else "M"


def parse_square(text):
    text = text.strip().lower()
    if len(text) != 2 or text[0] not in "abcdef" or text[1] not in "123456":
        raise ValueError(f"'{text}' is not a square (use a1 to f6).")
    return int(text[1]) - 1, "abcdef".index(text[0])


def square_name(pos):
    row, col = pos
    return "abcdef"[col] + str(row + 1)


def dist(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def label(piece):
    return LABELS.get((piece.side, piece.kind), piece.kind)


def is_draw_turn(n):
    return n >= 3 and n % 2 == 1


class GameState:
    def __init__(self, board=None, rounds=ROUNDS, first="M"):
        if board is None:
            board = Board()
            board.setup()
        self.board = board
        self.rounds = rounds
        self.turn = first
        self.turn_count = {"M": 0, "A": 0}
        self.hands = {"M": [], "A": []}
        self.offer = None
        self.phase = "action"
        self.power_used = False
        self.over = False
        self.winner = None
        self.log = []
        self.circuits = []
        self._start_turn()

    # ----- turn flow -----

    def _say(self, text):
        self.log.append(text)

    def _start_turn(self):
        while True:
            side = self.turn
            self.turn_count[side] += 1
            self.offer = None
            self.power_used = False
            self._say(f"{NAMES[side]} turn {self.turn_count[side]}.")
            if self._resolve_forks(side):
                break
            if self.over:
                return
            # the fork missed: the whole turn is lost, draw included
            if self._turn_limit_reached():
                return
            self.turn = other(side)
        if self.over:
            return
        if is_draw_turn(self.turn_count[side]):
            self.offer = []
            for _ in range(2):
                index, qc = Q.qrng_draw()
                self.circuits.append(("qrng", qc))
                self.offer.append(Q.POWERUPS[index])
            self.phase = "draw"
            self._say(f"Power-up draw: 1) {self.offer[0]}  2) {self.offer[1]}")
        else:
            self.phase = "action"

    def _resolve_forks(self, side):
        """Measure this side's forks. Returns False if a fork missed."""
        for piece in [p for p in self.board.pieces if p.side == side and p.fork is not None]:
            bit, qc = Q.fork_measure(fixed=piece.fork_fixed)
            self.circuits.append(("fork", qc))
            target = piece.fork[bit]
            piece.fork = None
            piece.fork_fixed = None
            if any(t is target for t in self.board.targets(piece)):
                self._say(f"Fork on {square_name(piece.pos)} collapsed to {label(target)} on "
                          f"{square_name(target.pos)}: hit.")
                self._annihilate(piece, target)
                if self.over:
                    return True
            else:
                self._say(f"Fork on {square_name(piece.pos)} collapsed to {label(target)}: "
                          f"miss, {NAMES[side]} loses the turn.")
                return False
        return True

    def _turn_limit_reached(self):
        if self.turn == "A" and self.turn_count["A"] >= self.rounds:
            self._finish_on_score()
            return True
        return False

    def _end_turn(self):
        if self.over:
            return
        if self._turn_limit_reached():
            return
        self.turn = other(self.turn)
        self._start_turn()

    def _finish_on_score(self):
        self.over = True
        m, a = self.board.score("M"), self.board.score("A")
        self.winner = "M" if m > a else "A" if a > m else None
        result = f"{NAMES[self.winner]} wins" if self.winner else "Draw"
        self._say(f"{self.rounds} rounds played. Score M {m} : A {a}. {result}.")

    def _annihilate(self, attacker, target):
        removed = self.board.annihilate(attacker, target)
        self._say("Removed: " + ", ".join(f"{label(p)} {square_name(p.pos)}" for p in removed))
        winner = self.board.winner(attacker.side)
        if winner is not None:
            self.over = True
            self.winner = winner
            self._say(f"A top quark is gone. {NAMES[winner]} wins.")
        return removed

    # ----- commands -----

    def command(self, text):
        """Run one command. Raises ValueError and changes nothing if it is not legal."""
        if self.over:
            raise ValueError("The game is over.")
        words = text.strip().lower().split()
        if not words:
            raise ValueError("Type a command (try 'help').")
        verb, args = words[0], words[1:]
        if self.phase == "draw":
            if verb == "keep":
                return self._keep(args)
            if verb == "skip" and not args:
                return self._skip()
            raise ValueError("Choose a power-up first: 'keep 1', 'keep 2' or 'skip'.")
        handlers = {"move": self._move, "attack": self._attack, "fork": self._fork,
                    "power": self._power, "use": self._power, "pass": self._pass}
        if verb not in handlers:
            raise ValueError(f"Unknown command '{verb}' (try 'help').")
        return handlers[verb](args)

    def _own_piece(self, text):
        piece = self.board.get(parse_square(text))
        if piece is None:
            raise ValueError(f"There is no piece on {text}.")
        if piece.side != self.turn:
            raise ValueError(f"The piece on {text} is not yours.")
        return piece

    def _piece(self, text):
        piece = self.board.get(parse_square(text))
        if piece is None:
            raise ValueError(f"There is no piece on {text}.")
        return piece

    def _target(self, piece, text):
        target = self.board.get(parse_square(text))
        for t in self.board.targets(piece):
            if t is target:
                return target
        raise ValueError(f"{label(piece)} on {square_name(piece.pos)} cannot reach an enemy on {text}.")

    def _need(self, args, n, usage):
        if len(args) != n:
            raise ValueError(f"Usage: {usage}")

    def _move(self, args):
        self._need(args, 2, "move <from> <to>")
        piece = self._own_piece(args[0])
        self.board.move(piece, parse_square(args[1]))
        self._say(f"{label(piece)} moved to {args[1]}.")
        self._end_turn()

    def _attack(self, args):
        self._need(args, 2, "attack <from> <target>")
        piece = self._own_piece(args[0])
        if len(self.board.targets(piece)) >= 2:
            raise ValueError("Two or more enemies are in range: use 'fork <from> <target A> <target B>'.")
        target = self._target(piece, args[1])
        self._annihilate(piece, target)
        self._end_turn()

    def _fork(self, args):
        self._need(args, 3, "fork <from> <target A> <target B>")
        piece = self._own_piece(args[0])
        first = self._target(piece, args[1])
        second = self._target(piece, args[2])
        if first is second:
            raise ValueError("Fork two different targets.")
        piece.fork = (first, second)
        piece.fork_fixed = None
        self._say(f"{label(piece)} on {args[0]} forks {args[1]} (A) and {args[2]} (B).")
        self._end_turn()

    def _pass(self, args):
        self._need(args, 0, "pass")
        self._say(f"{NAMES[self.turn]} passes.")
        self._end_turn()

    def _keep(self, args):
        if len(args) not in (1, 3) or args[0] not in ("1", "2") or (len(args) == 3 and (
                args[1] != "drop" or args[2] not in ("1", "2"))):
            raise ValueError("Usage: keep <1|2> [drop <1|2>]")
        hand = self.hands[self.turn]
        if len(hand) >= HAND_SIZE and len(args) == 1:
            raise ValueError("Your hand is full: 'keep <1|2> drop <1|2>' or 'skip'.")
        if len(hand) < HAND_SIZE and len(args) == 3:
            raise ValueError("Your hand is not full, nothing to drop.")
        card = self.offer[int(args[0]) - 1]
        if len(args) == 3:
            self._say(f"Dropped {hand.pop(int(args[2]) - 1)}.")
        hand.append(card)
        self._say(f"Kept {card}.")
        self.offer = None
        self.phase = "action"

    def _skip(self):
        self._say("Kept nothing.")
        self.offer = None
        self.phase = "action"

    def _power(self, args):
        if not args or args[0] not in CARDS:
            raise ValueError("Usage: power interference|cooper|teleport|bell ...")
        card = CARDS[args[0]]
        hand = self.hands[self.turn]
        if self.power_used:
            raise ValueError("You have already used a power-up this turn.")
        if card not in hand:
            raise ValueError(f"You have no {card} card.")
        args = args[1:]
        if card == "Interference":
            self._need(args, 2, "power interference <forked piece> <a|b>")
            piece = self._piece(args[0])
            Q.apply_interference(piece, args[1].upper())
            self._say(f"Interference fixed the fork on {args[0]} to {args[1].upper()}.")
        elif card == "Cooper Pair":
            self._need(args, 3, "power cooper <electron> <electron> <square>")
            e1, e2 = self._own_piece(args[0]), self._own_piece(args[1])
            Q.make_cooper_pair(self.board, e1, e2, parse_square(args[2]))
            self._say(f"Cooper pair formed on {args[2]}.")
        elif card == "Bell Link":
            self._need(args, 2, "power bell <enemy piece> <enemy piece>")
            Q.add_link(self.board, self._piece(args[0]), self._piece(args[1]), player=self.turn)
            self._say(f"Bell link between {args[0]} and {args[1]}.")
        else:
            self._need(args, 2, "power teleport <from> <to>")
            piece = self._own_piece(args[0])
            start = piece.pos
            ok, qc = Q.teleport_piece(self.board, piece, parse_square(args[1]))
            self.circuits.append(("teleport", qc))
            if not ok:
                piece.pos = start
                raise ValueError("Teleport failed, try again.")
            self._say(f"{label(piece)} teleported to {args[1]}.")
        hand.remove(card)
        self.power_used = True
        if card == "Teleport":
            self._end_turn()

    # ----- helpers for players, tests and the notebook -----

    def legal_commands(self):
        if self.over:
            return []
        if self.phase == "draw":
            if len(self.hands[self.turn]) < HAND_SIZE:
                return ["keep 1", "keep 2", "skip"]
            return [f"keep {k} drop {d}" for k in "12" for d in "12"] + ["skip"]
        board, side = self.board, self.turn
        own = [p for p in board.pieces if p.side == side]
        enemy = [p for p in board.pieces if p.side != side]
        result = []
        for p in own:
            sq = square_name(p.pos)
            result += [f"move {sq} {square_name(d)}" for d in board.moves(p)]
            targets = board.targets(p)
            if len(targets) == 1:
                result.append(f"attack {sq} {square_name(targets[0].pos)}")
            for i, a in enumerate(targets):
                for b in targets[i + 1:]:
                    result.append(f"fork {sq} {square_name(a.pos)} {square_name(b.pos)}")
        hand = [] if self.power_used else self.hands[side]
        if "Teleport" in hand:
            for p in own:
                for r in range(SIZE):
                    for c in range(SIZE):
                        dest = (r, c)
                        if board.get(dest) is None and not board.breaks_exclusion(p, dest) and any(
                                f is not p and dist(f.pos, dest) == 1 for f in own):
                            result.append(f"power teleport {square_name(p.pos)} {square_name(dest)}")
        if "Interference" in hand:
            for p in board.pieces:
                if p.fork is not None:
                    result += [f"power interference {square_name(p.pos)} {x}" for x in "ab"]
        if "Cooper Pair" in hand:
            electrons = [p for p in own if p.kind == "e" and p.fork is None]
            for i, a in enumerate(electrons):
                for b in electrons[i + 1:]:
                    if dist(a.pos, b.pos) <= 2:
                        for sq in (a.pos, b.pos):
                            result.append(f"power cooper {square_name(a.pos)} {square_name(b.pos)} "
                                          f"{square_name(sq)}")
        if "Bell Link" in hand:
            linkable = [p for p in enemy if p.kind != "t"]
            for i, a in enumerate(linkable):
                for b in linkable[i + 1:]:
                    linked = any((x is a and y is b) or (x is b and y is a) for x, y in board.links)
                    if dist(a.pos, b.pos) <= 3 and not linked:
                        result.append(f"power bell {square_name(a.pos)} {square_name(b.pos)}")
        result.append("pass")
        return result

    def status(self):
        lines = []
        if self.over:
            lines.append("Game over: " + (f"{NAMES[self.winner]} wins." if self.winner else "draw."))
        else:
            lines.append(f"Round {self.turn_count['A'] + (self.turn == 'M')}/{self.rounds}  "
                         f"{NAMES[self.turn]} to play ({self.phase})")
        lines.append(f"Score  M {self.board.score('M')} : A {self.board.score('A')}")
        for side in "MA":
            lines.append(f"{NAMES[side]} hand: {', '.join(self.hands[side]) or '-'}")
        for a, b in self.board.links:
            lines.append(f"Bell link: {label(a)} {square_name(a.pos)} <-> {label(b)} {square_name(b.pos)}")
        for p in self.board.pieces:
            if p.fork is not None:
                fixed = "" if p.fork_fixed is None else f" (fixed to {'AB'[p.fork_fixed]})"
                lines.append(f"Fork: {label(p)} {square_name(p.pos)} -> "
                             f"A {square_name(p.fork[0].pos)} / B {square_name(p.fork[1].pos)}{fixed}")
        if self.offer:
            lines.append(f"Draw: 1) {self.offer[0]}  2) {self.offer[1]}")
        return "\n".join(lines)

    def show(self):
        self.board.show()
        print(self.status())


HELP = """Commands (squares are a1..f6):
  move <from> <to>                 attack <from> <target>
  fork <from> <target A> <target B>  (when two or more enemies are in range)
  keep <1|2> [drop <1|2>] / skip   (power-up draw on your turns 3, 5, 7, ...)
  power interference <forked piece> <a|b>
  power cooper <electron> <electron> <square>
  power bell <enemy piece> <enemy piece>
  power teleport <from> <to>       (ends your turn)
                                   (at most one power-up per turn; 'use' also works)
  pass                             (end your turn without acting)
  help, quit"""


def play(game=None, read=input):
    game = game or GameState()
    print(HELP)
    while not game.over:
        game.show()
        seen = len(game.log)
        text = read(f"{NAMES[game.turn]}> ").strip()
        if text in ("quit", "exit"):
            break
        if text == "help":
            print(HELP)
            continue
        try:
            game.command(text)
        except ValueError as error:
            print("Not allowed:", error)
        for line in game.log[seen:]:
            print(line)
    if game.over:
        game.show()
    return game


if __name__ == "__main__":
    play()
