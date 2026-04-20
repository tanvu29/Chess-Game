"""
View class to display GUI of the game.

IMPORTANT FOR TEAM:
- UI drawing code goes here.
- Highlight colors, dragging visuals, and menu visuals go here.
- Do NOT put core chess rules here. Put those in ChessModel.py.
"""

import os
import pygame
from abc import ABC, abstractmethod


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
    SQUARE_SIZE = 140
    BOARD_SIZE = SQUARE_SIZE * 8
    WIDTH = BOARD_SIZE + 260
    HEIGHT = BOARD_SIZE

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

    def __init__(self, board):
        super().__init__(board)
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Chess in Python")

        self.title_font = pygame.font.SysFont("arial", 52, bold=True)
        self.menu_font = pygame.font.SysFont("arial", 32, bold=True)
        self.info_font = pygame.font.SysFont("arial", 28)
        self.small_font = pygame.font.SysFont("arial", 20)

        self.menu_buttons = {
            "one_player": pygame.Rect(self.WIDTH // 2 - 170, 260, 340, 70),
            "two_player": pygame.Rect(self.WIDTH // 2 - 170, 370, 340, 70),
            "chess960": pygame.Rect(self.WIDTH // 2 - 170, 480, 340, 70),
        }

        self.images = {}
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
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
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
        self.screen.blit(title, title.get_rect(center=(self.WIDTH // 2, 140)))

        subtitle = self.small_font.render(
            "Choose a mode to start the game",
            True,
            self.TEXT,
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.WIDTH // 2, 200)))

        label_map = {
            "one_player": "1 Player",
            "two_player": "2 Player",
            "chess960": "Chess960",
        }

        mouse = pygame.mouse.get_pos()
        for key, rect in self.menu_buttons.items():
            color = self.BUTTON_HOVER if rect.collidepoint(mouse) else self.BUTTON
            pygame.draw.rect(self.screen, color, rect, border_radius=12)

            text = self.menu_font.render(label_map[key], True, self.TEXT)
            self.screen.blit(text, text.get_rect(center=rect.center))

        pygame.display.flip()

    def get_menu_choice(self, mouse_pos):
        for key, rect in self.menu_buttons.items():
            if rect.collidepoint(mouse_pos):
                return key
        return None

    def draw_legal_square(self, x, y):
        inset = 20
        rect = pygame.Rect(
            x + inset,
            y + inset,
            self.SQUARE_SIZE - 2 * inset,
            self.SQUARE_SIZE - 2 * inset,
        )
        pygame.draw.rect(self.screen, self.LEGAL_FILL, rect, border_radius=10)
        pygame.draw.rect(self.screen, self.LEGAL_BORDER, rect, 4, border_radius=10)

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                x = col * self.SQUARE_SIZE
                y = (7 - row) * self.SQUARE_SIZE

                color = self.LIGHT if (row + col) % 2 == 0 else self.DARK

                if self.board.selected == (col, row):
                    color = self.SELECTED

                pygame.draw.rect(
                    self.screen,
                    color,
                    (x, y, self.SQUARE_SIZE, self.SQUARE_SIZE)
                )

                if (col, row) in self.board.legal_moves:
                    self.draw_legal_square(x, y)

    def draw_pieces(self):
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(col, row)
                if piece is None:
                    continue

                if self.board.dragging and self.board.drag_from == (col, row):
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
        pygame.draw.rect(self.screen, self.DRAG_BORDER, rect, 3, border_radius=8)

    def draw_panel(self):
        pygame.draw.rect(
            self.screen,
            self.PANEL_BG,
            (self.BOARD_SIZE, 0, 260, self.HEIGHT)
        )

        title = self.menu_font.render("Chess", True, self.TEXT)
        self.screen.blit(title, (self.BOARD_SIZE + 75, 20))

        turn_text = self.info_font.render(
            f"Turn: {'White' if self.board.turn == 'w' else 'Black'}",
            True,
            self.TEXT,
        )

        self.screen.blit(turn_text, (self.BOARD_SIZE + 20, 80))

        mode_text = self.info_font.render(
            f"Mode: {self.board.mode}",
            True,
            self.TEXT,
        )

        self.screen.blit(mode_text, (self.BOARD_SIZE + 20, 120))

        moves_title = self.info_font.render("Moves", True, self.TEXT)
        self.screen.blit(moves_title, (self.BOARD_SIZE + 20, 180))

        # Table header
        header_y = 220
        num_x = self.BOARD_SIZE + 20
        white_x = self.BOARD_SIZE + 65
        black_x = self.BOARD_SIZE + 150

        header_num = self.small_font.render("#", True, self.TEXT)
        header_white = self.small_font.render("White", True, self.TEXT)
        header_black = self.small_font.render("Black", True, self.TEXT)

        self.screen.blit(header_num, (num_x, header_y))
        self.screen.blit(header_white, (white_x, header_y))
        self.screen.blit(header_black, (black_x, header_y))

        pygame.draw.line(
            self.screen,
            self.TEXT,
            (self.BOARD_SIZE + 20, header_y + 24),
            (self.BOARD_SIZE + 235, header_y + 24),
            1
        )

        # Show latest moves
        row_height = 28
        start_y = header_y + 34
        moves = self.board.move_history

        paired_moves = []
        for i in range(0, len(moves), 2):
            white_move = moves[i]
            black_move = moves[i + 1] if i + 1 < len(moves) else ""
            paired_moves.append((i // 2 + 1, white_move, black_move))

        # Keep only the last rows that fit
        max_rows = (self.HEIGHT - start_y - 20) // row_height
        paired_moves = paired_moves[-max_rows:]

        for idx, white_move, black_move in paired_moves:
            y = start_y + (paired_moves.index((idx, white_move, black_move)) * row_height)

            num_surface = self.small_font.render(str(idx), True, self.TEXT)
            white_surface = self.small_font.render(white_move, True, self.TEXT)
            black_surface = self.small_font.render(black_move, True, self.TEXT)

            self.screen.blit(num_surface, (num_x, y))
            self.screen.blit(white_surface, (white_x, y))
            self.screen.blit(black_surface, (black_x, y))

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