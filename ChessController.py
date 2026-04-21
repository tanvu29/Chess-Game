"""
Controller class to handle game logic.

IMPORTANT FOR TEAM:
- Event handling goes here.
- Drag/drop behavior goes here.
- Menu flow goes here.
- Core chess rules should live in ChessModel.py.
"""

import sys
from abc import ABC, abstractmethod
import pygame


class ChessController(ABC):
    """
    Abstract representation of Chess Controller.
    """

    def __init__(self, board):
        """
        Initializes controller.

        Args:
            board: a ChessModel instance.

        Attributes:
            _board: a ChessModel instance representing the board for the game.
        """
        self._board = board

    @property
    def board(self):
        """
        Getter for board.

        Returns:
            a ChessModel instance representing the current state of the board.
        """
        return self._board

    @abstractmethod
    def move(self):
        """
        Abstract method for making a move in the game.
        """
        pass


class GameController(ChessController):
    """
    Controller Class to run whole chess game, including drag and drop
    functionality.
    """

    def __init__(self, board, view):
        """
        Initializes controller.

        Args:
            board: a ChessModel instance.
            view: a ChessView instance.

        Attributes:
            _board: a ChessModel instance representing the board for the game.
            _view: a ChessView instance representing the view of the game.
            _state: a string representing the current state of the game.
        """
        super().__init__(board)
        self._view = view
        self._state = "menu"

    @property
    def view(self):
        """
        Getter for _view attribute.

        Returns:
            a ChessView instance representing the current view of the game.
        """
        return self._view

    def move(self):
        pass

    def start_mode(self, mode_key):
        """
        Sets the mode of the game.

        Args:
            mode_key: a string representing the game mode to be played.
        """
        if mode_key == "one_player":
            self.board.start_game("one_player")
            self.board.set_stockfish(self.board.maybe_make_stockfish())
        elif mode_key == "two_player":
            self.board.start_game("two_player")
            self.board.set_stockfish(None)
        elif mode_key == "chess960":
            self.board.start_game("chess960")
            self.board.set_stockfish(None)

        self._state = "game"

    def handle_menu_click(self, mouse_pos):
        """
        Parses click to choose game mode in menu.

        Args:
            mouse_pos: a tuple representing the position of the mouse.
        """
        choice = self.view.get_menu_choice(mouse_pos)
        if choice is not None:
            self.start_mode(choice)

    def handle_mouse_down(self, mouse_pos):
        """
        Detects click on board to begin dragging motion.

        Args:
            mouse_pos: a tuple representing the position of the mouse.
        """
        board_pos = self.view.pixel_to_board(mouse_pos)
        if board_pos is None:
            return

        col, row = board_pos
        piece = self.board.get_piece(col, row)

        if piece is None:
            self.board.reset_selection()
            return

        if piece.color != self.board.turn:
            return

        self.board.selected = (col, row)
        self.board.legal_moves = piece.valid_moves(col, row, self.board)
        self.board.begin_drag(col, row, mouse_pos)

    def handle_mouse_motion(self, mouse_pos):
        """
        Updates mouse position on model side as user moves mouse.

        Args:
            mouse_pos: a tuple representing the position of the mouse.
        """
        if self.board.dragging:
            self.board.update_drag(mouse_pos)

    def handle_mouse_up(self, mouse_pos):
        """
        Detects release of the mouse and stops dragging.

        Args:
            mouse_pos: a tuple representing the position of the mouse.
        """
        if not self.board.dragging:
            return

        start = self.board.drag_from
        board_pos = self.view.pixel_to_board(mouse_pos)

        if start is None:
            self.board.clear_drag()
            self.board.reset_selection()
            return

        start_col, start_row = start

        if board_pos is not None:
            end_col, end_row = board_pos

            if self.board.is_legal_move(start_col, start_row, end_col, end_row):
                self.board.move_piece(start_col, start_row, end_col, end_row)
                self.board.clear_drag()
                self.board.reset_selection()

                if self.board.mode == "one_player" and self.board.turn == "b":
                    self.board.apply_stockfish_move()
                return

        # Illegal drop -> snap back automatically
        self.board.clear_drag()
        self.board.reset_selection()

    def run(self):
        """
        Begins running the game through the pygame window created by ChessView.
        """
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self._state == "menu":
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.handle_menu_click(event.pos)

                elif self._state == "game":
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.handle_mouse_down(event.pos)

                    elif event.type == pygame.MOUSEMOTION:
                        self.handle_mouse_motion(event.pos)

                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        self.handle_mouse_up(event.pos)

            if self._state == "menu":
                self.view.draw_menu()
            else:
                self.view.display()

            clock.tick(60)
