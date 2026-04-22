"""
Controller class to handle game logic.
"""

import sys
from abc import ABC, abstractmethod
import pygame


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

    def start_mode(self, mode_key, stockfish_level=None):
        if mode_key == "one_player":
            self.board.start_game("one_player")
            self.board.set_stockfish(self.board.maybe_make_stockfish())
            if stockfish_level is not None:
                self.board.configure_stockfish(stockfish_level)
        elif mode_key == "two_player":
            self.board.start_game("two_player")
            self.board.set_stockfish(None)
        elif mode_key == "chess960":
            self.board.start_game("chess960")
            self.board.set_stockfish(None)
        elif mode_key == "sandbox":
            self.board.start_game("sandbox")
            self.board.set_stockfish(None)

        self._state = "game"

    def handle_menu_click(self, mouse_pos):
        if self._state == "menu":
            choice = self.view.get_menu_choice(mouse_pos)
            if choice == "one_player":
                self._state = "difficulty_menu"
            elif choice is not None:
                self.start_mode(choice)
        elif self._state == "difficulty_menu":
            difficulty = self.view.get_difficulty_choice(mouse_pos)
            if difficulty is not None:
                self.start_mode("one_player", stockfish_level=difficulty)

    def handle_mouse_down(self, mouse_pos):
        if self.board.promotion_pending:
            choice = self.view.get_promotion_choice(mouse_pos, self.board.promotion_pending[2])
            if choice is not None:
                self.board.promote_pawn(choice)
                if self.board.mode == "one_player" and self.board.turn == "b":
                    pygame.display.flip()
                    pygame.time.wait(150)
                    self.board.apply_stockfish_move()
            return

        if self.board.mode == "sandbox":
            if self.view.sandbox_toggle_rect.collidepoint(mouse_pos):
                self.board.toggle_sandbox_side()
                return

            palette_choice = self.view.get_sandbox_palette_choice(mouse_pos)
            if palette_choice is not None:
                piece_name, color = palette_choice
                self.board.begin_palette_drag(piece_name, color, mouse_pos)
                return

        board_pos = self.view.pixel_to_board(mouse_pos)
        if board_pos is None:
            return

        col, row = board_pos
        piece = self.board.get_piece(col, row)

        if piece is None:
            self.board.reset_selection()
            return

        if self.board.mode != "sandbox" and piece.color != self.board.turn:
            return

        self.board.selected = (col, row)
        self.board.legal_moves = piece.valid_moves(col, row, self.board)
        self.board.begin_drag(col, row, mouse_pos)

    def handle_mouse_motion(self, mouse_pos):
        if self.board.dragging:
            self.board.update_drag(mouse_pos)

    def handle_mouse_up(self, mouse_pos):
        if self.board.promotion_pending:
            return

        if not self.board.dragging:
            return

        board_pos = self.view.pixel_to_board(mouse_pos)

        if self.board.drag_source == "palette":
            if board_pos is not None:
                col, row = board_pos
                self.board.set_piece(col, row, self.board.drag_piece)
            self.board.clear_drag()
            self.board.reset_selection()
            return

        start = self.board.drag_from
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

                if self.board.promotion_pending:
                    return

                if self.board.mode == "one_player" and self.board.turn == "b":
                    pygame.display.flip()
                    pygame.time.wait(150)
                    self.board.apply_stockfish_move()
                return

        self.board.clear_drag()
        self.board.reset_selection()

    def run(self):
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self._state in ("menu", "difficulty_menu"):
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.handle_menu_click(event.pos)

                elif self._state == "game":
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.handle_mouse_down(event.pos)

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                        if self.board.mode == "sandbox":
                            board_pos = self.view.pixel_to_board(event.pos)
                            if board_pos is not None:
                                col, row = board_pos
                                self.board.clear_square(col, row)

                    elif event.type == pygame.MOUSEMOTION:
                        self.handle_mouse_motion(event.pos)

                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        self.handle_mouse_up(event.pos)

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self._state = "menu"
                            self.board.clear_drag()
                            self.board.reset_selection()
                            self.board.clear_promotion()

            if self._state == "menu":
                self.view.draw_menu()
            elif self._state == "difficulty_menu":
                self.view.draw_difficulty_menu()
            else:
                self.view.display()

            clock.tick(60)