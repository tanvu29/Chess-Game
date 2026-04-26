"""
View class to display GUI of the game.
"""

import os
import sys
from abc import ABC, abstractmethod
import pygame


def resource_path(relative_path):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class ChessView(ABC):
    def __init__(self, board):
        self._board = board

    @property
    def board(self):
        return self._board

    @abstractmethod
    def display(self):
        pass


class PygameChessView(ChessView):
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

        self.SQUARE_SIZE = max(72, min(110, (screen_h - 120) // 8))
        self.BOARD_SIZE = self.SQUARE_SIZE * 8
        self.PANEL_WIDTH = 320
        self.WIDTH = self.BOARD_SIZE + self.PANEL_WIDTH
        self.HEIGHT = self.BOARD_SIZE

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Chess in Python")

        title_size = max(34, self.SQUARE_SIZE // 2)
        menu_size = max(22, self.SQUARE_SIZE // 4)
        info_size = max(18, self.SQUARE_SIZE // 5)
        small_size = max(14, self.SQUARE_SIZE // 7)

        self.title_font = pygame.font.SysFont("arial", title_size, bold=True)
        self.menu_font = pygame.font.SysFont("arial", menu_size, bold=True)
        self.info_font = pygame.font.SysFont("arial", info_size)
        self.small_font = pygame.font.SysFont("arial", small_size)

        center_x = self.WIDTH // 2
        button_w = min(340, self.WIDTH - 120)
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
            self.BOARD_SIZE + 20, self.HEIGHT - 70, 280, 38
        )

        self.game_over_back_rect = pygame.Rect(0, 0, 0, 0)

        self._load_images()

    def _load_images(self):
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
                    img, (self.SQUARE_SIZE, self.SQUARE_SIZE)
                )

    def get_piece_sprite_key(self, piece):
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
        self.screen.fill(self.MENU_BG)

        title = self.title_font.render("Chess in Python", True, self.TEXT)
        self.screen.blit(title, title.get_rect(center=(self.WIDTH // 2, 120)))

        subtitle = self.small_font.render(
            "Choose a mode to start the game", True, self.TEXT
        )
        self.screen.blit(
            subtitle, subtitle.get_rect(center=(self.WIDTH // 2, 170))
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
        self.screen.fill(self.MENU_BG)

        title = self.title_font.render("Stockfish Difficulty", True, self.TEXT)
        self.screen.blit(title, title.get_rect(center=(self.WIDTH // 2, 120)))

        subtitle = self.small_font.render(
            "Pick how strong you want the engine to be", True, self.TEXT
        )
        self.screen.blit(
            subtitle, subtitle.get_rect(center=(self.WIDTH // 2, 170))
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
        for key, rect in self.menu_buttons.items():
            if rect.collidepoint(mouse_pos):
                return key
        return None

    def get_difficulty_choice(self, mouse_pos):
        for label, rect in self.difficulty_buttons.items():
            if rect.collidepoint(mouse_pos):
                return label
        return None

    def draw_legal_square(self, x, y):
        inset = max(10, self.SQUARE_SIZE // 8)
        rect = pygame.Rect(
            x + inset,
            y + inset,
            self.SQUARE_SIZE - 2 * inset,
            self.SQUARE_SIZE - 2 * inset,
        )
        pygame.draw.rect(self.screen, self.LEGAL_FILL, rect, border_radius=10)
        pygame.draw.rect(
            self.screen, self.LEGAL_BORDER, rect, 3, border_radius=10
        )

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                x = col * self.SQUARE_SIZE
                y = (7 - row) * self.SQUARE_SIZE

                color = self.LIGHT if ((7 - row) + col) % 2 == 0 else self.DARK

                if self.board.selected == (col, row):
                    color = self.SELECTED

                pygame.draw.rect(
                    self.screen,
                    color,
                    (x, y, self.SQUARE_SIZE, self.SQUARE_SIZE),
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

                x = col * self.SQUARE_SIZE
                y = (7 - row) * self.SQUARE_SIZE

                key = self.get_piece_sprite_key(piece)
                if key in self.images:
                    self.screen.blit(self.images[key], (x, y))

    def draw_dragged_piece(self):
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
        if self.board.promotion_pending is None:
            self._promotion_rects = {}
            return

        _, _, color = self.board.promotion_pending

        panel_x = self.BOARD_SIZE + 20
        panel_y = self.HEIGHT - 245
        panel_w = self.PANEL_WIDTH - 40
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

    def get_promotion_choice(self, mouse_pos, color):
        for option, rect in self._promotion_rects.items():
            if rect.collidepoint(mouse_pos):
                return option
        return None

    def draw_sandbox_palette(self):
        panel_x = self.BOARD_SIZE + 20
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
        for key, rect in self._sandbox_palette_rects.items():
            if rect.collidepoint(mouse_pos):
                return key
        return None

    def draw_panel(self):
        pygame.draw.rect(
            self.screen,
            self.PANEL_BG,
            (self.BOARD_SIZE, 0, self.PANEL_WIDTH, self.HEIGHT),
        )

        title = self.menu_font.render("Chess", True, self.TEXT)
        self.screen.blit(title, (self.BOARD_SIZE + 90, 16))

        turn_text = self.info_font.render(
            f"Turn: {'White' if self.board.turn == 'w' else 'Black'}",
            True,
            self.TEXT,
        )
        self.screen.blit(turn_text, (self.BOARD_SIZE + 20, 70))

        mode_text = self.info_font.render(
            f"Mode: {self.board.mode}", True, self.TEXT
        )
        self.screen.blit(mode_text, (self.BOARD_SIZE + 20, 108))

        if self.board.mode == "one_player":
            diff_text = self.info_font.render(
                f"AI: {self.board.stockfish_label}", True, self.TEXT
            )
            self.screen.blit(diff_text, (self.BOARD_SIZE + 20, 146))

            status_text = self.small_font.render(
                self.board.engine_status, True, self.TEXT
            )
            self.screen.blit(status_text, (self.BOARD_SIZE + 20, 184))

            moves_title_y = 230
        elif self.board.mode == "sandbox":
            self.draw_sandbox_palette()
            self.draw_promotion_box()
            return
        else:
            moves_title_y = 170

        moves_title = self.info_font.render("Moves", True, self.TEXT)
        self.screen.blit(moves_title, (self.BOARD_SIZE + 20, moves_title_y))

        header_y = moves_title_y + 36
        num_x = self.BOARD_SIZE + 20
        white_x = self.BOARD_SIZE + 55
        black_x = self.BOARD_SIZE + 165

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
            (self.BOARD_SIZE + 20, header_y + 22),
            (self.WIDTH - 20, header_y + 22),
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

        max_rows = min(14, max(1, (self.HEIGHT - start_y - 240) // row_height))
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
        self.screen.fill((0, 0, 0))
        self.draw_board()
        self.draw_pieces()
        self.draw_dragged_piece()
        self.draw_panel()
        pygame.display.flip()

    def pixel_to_board(self, pos):
        x, y = pos
        if x < self.BOARD_SIZE and y < self.BOARD_SIZE:
            col = x // self.SQUARE_SIZE
            row = 7 - (y // self.SQUARE_SIZE)
            return col, row
        return None

    def draw_game_over(self):
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
        self.screen.blit(title, title.get_rect(center=(self.WIDTH // 2, 180)))

        sub = self.menu_font.render(line2, True, self.TEXT)
        self.screen.blit(sub, sub.get_rect(center=(self.WIDTH // 2, 260)))

        button_w = min(340, self.WIDTH - 120)
        self.game_over_back_rect = pygame.Rect(
            self.WIDTH // 2 - button_w // 2, 360, button_w, 60
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
