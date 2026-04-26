"""
Model class to represent the board, pieces, and game rules.
"""

import os
import sys
import random
import subprocess
import copy
from ChessPiece import Pawn, Knight, Bishop, Queen, King, Rook


def resource_path(relative_path):
    """
    Return an absolute path for assets both in development and in a PyInstaller
    build.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class StockfishAPI:
    """
    Direct UCI subprocess wrapper around the Stockfish engine executable.

    IMPORTANT:
    You need the actual engine binary, for example:
        stockfish/stockfish.exe
    """

    def __init__(self, engine_path=None):
        self.process = None
        self.skill_level = 10
        self.search_depth = 10
        self.status = "Stockfish not initialized"

        candidate_paths = []

        if engine_path is not None:
            candidate_paths.append(resource_path(engine_path))

        candidate_paths.extend(
            [
                resource_path("stockfish/stockfish.exe"),
                resource_path("stockfish.exe"),
                resource_path("stockfish/stockfish-windows-x86-64.exe"),
                resource_path("stockfish/stockfish-windows-x86-64-avx2.exe"),
                resource_path(
                    "stockfish/stockfish-windows-x86-64-sse41-popcnt.exe"
                ),
            ]
        )

        found_path = None
        for path in candidate_paths:
            if os.path.exists(path):
                found_path = path
                break

        if found_path is None:
            self.status = "stockfish engine executable not found"
            return

        try:
            self.process = subprocess.Popen(
                [found_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True,
                bufsize=1,
            )

            self.send_command("uci")
            if not self._wait_for("uciok", timeout_lines=200):
                self.status = "stockfish did not respond to UCI"
                self.close()
                return

            self.send_command("isready")
            if not self._wait_for("readyok", timeout_lines=200):
                self.status = "stockfish not ready"
                self.close()
                return

            self.status = f"Stockfish loaded: {os.path.basename(found_path)}"
            self.set_strength(skill_level=10, search_depth=10, chess960=False)

        except Exception as e:
            self.process = None
            self.status = f"Stockfish launch failed: {e}"

    def close(self):
        if self.process is not None:
            try:
                self.send_command("quit")
            except Exception:
                pass
            self.process = None

    def send_command(self, command):
        if self.process is None or self.process.stdin is None:
            return
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def _wait_for(self, target, timeout_lines=200):
        if self.process is None or self.process.stdout is None:
            return False

        for _ in range(timeout_lines):
            line = self.process.stdout.readline()
            if not line:
                continue
            line = line.strip()
            if line == target or target in line:
                return True
        return False

    def set_strength(self, skill_level=10, search_depth=10, chess960=False):
        """
        Configure engine difficulty.

        This version makes difficulties feel more different by using:
        - Skill Level
        - Limited strength mode
        - Elo caps for weaker settings
        - movetime differences in get_best_move()
        """
        self.skill_level = max(0, min(20, int(skill_level)))
        self.search_depth = max(1, int(search_depth))

        if self.process is None:
            return

        self.send_command(
            f"setoption name Skill Level value {self.skill_level}"
        )

        if self.skill_level <= 5:
            self.send_command("setoption name UCI_LimitStrength value true")
            self.send_command("setoption name UCI_Elo value 800")
        elif self.skill_level <= 10:
            self.send_command("setoption name UCI_LimitStrength value true")
            self.send_command("setoption name UCI_Elo value 1200")
        elif self.skill_level <= 15:
            self.send_command("setoption name UCI_LimitStrength value true")
            self.send_command("setoption name UCI_Elo value 1600")
        else:
            self.send_command("setoption name UCI_LimitStrength value false")

        self.send_command(
            "setoption name UCI_Chess960 value"
            f" {'true' if chess960 else 'false'}"
        )
        self.send_command("isready")
        self._wait_for("readyok", timeout_lines=200)

    def get_best_move(self, fen):
        if self.process is None or self.process.stdout is None:
            return None

        try:
            self.send_command(f"position fen {fen}")

            # Difficulty difference is mostly driven here
            if self.skill_level <= 5:
                self.send_command("go movetime 50")
            elif self.skill_level <= 10:
                self.send_command("go movetime 150")
            elif self.skill_level <= 15:
                self.send_command("go movetime 400")
            else:
                self.send_command("go movetime 1000")

            for _ in range(500):
                line = self.process.stdout.readline()
                if not line:
                    continue
                line = line.strip()
                if line.startswith("bestmove"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
                    return None

            self.status = "Stockfish returned no move"
            return None

        except Exception as e:
            self.status = f"Engine move failed: {e}"
            return None


class ChessModel:
    """
    Model representation of the chess game/board.
    """

    def __init__(self):
        """
        UPDATES:
            _game_result: a string which gets intialized as None. The following
            valid states for this attribute are "checkmate_w", "checkmate_b",
            and "stalemate".
        """
        self._board = [[None] * 8 for _ in range(8)]
        self._turn = "w"
        self._move_number = 1
        self._captured_pieces = {"w": [], "b": []}
        self._move_history = []
        self._selected = None
        self._legal_moves = []
        self._mode = None
        self._stockfish = None
        self._stockfish_label = "Medium"
        self._engine_status = "No engine"

        self._dragging = False
        self._drag_piece = None
        self._drag_from = None
        self._drag_mouse_pos = None
        self._drag_source = None

        self._en_passant_target = None  # (col, row) of the square a pawn can
        # capture via en passant, or None
        self._castling_rights = {
            "w": {"kingside": True, "queenside": True},
            "b": {"kingside": True, "queenside": True},
        }

        self._promotion_pending = None
        self._sandbox_side_to_move = "w"
        self._game_result = None

    def __deepcopy__(self, memo):
        """
        Custom deepcopy that skips the Stockfish process, since subprocess
        objects contain thread locks which cannot be copied.
        """
        cls = self.__class__
        copy_obj = cls.__new__(cls)
        memo[id(self)] = copy_obj

        for key, value in self.__dict__.items():
            if key == "_stockfish":
                # Carry the reference across without copying — the copy is
                # only used for check simulation and never needs the engine
                setattr(copy_obj, key, None)
            else:
                setattr(copy_obj, key, copy.deepcopy(value, memo))

        return copy_obj

    # ----------------------------
    # Setup
    # ----------------------------

    def setup_standard(self):
        self._board = [[None] * 8 for _ in range(8)]
        self._turn = "w"
        self._move_number = 1
        self._captured_pieces = {"w": [], "b": []}
        self._move_history = []
        self.reset_selection()
        self.clear_drag()
        self.clear_promotion()
        self._game_result = None
        self._castling_rights = {
            "w": {"kingside": True, "queenside": True},
            "b": {"kingside": True, "queenside": True},
        }

        back_rank = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]

        for col, piece_cls in enumerate(back_rank):
            self._board[0][col] = piece_cls("w")
            self._board[7][col] = piece_cls("b")

        for col in range(8):
            self._board[1][col] = Pawn("w")
            self._board[6][col] = Pawn("b")

    def setup_sandbox(self):
        self._board = [[None] * 8 for _ in range(8)]
        self._turn = "w"
        self._move_number = 1
        self._captured_pieces = {"w": [], "b": []}
        self._move_history = []
        self._sandbox_side_to_move = "w"
        self.reset_selection()
        self.clear_drag()
        self.clear_promotion()
        self._game_result = None
        self._castling_rights = {
            "w": {"kingside": True, "queenside": True},
            "b": {"kingside": True, "queenside": True},
        }

    def setup_chess960(self):
        self._board = [[None] * 8 for _ in range(8)]
        self._turn = "w"
        self._move_number = 1
        self._captured_pieces = {"w": [], "b": []}
        self._move_history = []
        self.reset_selection()
        self.clear_drag()
        self.clear_promotion()
        self._game_result = None
        self._castling_rights = {
            "w": {"kingside": True, "queenside": True},
            "b": {"kingside": True, "queenside": True},
        }

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
        elif mode == "sandbox":
            self.setup_sandbox()
        else:
            self.setup_standard()

    # ----------------------------
    # Stockfish
    # ----------------------------

    def maybe_make_stockfish(self):
        api = StockfishAPI()
        self._engine_status = api.status
        print("STOCKFISH STATUS:", api.status)
        return api if api.process is not None else None

    def set_stockfish(self, stockfish_api):
        self._stockfish = stockfish_api
        if stockfish_api is None:
            self._engine_status = "No engine loaded"
        else:
            self._engine_status = stockfish_api.status

    def configure_stockfish(self, label):
        self._stockfish_label = label

        if self._stockfish is None:
            self._engine_status = "Stockfish unavailable"
            return

        presets = {
            "Easy": (3, 1),
            "Medium": (8, 4),
            "Hard": (15, 8),
            "Max": (20, 12),
        }

        skill, depth = presets.get(label, (8, 4))
        use_960 = self._mode == "chess960"
        self._stockfish.set_strength(
            skill_level=skill, search_depth=depth, chess960=use_960
        )
        self._engine_status = f"Engine ready ({label})"

    @property
    def stockfish_label(self):
        return self._stockfish_label

    @property
    def engine_status(self):
        return self._engine_status

    def apply_stockfish_move(self):
        if self._mode != "one_player":
            return False

        if self._stockfish is None:
            self._engine_status = "Stockfish unavailable"
            return False

        if self.promotion_pending:
            return False

        fen = self.board_to_fen()
        bestmove = self._stockfish.get_best_move(fen)

        if bestmove is None or bestmove == "(none)":
            return

        if bestmove is None or len(bestmove) < 4:
            self._engine_status = "Stockfish returned no move"
            return False

        start = bestmove[:2]
        end = bestmove[2:4]

        start_col, start_row = self.alg_to_coord(start)
        end_col, end_row = self.alg_to_coord(end)

        piece = self.get_piece(start_col, start_row)
        if piece is None:
            self._engine_status = f"Invalid engine move: {bestmove}"
            return False

        legal = piece.valid_moves(start_col, start_row, self)
        if (end_col, end_row) not in legal:
            self._engine_status = f"Illegal engine move blocked: {bestmove}"
            return False

        moved = self.move_piece(start_col, start_row, end_col, end_row)
        if not moved:
            self._engine_status = f"Engine failed to move: {bestmove}"
            return False

        self.reset_selection()
        self._engine_status = f"Engine played: {bestmove}"

        if self.promotion_pending is not None:
            self.promote_pawn("Queen")

        return True

    # ----------------------------
    # Properties
    # ----------------------------

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
    def drag_source(self):
        return self._drag_source

    @property
    def move_history(self):
        return self._move_history

    @property
    def promotion_pending(self):
        return self._promotion_pending

    @property
    def sandbox_side_to_move(self):
        return self._sandbox_side_to_move

    @property
    def game_result(self):
        return self._game_result

    @property
    def en_passant_target(self):
        return self._en_passant_target

    @property
    def castling_rights(self):
        return self._castling_rights

    # ----------------------------
    # Drag state
    # ----------------------------

    def begin_drag(self, col, row, mouse_pos):
        piece = self.get_piece(col, row)
        if piece is None:
            return False

        self._dragging = True
        self._drag_piece = piece
        self._drag_from = (col, row)
        self._drag_mouse_pos = mouse_pos
        self._drag_source = "board"
        return True

    def begin_palette_drag(self, piece_name, color, mouse_pos):
        piece = self.create_piece_by_name(piece_name, color)
        if piece is None:
            return False

        self._dragging = True
        self._drag_piece = piece
        self._drag_from = None
        self._drag_mouse_pos = mouse_pos
        self._drag_source = "palette"
        return True

    def update_drag(self, mouse_pos):
        self._drag_mouse_pos = mouse_pos

    def clear_drag(self):
        self._dragging = False
        self._drag_piece = None
        self._drag_from = None
        self._drag_mouse_pos = None
        self._drag_source = None

    # ----------------------------
    # Board helpers
    # ----------------------------

    def get_piece(self, col, row):
        if 0 <= col <= 7 and 0 <= row <= 7:
            return self._board[row][col]
        return None

    def set_piece(self, col, row, piece):
        if 0 <= col <= 7 and 0 <= row <= 7:
            self._board[row][col] = piece

    def clear_square(self, col, row):
        if 0 <= col <= 7 and 0 <= row <= 7:
            self._board[row][col] = None

    def reset_selection(self):
        self._selected = None
        self._legal_moves = []

    def create_piece_by_name(self, piece_name, color):
        mapping = {
            "Pawn": Pawn,
            "Knight": Knight,
            "Bishop": Bishop,
            "Rook": Rook,
            "Queen": Queen,
            "King": King,
        }
        piece_cls = mapping.get(piece_name)
        if piece_cls is None:
            return None
        return piece_cls(color)

    # ----------------------------
    # Promotion
    # ----------------------------

    def clear_promotion(self):
        self._promotion_pending = None

    def _check_promotion_needed(self, col, row):
        piece = self.get_piece(col, row)
        if not isinstance(piece, Pawn):
            return False

        if piece.color == "w" and row == 7:
            self._promotion_pending = (col, row, piece.color)
            return True

        if piece.color == "b" and row == 0:
            self._promotion_pending = (col, row, piece.color)
            return True

        return False

    def promote_pawn(self, piece_name):
        if self._promotion_pending is None:
            return False

        col, row, color = self._promotion_pending

        mapping = {
            "Queen": Queen,
            "Rook": Rook,
            "Bishop": Bishop,
            "Knight": Knight,
        }

        piece_cls = mapping.get(piece_name)
        if piece_cls is None:
            return False

        new_piece = piece_cls(color)
        new_piece.has_moved = True
        self.set_piece(col, row, new_piece)

        if self._move_history:
            suffix = {
                "Queen": "=Q",
                "Rook": "=R",
                "Bishop": "=B",
                "Knight": "=N",
            }[piece_name]
            self._move_history[-1] += suffix

        self.clear_promotion()
        return True

    # ----------------------------
    # Sandbox helpers
    # ----------------------------

    def toggle_sandbox_side(self):
        self._sandbox_side_to_move = (
            "b" if self._sandbox_side_to_move == "w" else "w"
        )

    def get_sandbox_state_label(self):
        side = "White" if self._sandbox_side_to_move == "w" else "Black"
        return f"State for {side} to move: not implemented"

    # ----------------------------
    # Move legality
    # ----------------------------

    def is_legal_move(self, start_col, start_row, end_col, end_row):
        piece = self.get_piece(start_col, start_row)
        if piece is None:
            return False

        if self._mode != "sandbox" and piece.color != self._turn:
            return False

        moves = piece.valid_moves(start_col, start_row, self)
        if (end_col, end_row) not in moves:
            return False

        model_copy = copy.deepcopy(self)
        model_copy.move_piece(start_col, start_row, end_col, end_row)
        if model_copy.is_in_check(piece.color):
            return False

        return True

    # ----------------------------
    # Notation helpers
    # ----------------------------

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

    def _format_move_text(
        self,
        piece,
        start_col,
        start_row,
        end_col,
        end_row,
        captured,
        is_castling=False,
    ):
        start_sq = self.coord_to_alg(start_col, start_row)
        end_sq = self.coord_to_alg(end_col, end_row)
        prefix = self._piece_letter(piece)

        if is_castling:
            move_text = "O-O" if end_col == 6 else "O-O-O"
        elif isinstance(piece, Pawn):
            if captured:
                move_text = f"{start_sq[0]}x{end_sq}"
            else:
                move_text = end_sq
        elif captured:
            move_text = f"{prefix}x{end_sq}"
        else:
            move_text = f"{prefix}{end_sq}"

        opponent = "b" if piece.color == "w" else "w"
        if self.is_in_check(opponent):
            if not self.has_legal_moves(opponent):
                move_text += "#"
            else:
                move_text += "+"

        return move_text

    def move_piece(self, start_col, start_row, end_col, end_row):
        piece = self.get_piece(start_col, start_row)
        if piece is None:
            return False

        target = self.get_piece(end_col, end_row)
        captured = target is not None

        # --- En passant capture ---
        # A pawn moving diagonally to an empty square must be capturing en
        # passant
        is_en_passant = (
            isinstance(piece, Pawn) and end_col != start_col and target is None
        )
        if is_en_passant:
            # Remove the captured pawn, which sits on the same row as the
            # moving pawn's start
            self.clear_square(end_col, start_row)
            captured = True

        if target is not None:
            self._captured_pieces[target.color].append(target)

        # --- Castling: move the rook to its new square ---
        is_castling = isinstance(piece, King) and abs(end_col - start_col) == 2
        if is_castling:
            back_row = start_row
            if end_col == 6:  # Kingside
                rook = self.get_piece(7, back_row)
                self.set_piece(5, back_row, rook)
                self.clear_square(7, back_row)
                if rook:
                    rook.has_moved = True
            elif end_col == 2:  # Queenside
                rook = self.get_piece(0, back_row)
                self.set_piece(3, back_row, rook)
                self.clear_square(0, back_row)
                if rook:
                    rook.has_moved = True

        self.set_piece(end_col, end_row, piece)
        self.set_piece(start_col, start_row, None)

        piece.has_moved = True

        # --- Revoke castling rights ---
        if isinstance(piece, King):
            self._castling_rights[piece.color]["kingside"] = False
            self._castling_rights[piece.color]["queenside"] = False
        if isinstance(piece, Rook):
            if start_col == 7:
                self._castling_rights[piece.color]["kingside"] = False
            elif start_col == 0:
                self._castling_rights[piece.color]["queenside"] = False

        # --- Set en passant target for next move ---
        # Only set when a pawn advances two squares; clear it in all other cases
        if isinstance(piece, Pawn) and abs(end_row - start_row) == 2:
            # The en passant target square is the square the pawn skipped over
            self._en_passant_target = (end_col, (start_row + end_row) // 2)
        else:
            self._en_passant_target = None

        if self._mode != "sandbox":
            self._turn = "b" if self._turn == "w" else "w"
            self._move_number += 1

        if self._mode != "sandbox":
            move_text = self._format_move_text(
                piece, start_col, start_row, end_col, end_row, captured
            )
            self._move_history.append(move_text)

        self._check_promotion_needed(end_col, end_row)
        return True

    # ----------------------------
    # FEN
    # ----------------------------

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

        # Build castling rights string for FEN
        castling = ""
        if self._castling_rights["w"]["kingside"]:
            castling += "K"
        if self._castling_rights["w"]["queenside"]:
            castling += "Q"
        if self._castling_rights["b"]["kingside"]:
            castling += "k"
        if self._castling_rights["b"]["queenside"]:
            castling += "q"
        if not castling:
            castling = "-"

        # En passant target square for FEN
        if self._en_passant_target:
            ep_col, ep_row = self._en_passant_target
            ep_sq = self.coord_to_alg(ep_col, ep_row)
        else:
            ep_sq = "-"
        return "/".join(fen_rows) + f" {side} {castling} {ep_sq} 0 1"

    def is_in_check(self, color):
        """
        Check function to see if the chosen color is in check in the current
        board state.

        Args:
            color: a string representing the color of player to check.

        Returns:
            A boolean representing whether or not that color is in check or not.
        """
        opponent = "b" if color == "w" else "w"

        # Find the King's Position
        king = None
        king_r_pos = None
        king_c_pos = None
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(col, row)
                if isinstance(piece, King) and piece.color == color:
                    king = piece
                    king_r_pos = row
                    king_c_pos = col

        if king is None:
            raise ValueError(f"No {color} king found on the board.")

        # Rook and Queen Checks
        rook_directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for index in range(4):
            single_direction = [rook_directions[index]]
            king_as_rook_moves = king.slide(
                king_c_pos, king_r_pos, single_direction, self
            )
            if king_as_rook_moves == []:
                continue
            potential_target_pos = king_as_rook_moves[-1]
            potential_target = self.get_piece(
                potential_target_pos[0], potential_target_pos[1]
            )
            if (
                isinstance(potential_target, Rook)
                or isinstance(potential_target, Queen)
            ) and potential_target.color == opponent:
                return True

        # Bishop and Queen Checks
        bishop_directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        for index in range(4):
            single_direction = [bishop_directions[index]]
            king_as_bishop_moves = king.slide(
                king_c_pos, king_r_pos, single_direction, self
            )
            if king_as_bishop_moves == []:
                continue
            potential_target_pos = king_as_bishop_moves[-1]
            potential_target = self.get_piece(
                potential_target_pos[0], potential_target_pos[1]
            )
            if (
                isinstance(potential_target, Bishop)
                or isinstance(potential_target, Queen)
            ) and potential_target.color == opponent:
                return True

        # Knight Checks
        for dc, dr in [
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ]:
            piece = self.get_piece(king_c_pos + dc, king_r_pos + dr)
            if isinstance(piece, Knight) and piece.color == opponent:
                return True

        # Pawn Checks
        pawn_dir = 1 if color == "w" else -1
        for dc in [-1, 1]:
            piece = self.get_piece(king_c_pos + dc, king_r_pos + pawn_dir)
            if isinstance(piece, Pawn) and piece.color == opponent:
                return True

        # King Attacks
        for dc in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if dc == 0 and dr == 0:
                    continue
                piece = self.get_piece(king_c_pos + dc, king_r_pos + dr)
                if isinstance(piece, King) and piece.color == opponent:
                    return True

        return False

    def has_legal_moves(self, color):
        """
        Checks to see if the given color has any legal moves left. This is used
        for both checkmate and stalemate endings for chess.

        Args:
            color: a string representing the color of the player to check.

        Returns:
            a boolean representing whether or not the player has legal moves.
        """
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(col, row)
                if piece is None or piece.color != color:
                    continue
                for end_col, end_row in piece.valid_moves(col, row, self):
                    if self.is_legal_move(col, row, end_col, end_row):
                        return True
        return False

    def check_game_end(self):
        """
        Sets _game_result to one of:
        'checkmate_w' (white wins), 'checkmate_b' (black wins), or 'stalemate'.
        Returns True if the game has ended, False otherwise.
        """
        if not self.has_legal_moves(self._turn):
            if self.is_in_check(self._turn):
                # The player whose turn it is has no moves and is in check
                self._game_result = (
                    "checkmate_w" if self._turn == "b" else "checkmate_b"
                )
            else:
                self._game_result = "stalemate"
            return True
        return False

    def _is_square_attacked(self, col, row, by_color):
        """
        Return True if the given square is attacked by any piece of by_color.
        """
        # Temporarily place a king of the opposite color on the square and
        # check if it would be in check — this reuses all our attack detection
        original = self.get_piece(col, row)
        defender_color = "w" if by_color == "b" else "b"
        temp_king = King(defender_color)
        self.set_piece(col, row, temp_king)
        attacked = self.is_in_check(defender_color)
        self.set_piece(col, row, original)
        return attacked

    def get_castling_moves(self, col, row, color):
        """
        Return castling destination squares for the king at (col, row).
        Enforces all castling rules:
        - King and rook must not have moved
        - Squares between king and rook must be empty
        - King must not be in check, pass through check, or land in check
        """
        moves = []
        back_row = 0 if color == "w" else 7
        opponent = "b" if color == "w" else "w"

        if row != back_row or col != 4:
            return moves  # King is not on its starting square

        if self.is_in_check(color):
            return moves  # Cannot castle while in check

        # Kingside castling
        if self._castling_rights[color]["kingside"]:
            rook = self.get_piece(7, back_row)
            if (
                isinstance(rook, Rook)
                and not rook.has_moved
                and self.get_piece(5, back_row) is None
                and self.get_piece(6, back_row) is None
                and not self._is_square_attacked(5, back_row, opponent)
                and not self._is_square_attacked(6, back_row, opponent)
            ):
                moves.append((6, back_row))

        # Queenside castling
        if self._castling_rights[color]["queenside"]:
            rook = self.get_piece(0, back_row)
            if (
                isinstance(rook, Rook)
                and not rook.has_moved
                and self.get_piece(1, back_row) is None
                and self.get_piece(2, back_row) is None
                and self.get_piece(3, back_row) is None
                and not self._is_square_attacked(3, back_row, opponent)
                and not self._is_square_attacked(4, back_row, opponent)
            ):
                moves.append((2, back_row))

        return moves
