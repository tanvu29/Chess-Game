"""
Controller class to handle game logic.
"""

import sys
from abc import ABC, abstractmethod
import pygame


class ChessController(ABC):
    """
    Abstract base class for chess game controllers.

    Attributes:
        _board: A ChessModel instance representing the game state.
    """

    def __init__(self, board):
        self._board = board

    @property
    def board(self):
        """
        Property method that returns the ChessModel instance.
        """
        return self._board

    @abstractmethod
    def move(self):
        """
        Execute a move action for the current controller implementation.
        """


class GameController(ChessController):
    """
    Concrete controller that manages the full game loop, user input, and
    transitions between application states.

    Attributes:
        _board: A ChessModel instance representing the game state.
        _view: A PygameChessView instance used to render the game.
        _state: A string representing the current application state
            ('menu', 'difficulty_menu', 'game', or 'game_over').
    """

    def __init__(self, board, view):
        super().__init__(board)
        self._view = view
        self._state = "menu"

    @property
    def view(self):
        """
        Property method that returns the view instance.
        """
        return self._view

    def move(self):
        """
        Satisfy the abstract move interface. Move execution is handled
        through the mouse event handlers in this implementation.
        """

    def start_mode(self, mode_key, stockfish_level=None):
        """
        Initialize the board for the given game mode and transition to the
        game state.

        For one-player mode, attempts to load the Stockfish engine and applies
        the chosen difficulty level if provided.

        Args:
            mode_key: A string representing the game mode to start
                ('one_player', 'two_player', 'chess960', or 'sandbox').
            stockfish_level: A string representing the difficulty preset to
                apply in one-player mode (e.g. 'Easy', 'Hard'), or None to
                use the default.
        """
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
        """
        Process a mouse click on the main menu or difficulty selection screen.

        In the main menu state, routes the click to the appropriate mode or
        advances to the difficulty menu for one-player mode. In the difficulty
        menu state, starts a one-player game with the chosen difficulty.

        Args:
            mouse_pos: A tuple of two ints representing the (x, y) mouse
                position at the time of the click.
        """
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
        """
        Process a left mouse button press down, beginning a drag and drop.

        For promotion, the press down deciphers what piece to promote.
        Otherwise, it begins the drag-and-drop sequence for both pulling
        sandbox pieces and making moves.
        """
        if self.board.promotion_pending:
            choice = self.view.get_promotion_choice(
                mouse_pos, self.board.promotion_pending[2]
            )
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
        
        if self.board.mode == "one_player" and piece.color == "b":
            return

        self.board.selected = (col, row)
        self.board.legal_moves = piece.valid_moves(col, row, self.board)
        self.board.begin_drag(col, row, mouse_pos)

    def handle_mouse_motion(self, mouse_pos):
        """
        Process mouse movement, updating the drag position when a piece is
        being dragged.

        Args:
            mouse_pos: A tuple of two ints representing the current (x, y)
                mouse position.
        """
        if self.board.dragging:
            self.board.update_drag(mouse_pos)

    def handle_mouse_up(self, mouse_pos):
        """
        Process a left mouse button release, completing a drag-and-drop move.

        For board drags, validates and executes the move if legal, then checks
        for game-ending conditions and triggers the engine response in
        one-player mode. For palette drags, places the dragged piece on the
        target square. Clears all drag and selection state in all cases.

        Args:
            mouse_pos: A tuple of two ints representing the (x, y) mouse
                position at the time of release.
        """
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

                if self.board.check_game_end():
                    self._state = "game_over"
                    return

                if self.board.mode == "one_player" and self.board.turn == "b":
                    pygame.display.flip()
                    pygame.time.wait(150)
                    self.board.apply_stockfish_move()

                    if self.board.check_game_end():
                        self._state = "game_over"
                return

        self.board.clear_drag()
        self.board.reset_selection()

    def run(self):
        """
        Start the main game loop, processing events and rendering each frame
        until the application is closed.

        Dispatches pygame events to the appropriate handler based on the current
        application state. Renders the correct screen for each state and caps
        the frame rate at 60 FPS.
        """
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self._state in ("menu", "difficulty_menu"):
                    if (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                    ):
                        self.handle_menu_click(event.pos)

                elif self._state == "game_over":
                    if (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                    ):
                        if self.view.game_over_back_rect.collidepoint(
                            event.pos
                        ):
                            self._state = "menu"

                elif self._state == "game":
                    if (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                    ):
                        self.handle_mouse_down(event.pos)

                    elif (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 3
                    ):
                        if self.board.mode == "sandbox":
                            board_pos = self.view.pixel_to_board(event.pos)
                            if board_pos is not None:
                                col, row = board_pos
                                self.board.clear_square(col, row)

                    elif event.type == pygame.MOUSEMOTION:
                        self.handle_mouse_motion(event.pos)

                    elif (
                        event.type == pygame.MOUSEBUTTONUP and event.button == 1
                    ):
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
            elif self._state == "game_over":
                self.view.draw_game_over()
            else:
                self.view.display()

            clock.tick(60)
