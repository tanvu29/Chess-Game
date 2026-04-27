"""
View class to display GUI of the game.
"""

import os
import sys
from abc import ABC, abstractmethod
import pygame


def resource_path(relative_path):
    """
    Resolve the absolute path to a resource, compatible with PyInstaller
    bundles.

    Args:
        relative_path: A string representing the relative path to the resource.

    Returns:
        A string representing the absolute path to the resource.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class ChessView(ABC):
    """
    Abstract base class for rendering the chess game.

    Attributes:
        _board: A board instance representing the chessboard to be displayed.
    """

    def __init__(self, board):
        self._board = board

    @property
    def board(self):
        """
        Property method that returns the board instance.
        """
        return self._board

    @abstractmethod
    def display(self):
        """
        Render the current state of the board to the screen.
        """


class PygameChessView(ChessView):
    """
    Pygame implementation of the chess view.

    Attributes:
        (TUPLES - REPRESENTING RGB COLOR)
        MENU_BG: A tuple representing the RGB color of the menu background.
        PANEL_BG: A tuple representing the RGB color of the side panel
        background.
        LIGHT: A tuple representing the RGB color of light squares on the board.
        DARK: A tuple representing the RGB color of dark squares on the board.
        SELECTED: A tuple representing the RGB highlight color of a selected
        square.
        LEGAL_FILL: A tuple representing the RGB fill color for legal move
        indicators.
        LEGAL_BORDER: A tuple representing the RGB border color for legal move
        indicators.
        TEXT: A tuple representing the RGB color used for all text rendering.
        BUTTON: A tuple representing the RGB color of buttons in their default
        state.
        BUTTON_HOVER: A tuple representing the RGB color of buttons on mouse
        hover.
        DRAG_BORDER: A tuple representing the RGB border color drawn around a
        dragged piece.
        PROMO_BG: A tuple representing the RGB background color of the
        promotion panel.

        (INTS - REPRESENTING PIXEL ATTRIBUTES)
        square_size: An int representing the pixel size of each board square.
        board_size: An int representing the total pixel size of the board
        (8 * square_size).
        panel_width: An int representing the pixel width of the side panel.
        width: An int representing the total pixel width of the window.
        height: An int representing the total pixel height of the window.

        (PYGAME OBJECTS)
        screen: A pygame Surface representing the main display window.
        title_font: A pygame Font used for large heading text.
        menu_font: A pygame Font used for menu button labels.
        info_font: A pygame Font used for in-game information text.
        small_font: A pygame Font used for smaller detail text.
        menu_buttons: A dict mapping mode key strings to pygame Rects for main
        menu buttons.
        difficulty_buttons: A dict mapping difficulty label strings to pygame
        Rects.
        images: A dict mapping piece sprite key strings to scaled pygame
        Surfaces.
        sandbox_toggle_rect: A pygame Rect for the sandbox side-to-move toggle
        button.
        game_over_back_rect: A pygame Rect for the back-to-menu button on the
        game over screen.
    """

    MENU_BG = (30, 30, 40)
    PANEL_BG = (20, 20, 28)
    LIGHT = (240, 217, 181)
    DARK = (181, 136, 99)
    SELECTED = (246, 246, 105)
    LEGAL_FILL = (80, 180, 80)
    LEGAL_BORDER = (30, 120, 30)
    TEXT = (245, 245, 245)
    BUTTON = (65, 65, 85)
    BUTTON_HOVER = (90, 90, 120)
    DRAG_BORDER = (255, 255, 255)
    PROMO_BG = (40, 40, 52)

    def __init__(self, board):
        super().__init__(board)
        pygame.init()

        display_info = pygame.display.Info()
        screen_h = max(720, display_info.current_h)

        self.square_size = max(72, min(110, (screen_h - 120) // 8))
        self.board_size = self.square_size * 8
        self.panel_width = 320
        self.width = self.board_size + self.panel_width
        self.height = self.board_size

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Chess in Python")

        title_size = max(34, self.square_size // 2)
        menu_size = max(22, self.square_size // 4)
        info_size = max(18, self.square_size // 5)
        small_size = max(14, self.square_size // 7)

        self.title_font = pygame.font.SysFont("arial", title_size, bold=True)
        self.menu_font = pygame.font.SysFont("arial", menu_size, bold=True)
        self.info_font = pygame.font.SysFont("arial", info_size)
        self.small_font = pygame.font.SysFont("arial", small_size)

        center_x = self.width // 2
        button_w = min(340, self.width - 120)
        button_h = 60
        self.menu_buttons = {
            "one_player": pygame.Rect(
                center_x - button_w // 2, 220, button_w, button_h
            ),
            "two_player": pygame.Rect(
                center_x - button_w // 2, 310, button_w, button_h
            ),
            "chess960": pygame.Rect(
                center_x - button_w // 2, 400, button_w, button_h
            ),
            "sandbox": pygame.Rect(
                center_x - button_w // 2, 490, button_w, button_h
            ),
        }

        self.difficulty_buttons = {
            "Easy": pygame.Rect(center_x - button_w // 2, 220, button_w, 55),
            "Medium": pygame.Rect(center_x - button_w // 2, 305, button_w, 55),
            "Hard": pygame.Rect(center_x - button_w // 2, 390, button_w, 55),
            "Max": pygame.Rect(center_x - button_w // 2, 475, button_w, 55),
        }

        self.images = {}
        self._promotion_rects = {}
        self._sandbox_palette_rects = {}
        self.sandbox_toggle_rect = pygame.Rect(
            self.board_size + 20, self.height - 70, 280, 38
        )

        self.game_over_back_rect = pygame.Rect(0, 0, 0, 0)

        self._load_images()

    def _load_images(self):
        """
        Load and scale all piece sprite images from disk into the images dict.
        """
        sprite_map = {
            "wp": "sprites/wp.png",
            "wr": "sprites/wr.png",
            "wn": "sprites/wn.png",
            "wb": "sprites/wb.png",
            "wq": "sprites/wq.png",
            "wk": "sprites/wk.png",
            "bp": "sprites/bp.png",
            "br": "sprites/br.png",
            "bn": "sprites/bn.png",
            "bb": "sprites/bb.png",
            "bq": "sprites/bq.png",
            "bk": "sprites/bk.png",
        }

        for key, path in sprite_map.items():
            abs_path = resource_path(path)
            if os.path.exists(abs_path):
                img = pygame.image.load(abs_path).convert_alpha()
                self.images[key] = pygame.transform.smoothscale(
                    img, (self.square_size, self.square_size)
                )

    def get_piece_sprite_key(self, piece):
        """
        Return the sprite lookup key for a given piece.

        Args:
            piece: A ChessPiece instance, or None.

        Returns:
            A string sprite key (e.g. 'wq', 'bn') used to index into
            self.images, or None if piece is None.
        """
        if piece is None:
            return None

        mapping = {
            "Pawn": "p",
            "Rook": "r",
            "Knight": "n",
            "Bishop": "b",
            "Queen": "q",
            "King": "k",
        }
        return piece.color + mapping[piece.__class__.__name__]

    def draw_menu(self):
        """
        Render the main menu screen with mode selection buttons.
        """
        self.screen.fill(self.MENU_BG)

        title = self.title_font.render("Chess in Python", True, self.TEXT)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 120)))

        subtitle = self.small_font.render(
            "Choose a mode to start the game", True, self.TEXT
        )
        self.screen.blit(
            subtitle, subtitle.get_rect(center=(self.width // 2, 170))
        )

        label_map = {
            "one_player": "1 Player",
            "two_player": "2 Player",
            "chess960": "Chess960",
            "sandbox": "Sandbox",
        }

        mouse = pygame.mouse.get_pos()
        for key, rect in self.menu_buttons.items():
            color = (
                self.BUTTON_HOVER if rect.collidepoint(mouse) else self.BUTTON
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=12)
            text = self.menu_font.render(label_map[key], True, self.TEXT)
            self.screen.blit(text, text.get_rect(center=rect.center))

        pygame.display.flip()

    def draw_difficulty_menu(self):
        """
        Render the difficulty selection screen for single-player mode.
        """
        self.screen.fill(self.MENU_BG)

        title = self.title_font.render("Stockfish Difficulty", True, self.TEXT)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 120)))

        subtitle = self.small_font.render(
            "Pick how strong you want the engine to be", True, self.TEXT
        )
        self.screen.blit(
            subtitle, subtitle.get_rect(center=(self.width // 2, 170))
        )

        mouse = pygame.mouse.get_pos()
        for label, rect in self.difficulty_buttons.items():
            color = (
                self.BUTTON_HOVER if rect.collidepoint(mouse) else self.BUTTON
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=12)
            text = self.menu_font.render(label, True, self.TEXT)
            self.screen.blit(text, text.get_rect(center=rect.center))

        pygame.display.flip()

    def get_menu_choice(self, mouse_pos):
        """
        Return the mode key corresponding to the clicked main menu button.

        Args:
            mouse_pos: A tuple of two ints representing the (x, y) mouse
            position.

        Returns:
            A string mode key (e.g. 'one_player', 'sandbox'), or None if no
            button was clicked.
        """
        for key, rect in self.menu_buttons.items():
            if rect.collidepoint(mouse_pos):
                return key
        return None

    def get_difficulty_choice(self, mouse_pos):
        """
        Return the difficulty label corresponding to the clicked difficulty
        button.

        Args:
            mouse_pos: A tuple of two ints representing the (x, y) mouse
            position.

        Returns:
            A string difficulty label (e.g. 'Easy', 'Hard'), or None if no
            button was clicked.
        """
        for label, rect in self.difficulty_buttons.items():
            if rect.collidepoint(mouse_pos):
                return label
        return None

    def draw_legal_square(self, x, y):
        """
        Draw a highlighted indicator on a square to mark it as a legal move
        destination.

        Args:
            x: An int representing the pixel x-coordinate of the square's
            top-left corner.
            y: An int representing the pixel y-coordinate of the square's
            top-left corner.
        """
        inset = max(10, self.square_size // 8)
        rect = pygame.Rect(
            x + inset,
            y + inset,
            self.square_size - 2 * inset,
            self.square_size - 2 * inset,
        )
        pygame.draw.rect(self.screen, self.LEGAL_FILL, rect, border_radius=10)
        pygame.draw.rect(
            self.screen, self.LEGAL_BORDER, rect, 3, border_radius=10
        )

    def draw_board(self):
        """
        Render all 64 squares of the chessboard. Applies selection and legal
        move highlights.
        """
        for row in range(8):
            for col in range(8):
                x = col * self.square_size
                y = (7 - row) * self.square_size

                color = self.LIGHT if ((7 - row) + col) % 2 == 0 else self.DARK

                if self.board.selected == (col, row):
                    color = self.SELECTED

                pygame.draw.rect(
                    self.screen,
                    color,
                    (x, y, self.square_size, self.square_size),
                )

                if (col, row) in self.board.legal_moves:
                    self.draw_legal_square(x, y)

                # Highlight the en passant target square when a pawn is selected
                # and the target is one of its legal moves
                if (
                    self.board.en_passant_target == (col, row)
                    and (col, row) in self.board.legal_moves
                ):
                    self.draw_legal_square(x, y)

    def draw_pieces(self):
        """
        Render all pieces currently on the board, skipping any piece that is
        actively being dragged.
        """
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(col, row)
                if piece is None:
                    continue

                if (
                    self.board.dragging
                    and self.board.drag_source == "board"
                    and self.board.drag_from == (col, row)
                ):
                    continue

                x = col * self.square_size
                y = (7 - row) * self.square_size

                key = self.get_piece_sprite_key(piece)
                if key in self.images:
                    self.screen.blit(self.images[key], (x, y))

    def draw_dragged_piece(self):
        """
        Render the piece currently being dragged, centered on the mouse cursor.
        """
        if not self.board.dragging:
            return

        piece = self.board.drag_piece
        if piece is None or self.board.drag_mouse_pos is None:
            return

        key = self.get_piece_sprite_key(piece)
        if key not in self.images:
            return

        mx, my = self.board.drag_mouse_pos
        img = self.images[key]
        rect = img.get_rect(center=(mx, my))

        self.screen.blit(img, rect.topleft)
        pygame.draw.rect(
            self.screen, self.DRAG_BORDER, rect, 2, border_radius=8
        )

    def draw_promotion_box(self):
        """
        Render the pawn promotion selection panel in the side panel when a
        promotion is pending, or clear stored rects when it is not.
        """
        if self.board.promotion_pending is None:
            self._promotion_rects = {}
            return

        _, _, color = self.board.promotion_pending

        panel_x = self.board_size + 20
        panel_y = self.height - 245
        panel_w = self.panel_width - 40
        panel_h = 220

        pygame.draw.rect(
            self.screen,
            self.PROMO_BG,
            (panel_x, panel_y, panel_w, panel_h),
            border_radius=12,
        )

        title = self.small_font.render("Promote pawn", True, self.TEXT)
        self.screen.blit(title, (panel_x + 20, panel_y + 12))

        options = ["Queen", "Rook", "Bishop", "Knight"]
        sprite_keys = {
            "Queen": color + "q",
            "Rook": color + "r",
            "Bishop": color + "b",
            "Knight": color + "n",
        }

        self._promotion_rects = {}
        for i, option in enumerate(options):
            rect = pygame.Rect(
                panel_x + 15, panel_y + 42 + i * 42, panel_w - 30, 34
            )
            pygame.draw.rect(self.screen, self.BUTTON, rect, border_radius=8)

            key = sprite_keys[option]
            if key in self.images:
                icon = pygame.transform.smoothscale(self.images[key], (28, 28))
                self.screen.blit(icon, (rect.x + 4, rect.y + 3))

            label = self.small_font.render(option, True, self.TEXT)
            self.screen.blit(label, (rect.x + 42, rect.y + 7))
            self._promotion_rects[option] = rect

    def get_promotion_choice(self, mouse_pos):
        """
        Return the piece name selected in the promotion panel.

        Args:
            mouse_pos: A tuple of two ints representing the (x, y) mouse
            position.

        Returns:
            A string piece name (e.g. 'Queen', 'Knight'), or None if no
            promotion option was clicked.
        """
        for option, rect in self._promotion_rects.items():
            if rect.collidepoint(mouse_pos):
                return option
        return None

    def draw_sandbox_palette(self):
        """
        Render the sandbox tool palette in the side panel, including piece
        selection icons, the side-to-move toggle, and state hints.
        """
        panel_x = self.board_size + 20
        start_y = 250

        title = self.info_font.render("Sandbox Tools", True, self.TEXT)
        self.screen.blit(title, (panel_x, start_y))

        self._sandbox_palette_rects = {}
        items = [
            ("Pawn", "w"),
            ("Knight", "w"),
            ("Bishop", "w"),
            ("Rook", "w"),
            ("Queen", "w"),
            ("King", "w"),
            ("Pawn", "b"),
            ("Knight", "b"),
            ("Bishop", "b"),
            ("Rook", "b"),
            ("Queen", "b"),
            ("King", "b"),
        ]

        box_size = 44
        gap = 10
        y0 = start_y + 45
        for i, (piece_name, color) in enumerate(items):
            row = i // 2
            col = i % 2
            rect = pygame.Rect(
                panel_x + col * (box_size + 120),
                y0 + row * (box_size + gap),
                box_size,
                box_size,
            )
            pygame.draw.rect(self.screen, self.BUTTON, rect, border_radius=8)

            temp_key = (
                color
                + {
                    "Pawn": "p",
                    "Knight": "n",
                    "Bishop": "b",
                    "Rook": "r",
                    "Queen": "q",
                    "King": "k",
                }[piece_name]
            )
            if temp_key in self.images:
                icon = pygame.transform.smoothscale(
                    self.images[temp_key], (box_size, box_size)
                )
                self.screen.blit(icon, rect.topleft)

            label = self.small_font.render(
                f"{'White' if color == 'w' else 'Black'} {piece_name}",
                True,
                self.TEXT,
            )
            self.screen.blit(label, (rect.right + 8, rect.y + 10))
            self._sandbox_palette_rects[(piece_name, color)] = rect

        pygame.draw.rect(
            self.screen, self.BUTTON, self.sandbox_toggle_rect, border_radius=8
        )
        text = self.small_font.render(
            "Side to move: "
            f"{'White' if self.board.sandbox_side_to_move == 'w' else 'Black'}",
            True,
            self.TEXT,
        )
        self.screen.blit(
            text, text.get_rect(center=self.sandbox_toggle_rect.center)
        )

        hint = self.small_font.render(
            "Right click board square to delete piece", True, self.TEXT
        )
        self.screen.blit(hint, (panel_x, self.sandbox_toggle_rect.y - 35))

        state_text = self.small_font.render(
            self.board.get_sandbox_state_label(), True, self.TEXT
        )
        self.screen.blit(state_text, (panel_x, self.sandbox_toggle_rect.y - 65))

    def get_sandbox_palette_choice(self, mouse_pos):
        """
        Return the piece name and color corresponding to the clicked sandbox
        palette icon.

        Args:
            mouse_pos: A tuple of two ints representing the (x, y) mouse
            position.

        Returns:
            A tuple of (piece_name, color) strings (e.g. ('Queen', 'w')), or
            None if no palette icon was clicked.
        """
        for key, rect in self._sandbox_palette_rects.items():
            if rect.collidepoint(mouse_pos):
                return key
        return None

    def draw_panel(self):
        """
        Render the side panel, including turn indicator, game mode, move
        history and any mode-specific UI such as the sandbox palette or
        promotion box.
        """
        pygame.draw.rect(
            self.screen,
            self.PANEL_BG,
            (self.board_size, 0, self.panel_width, self.height),
        )

        title = self.menu_font.render("Chess", True, self.TEXT)
        self.screen.blit(title, (self.board_size + 90, 16))

        turn_text = self.info_font.render(
            f"Turn: {'White' if self.board.turn == 'w' else 'Black'}",
            True,
            self.TEXT,
        )
        self.screen.blit(turn_text, (self.board_size + 20, 70))

        mode_text = self.info_font.render(
            f"Mode: {self.board.mode}", True, self.TEXT
        )
        self.screen.blit(mode_text, (self.board_size + 20, 108))

        if self.board.mode == "one_player":
            diff_text = self.info_font.render(
                f"AI: {self.board.stockfish_label}", True, self.TEXT
            )
            self.screen.blit(diff_text, (self.board_size + 20, 146))

            status_text = self.small_font.render(
                self.board.engine_status, True, self.TEXT
            )
            self.screen.blit(status_text, (self.board_size + 20, 184))

            moves_title_y = 230
        elif self.board.mode == "sandbox":
            self.draw_sandbox_palette()
            self.draw_promotion_box()
            return
        else:
            moves_title_y = 170

        moves_title = self.info_font.render("Moves", True, self.TEXT)
        self.screen.blit(moves_title, (self.board_size + 20, moves_title_y))

        header_y = moves_title_y + 36
        num_x = self.board_size + 20
        white_x = self.board_size + 55
        black_x = self.board_size + 165

        self.screen.blit(
            self.small_font.render("#", True, self.TEXT), (num_x, header_y)
        )
        self.screen.blit(
            self.small_font.render("White", True, self.TEXT),
            (white_x, header_y),
        )
        self.screen.blit(
            self.small_font.render("Black", True, self.TEXT),
            (black_x, header_y),
        )

        pygame.draw.line(
            self.screen,
            self.TEXT,
            (self.board_size + 20, header_y + 22),
            (self.width - 20, header_y + 22),
            1,
        )

        row_height = 26
        start_y = header_y + 30
        moves = self.board.move_history

        paired_moves = []
        for i in range(0, len(moves), 2):
            white_move = moves[i]
            black_move = moves[i + 1] if i + 1 < len(moves) else ""
            paired_moves.append((i // 2 + 1, white_move, black_move))

        max_rows = min(14, max(1, (self.height - start_y - 240) // row_height))
        paired_moves = paired_moves[-max_rows:]

        for row_index, (idx, white_move, black_move) in enumerate(paired_moves):
            y = start_y + row_index * row_height
            self.screen.blit(
                self.small_font.render(str(idx), True, self.TEXT), (num_x, y)
            )
            self.screen.blit(
                self.small_font.render(white_move, True, self.TEXT),
                (white_x, y),
            )
            self.screen.blit(
                self.small_font.render(black_move, True, self.TEXT),
                (black_x, y),
            )

        self.draw_promotion_box()

    def display(self):
        """
        Render the complete game screen: board, pieces, dragged piece, and
        panel.
        """
        self.screen.fill((0, 0, 0))
        self.draw_board()
        self.draw_pieces()
        self.draw_dragged_piece()
        self.draw_panel()
        pygame.display.flip()

    def pixel_to_board(self, pos):
        """
        Convert a pixel position on screen to board coordinates.

        Args:
            pos: A tuple of two ints representing the (x, y) pixel position.

        Returns:
            A tuple of two ints (col, row) representing the board coordinates,
            or None if the position is outside the board area.
        """
        x, y = pos
        if x < self.board_size and y < self.board_size:
            col = x // self.square_size
            row = 7 - (y // self.square_size)
            return col, row
        return None

    def draw_game_over(self):
        """
        Render the game over screen displaying the result and a back-to-menu
        button.
        """
        self.screen.fill(self.MENU_BG)

        result = self.board.game_result
        if result == "checkmate_w":
            line1 = "Checkmate!"
            line2 = "White wins"
        elif result == "checkmate_b":
            line1 = "Checkmate!"
            line2 = "Black wins"
        else:
            line1 = "Stalemate!"
            line2 = "It's a draw"

        title = self.title_font.render(line1, True, self.TEXT)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 180)))

        sub = self.menu_font.render(line2, True, self.TEXT)
        self.screen.blit(sub, sub.get_rect(center=(self.width // 2, 260)))

        button_w = min(340, self.width - 120)
        self.game_over_back_rect = pygame.Rect(
            self.width // 2 - button_w // 2, 360, button_w, 60
        )
        mouse = pygame.mouse.get_pos()
        color = (
            self.BUTTON_HOVER
            if self.game_over_back_rect.collidepoint(mouse)
            else self.BUTTON
        )
        pygame.draw.rect(
            self.screen, color, self.game_over_back_rect, border_radius=12
        )

        btn_text = self.menu_font.render("Back to Menu", True, self.TEXT)
        self.screen.blit(
            btn_text, btn_text.get_rect(center=self.game_over_back_rect.center)
        )

        pygame.display.flip()
