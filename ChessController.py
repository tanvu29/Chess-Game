"""
Controller class to handle game logic.

IMPORTANT FOR TEAM:
- Event handling goes here.
- Drag/drop behavior goes here.
- Menu flow goes here.
- Core chess rules should live in ChessModel.py.
"""

import sys
import pygame
from abc import ABC, abstractmethod


class ChessController(ABC):
    def __init__(self, board):
        self._board = board

    @property
    def board(self):
        return self._board

    @abstractmethod
    def move(self):
        pass


class GameController(ChessController):
    def __init__(self, board, view):
        super().__init__(board)
        self._view = view
        self._state = "menu"

    @property
    def view(self):
        return self._view

    def move(self):
        pass

    def start_mode(self, mode_key):
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
        choice = self.view.get_menu_choice(mouse_pos)
        if choice is not None:
            self.start_mode(choice)

    def handle_mouse_down(self, mouse_pos):
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
        if self.board.dragging:
            self.board.update_drag(mouse_pos)

    def handle_mouse_up(self, mouse_pos):
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