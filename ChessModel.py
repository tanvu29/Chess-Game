"""
Model class to represent the board, pieces, and game rules.

IMPORTANT FOR TEAM:
- Put board state here.
- Put move legality helpers here.
- Put Stockfish integration here.
- Put Chess960 setup here.
- Keep ChessPiece.py for raw piece movement patterns only.
- Keep ChessView.py for drawing only.
- Keep ChessController.py for event handling only.
"""

import os
import random
import subprocess
from ChessPiece import Pawn, Knight, Bishop, Queen, King, Rook


class StockfishAPI:
    """
    Minimal Stockfish bridge.

    Put stockfish.exe at:
        stockfish/stockfish.exe
    """

    def __init__(self, engine_path="stockfish/stockfish.exe"):
        self.engine_path = engine_path
        self.process = None

        if os.path.exists(engine_path):
            self.process = subprocess.Popen(
                engine_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            self.send_command("uci")
            self.send_command("isready")

    def send_command(self, command):
        if self.process is None:
            return
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def get_best_move(self, fen, depth=10):
        if self.process is None:
            return None

        self.send_command(f"position fen {fen}")
        self.send_command(f"go depth {depth}")

        while True:
            line = self.process.stdout.readline().strip()
            if line.startswith("bestmove"):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
                return None


class ChessModel:
    """
    Model representation of the chess game/board.
    """

    def __init__(self):
        self._board = [[None] * 8 for _ in range(8)]
        self._turn = "w"
        self._move_number = 1
        self._captured_pieces = {"w": [], "b": []}
        self._move_history = []
        self._selected = None
        self._legal_moves = []
        self._mode = None
        self._stockfish = None

        self._dragging = False
        self._drag_piece = None
        self._drag_from = None
        self._drag_mouse_pos = None

    def setup_standard(self):
        self._board = [[None] * 8 for _ in range(8)]
        self._turn = "w"
        self._move_number = 1
        self._captured_pieces = {"w": [], "b": []}
        self._move_history = []
        self.reset_selection()
        self.clear_drag()

        back_rank = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]

        for col, piece_cls in enumerate(back_rank):
            self._board[0][col] = piece_cls("w")
            self._board[7][col] = piece_cls("b")

        for col in range(8):
            self._board[1][col] = Pawn("w")
            self._board[6][col] = Pawn("b")

    def setup_chess960(self):
        self._board = [[None] * 8 for _ in range(8)]
        self._turn = "w"
        self._move_number = 1
        self._captured_pieces = {"w": [], "b": []}
        self._move_history = []
        self.reset_selection()
        self.clear_drag()

        layout = self._generate_960_back_rank()

        for col, piece_cls in enumerate(layout):
            self._board[0][col] = piece_cls("w")
            self._board[7][col] = piece_cls("b")

        for col in range(8):
            self._board[1][col] = Pawn("w")
            self._board[6][col] = Pawn("b")

    def _generate_960_back_rank(self):
        layout = [None] * 8

        dark_squares = [0, 2, 4, 6]
        light_squares = [1, 3, 5, 7]

        b1 = random.choice(dark_squares)
        b2 = random.choice(light_squares)
        layout[b1] = Bishop
        layout[b2] = Bishop

        remaining = [i for i in range(8) if layout[i] is None]
        q = random.choice(remaining)
        layout[q] = Queen

        remaining = [i for i in range(8) if layout[i] is None]
        n1, n2 = random.sample(remaining, 2)
        layout[n1] = Knight
        layout[n2] = Knight

        remaining = sorted([i for i in range(8) if layout[i] is None])
        layout[remaining[0]] = Rook
        layout[remaining[1]] = King
        layout[remaining[2]] = Rook

        return layout

    def start_game(self, mode):
        self._mode = mode
        if mode == "chess960":
            self.setup_chess960()
        else:
            self.setup_standard()

    def maybe_make_stockfish(self):
        api = StockfishAPI()
        return api if api.process is not None else None

    def set_stockfish(self, stockfish_api):
        self._stockfish = stockfish_api

    def apply_stockfish_move(self):
        if self._mode != "one_player":
            return

        if self._stockfish is None:
            return

        fen = self.board_to_fen()
        bestmove = self._stockfish.get_best_move(fen)

        if bestmove is None or len(bestmove) < 4:
            return

        start = bestmove[:2]
        end = bestmove[2:4]

        start_col, start_row = self.alg_to_coord(start)
        end_col, end_row = self.alg_to_coord(end)

        piece = self.get_piece(start_col, start_row)
        if piece is None:
            return

        legal = piece.valid_moves(start_col, start_row, self)
        if (end_col, end_row) in legal:
            self.move_piece(start_col, start_row, end_col, end_row)
            self.reset_selection()

    @property
    def mode(self):
        return self._mode

    @property
    def board(self):
        return self._board

    @property
    def turn(self):
        return self._turn

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value

    @property
    def legal_moves(self):
        return self._legal_moves

    @legal_moves.setter
    def legal_moves(self, value):
        self._legal_moves = value

    @property
    def dragging(self):
        return self._dragging

    @property
    def drag_piece(self):
        return self._drag_piece

    @property
    def drag_from(self):
        return self._drag_from

    @property
    def drag_mouse_pos(self):
        return self._drag_mouse_pos

    @property
    def move_history(self):
        return self._move_history

    def begin_drag(self, col, row, mouse_pos):
        piece = self.get_piece(col, row)
        if piece is None:
            return False
        self._dragging = True
        self._drag_piece = piece
        self._drag_from = (col, row)
        self._drag_mouse_pos = mouse_pos
        return True

    def update_drag(self, mouse_pos):
        self._drag_mouse_pos = mouse_pos

    def clear_drag(self):
        self._dragging = False
        self._drag_piece = None
        self._drag_from = None
        self._drag_mouse_pos = None

    def get_piece(self, col, row):
        if 0 <= col <= 7 and 0 <= row <= 7:
            return self._board[row][col]
        return None

    def set_piece(self, col, row, piece):
        if 0 <= col <= 7 and 0 <= row <= 7:
            self._board[row][col] = piece

    def reset_selection(self):
        self._selected = None
        self._legal_moves = []

    def is_legal_move(self, start_col, start_row, end_col, end_row):
        piece = self.get_piece(start_col, start_row)
        if piece is None:
            return False

        if piece.color != self._turn:
            return False

        moves = piece.valid_moves(start_col, start_row, self)
        return (end_col, end_row) in moves

    def coord_to_alg(self, col, row):
        return chr(ord("a") + col) + str(row + 1)

    def alg_to_coord(self, square):
        col = ord(square[0]) - ord("a")
        row = int(square[1]) - 1
        return col, row

    def _piece_letter(self, piece):
        mapping = {
            Pawn: "",
            Knight: "N",
            Bishop: "B",
            Rook: "R",
            Queen: "Q",
            King: "K",
        }
        return mapping.get(type(piece), "")

    def _format_move_text(self, piece, start_col, start_row, end_col, end_row, captured):
        start_sq = self.coord_to_alg(start_col, start_row)
        end_sq = self.coord_to_alg(end_col, end_row)
        prefix = self._piece_letter(piece)

        if isinstance(piece, Pawn):
            if captured:
                return f"{start_sq[0]}x{end_sq}"
            return end_sq

        if captured:
            return f"{prefix}x{end_sq}"
        return f"{prefix}{end_sq}"

    def move_piece(self, start_col, start_row, end_col, end_row):
        piece = self.get_piece(start_col, start_row)
        if piece is None:
            return False

        target = self.get_piece(end_col, end_row)
        captured = target is not None

        if target is not None:
            self._captured_pieces[target.color].append(target)

        move_text = self._format_move_text(
            piece, start_col, start_row, end_col, end_row, captured
        )

        self.set_piece(end_col, end_row, piece)
        self.set_piece(start_col, start_row, None)
        piece.has_moved = True

        self._move_history.append(move_text)
        self._turn = "b" if self._turn == "w" else "w"
        self._move_number += 1
        return True

    def board_to_fen(self):
        fen_rows = []

        for row in range(7, -1, -1):
            empty = 0
            fen_row = ""

            for col in range(8):
                piece = self._board[row][col]
                if piece is None:
                    empty += 1
                else:
                    if empty > 0:
                        fen_row += str(empty)
                        empty = 0
                    fen_row += piece.fen_symbol()

            if empty > 0:
                fen_row += str(empty)

            fen_rows.append(fen_row)

        side = "w" if self._turn == "w" else "b"
        return "/".join(fen_rows) + f" {side} - - 0 1"