"""
Piece class to represent each piece.

IMPORTANT FOR TEAM:
- Put piece-specific geometric movement here.
- Examples: rook lines, bishop diagonals, knight jumps, pawn forward moves.
- Do NOT put full game-state rules here such as:
    - check / checkmate
    - pinned pieces
    - castling through check
    - en passant state tracking
    - promotion UI
Those higher-level rules should go in helper_functions.py and/or ChessController.py.
"""

from abc import ABC, abstractmethod


class ChessPiece(ABC):
    """
    Abstract representation of the pieces.

    Attributes:
        _color: A string representing the color of the piece
        _has_moved: A boolean representing whether the piece has moved
    """

    def __init__(self, color):
        self._color = color
        self._has_moved = False

    @property
    def color(self):
        return self._color

    @property
    def has_moved(self):
        return self._has_moved

    @has_moved.setter
    def has_moved(self, value):
        self._has_moved = value

    @abstractmethod
    def valid_moves(self, col, row, board):
        """
        Return geometric candidate moves for this piece.

        IMPORTANT:
        This should return moves allowed by the piece's movement pattern.
        Full legality filtering such as "does this leave the king in check?"
        should be done in helper_functions.py.
        """
        pass

    def _slide(self, col, row, directions, board):
        """
        Helper for sliding pieces.

        This handles blocking and captures in straight lines / diagonals.
        """
        moves = []
        for dc, dr in directions:
            c, r = col + dc, row + dr
            while 0 <= c <= 7 and 0 <= r <= 7:
                target = board.get_piece(c, r)
                if target is None:
                    moves.append((c, r))
                elif target.color != self.color:
                    moves.append((c, r))
                    break
                else:
                    break
                c += dc
                r += dr
        return moves

    def fen_symbol(self):
        mapping = {
            Pawn: "p",
            Knight: "n",
            Bishop: "b",
            Rook: "r",
            Queen: "q",
            King: "k",
        }
        symbol = mapping[type(self)]
        return symbol.upper() if self.color == "w" else symbol


class Knight(ChessPiece):
    def valid_moves(self, col, row, board):
        candidates = [
            (col + 2, row + 1), (col + 2, row - 1),
            (col - 2, row + 1), (col - 2, row - 1),
            (col + 1, row + 2), (col + 1, row - 2),
            (col - 1, row + 2), (col - 1, row - 2),
        ]

        moves = []
        for c, r in candidates:
            if 0 <= c <= 7 and 0 <= r <= 7:
                target = board.get_piece(c, r)
                if target is None or target.color != self.color:
                    moves.append((c, r))
        return moves


class Bishop(ChessPiece):
    def valid_moves(self, col, row, board):
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        return self._slide(col, row, directions, board)


class Rook(ChessPiece):
    def valid_moves(self, col, row, board):
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        return self._slide(col, row, directions, board)


class Queen(ChessPiece):
    def valid_moves(self, col, row, board):
        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ]
        return self._slide(col, row, directions, board)


class King(ChessPiece):
    def valid_moves(self, col, row, board):
        candidates = [
            (col, row + 1), (col, row - 1),
            (col + 1, row), (col - 1, row),
            (col + 1, row + 1), (col + 1, row - 1),
            (col - 1, row + 1), (col - 1, row - 1),
        ]

        moves = []
        for c, r in candidates:
            if 0 <= c <= 7 and 0 <= r <= 7:
                target = board.get_piece(c, r)
                if target is None or target.color != self.color:
                    moves.append((c, r))
        return moves


class Pawn(ChessPiece):
    def valid_moves(self, col, row, board):
        """
        Pawn geometric movement only.

        IMPORTANT FOR TEAM:
        - Add en passant support in helper_functions.py because it depends on
          move history / last move state.
        - Add promotion handling in ChessController.py because it involves UI
          and replacement piece choice.
        """
        moves = []

        direction = 1 if self.color == "w" else -1
        next_row = row + direction

        if 0 <= next_row <= 7 and board.get_piece(col, next_row) is None:
            moves.append((col, next_row))

            start_row = 1 if self.color == "w" else 6
            jump_row = row + 2 * direction
            if row == start_row and 0 <= jump_row <= 7 and board.get_piece(col, jump_row) is None:
                moves.append((col, jump_row))

        for dc in (-1, 1):
            c = col + dc
            r = row + direction
            if 0 <= c <= 7 and 0 <= r <= 7:
                target = board.get_piece(c, r)
                if target is not None and target.color != self.color:
                    moves.append((c, r))

        return moves