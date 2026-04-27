"""
Piece class to represent each piece's geometric movement.
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
        """
        Property method that returns the color of the piece.
        """
        return self._color

    @property
    def has_moved(self):
        """
        Property method that returns whether the piece has moved.
        """
        return self._has_moved

    @has_moved.setter
    def has_moved(self, value):
        """
        Setter for _has_moved attribute.
        """
        self._has_moved = value

    @abstractmethod
    def valid_moves(self, col, row, board):
        """
        Check the board for all squares the piece can geometrically move to.

        Args:
            col: An int representing the current file position of the piece
            row: An int representing current rank position of the piece
            board: A board instance representing the chessboard

        Returns:
            A list of tuples that represent possible coordinates
            the piece can move to.
        """

    def slide(self, col, row, directions, board):
        """
        Helper to check candidate moves for sliding pieces (rook bishop queen).
        Walks in each direction until blocked or out of bounds.

        Args:
            col: An int representing the current file position of the piece
            row: An int representing current rank position of the piece
            directions: A list of tuples representing direction vectors
            board: A board instance representing the chessboard

        Returns:
            A list of tuples that represent possible coordinates
            the sliding piece can move to.
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
        """
        Map each piece to its FEN (Forsyth-Edwards Notation).

        Returns:
            A string representing the FEN symbol of the piece.
        """
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
    """
    Implementation of move rules for the Knight.

    Attributes:
        _color: A string representing the color of the piece
        _has_moved: A boolean representing whether the piece has moved
    """

    def valid_moves(self, col, row, board):
        candidates = [
            (col + 2, row + 1),
            (col + 2, row - 1),
            (col - 2, row + 1),
            (col - 2, row - 1),
            (col + 1, row + 2),
            (col + 1, row - 2),
            (col - 1, row + 2),
            (col - 1, row - 2),
        ]

        moves = []
        for c, r in candidates:
            if 0 <= c <= 7 and 0 <= r <= 7:
                target = board.get_piece(c, r)
                if target is None or target.color != self.color:
                    moves.append((c, r))
        return moves


class Bishop(ChessPiece):
    """
    Implementation of move rules for the Bishop.

    Attributes:
        _color: A string representing the color of the piece
        _has_moved: A boolean representing whether the piece has moved
    """

    def valid_moves(self, col, row, board):
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        return self.slide(col, row, directions, board)


class Rook(ChessPiece):
    """
    Implementation of move rules for the Rook.

    Attributes:
        _color: A string representing the color of the piece
        _has_moved: A boolean representing whether the piece has moved
    """

    def valid_moves(self, col, row, board):
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        return self.slide(col, row, directions, board)


class Queen(ChessPiece):
    """
    Implementation of move rules for the Queen.

    Attributes:
        _color: A string representing the color of the piece
        _has_moved: A boolean representing whether the piece has moved
    """

    def valid_moves(self, col, row, board):
        directions = [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]
        return self.slide(col, row, directions, board)


class King(ChessPiece):
    """
    **Partial implementation of move rules for the King.
    Note: King-is-checked logic not implemented here.

    Attributes:
        _color: A string representing the color of the piece
        _has_moved: A boolean representing whether the piece has moved
    """

    def valid_moves(self, col, row, board):
        candidates = [
            (col, row + 1),
            (col, row - 1),
            (col + 1, row),
            (col - 1, row),
            (col + 1, row + 1),
            (col + 1, row - 1),
            (col - 1, row + 1),
            (col - 1, row - 1),
        ]

        moves = []
        for c, r in candidates:
            if 0 <= c <= 7 and 0 <= r <= 7:
                target = board.get_piece(c, r)
                if target is None or target.color != self.color:
                    moves.append((c, r))

        # Add castling moves from the model
        moves += board.get_castling_moves(col, row, self.color)
        return moves


class Pawn(ChessPiece):
    """
    **Partial implementation of move rules for the Pawn.
    Includes: One step, two step, diagonal capture.

    Attributes:
        _color: A string representing the color of the piece
        _has_moved: A boolean representing whether the piece has moved
    """

    def valid_moves(self, col, row, board):
        moves = []

        direction = 1 if self.color == "w" else -1
        next_row = row + direction

        if 0 <= next_row <= 7 and board.get_piece(col, next_row) is None:
            moves.append((col, next_row))

            start_row = 1 if self.color == "w" else 6
            jump_row = row + 2 * direction
            if (
                row == start_row
                and 0 <= jump_row <= 7
                and board.get_piece(col, jump_row) is None
            ):
                moves.append((col, jump_row))

        for dc in (-1, 1):
            c = col + dc
            r = row + direction
            if 0 <= c <= 7 and 0 <= r <= 7:
                target = board.get_piece(c, r)
                if target is not None and target.color != self.color:
                    moves.append((c, r))
                # En passant capture
                elif board.en_passant_target == (c, r):
                    moves.append((c, r))

        return moves
