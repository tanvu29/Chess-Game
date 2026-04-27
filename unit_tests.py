"""
Unit tests for the chess game.
"""

import unittest
from chess_piece import Pawn, Knight, Bishop, Rook, Queen, King
from chess_model import ChessModel


# Helpers
 
def empty_board():
    """
    Return a ChessModel with an empty board and standard defaults.
    """
    m = ChessModel()
    m._mode = "two_player"

    # Place kings far apart so they don't interfere with tests
    # Kings need to be on the board, or else the is_in_check
    # function complains about not having Kings on the board
    m.set_piece(0, 0, King("w"))
    m.set_piece(7, 7, King("b"))
    return m
 
 
def place(model, col, row, piece):
    """
    Place a piece on the model board.
    """
    model.set_piece(col, row, piece)


def clear_kings(model):
    """
    Remove any kings from the board.
    """
    for col in range(8):
        for row in range(8):
            piece = model.get_piece(col, row)
            if isinstance(piece, King):
                model.set_piece(col, row, None)

# -------------------
# Piece move geometry
# -------------------

class TestPawnMoves(unittest.TestCase):
 
    def test_white_pawn_single_step(self):
        m = empty_board()
        place(m, 4, 4, Pawn("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertIn((4, 5), moves)
 
    def test_white_pawn_double_step_from_start(self):
        m = empty_board()
        place(m, 4, 1, Pawn("w"))
        moves = m.get_piece(4, 1).valid_moves(4, 1, m)
        self.assertIn((4, 3), moves)
 
    def test_white_pawn_no_double_step_after_moving(self):
        m = empty_board()
        p = Pawn("w")
        p.has_moved = True
        place(m, 4, 3, p)
        moves = p.valid_moves(4, 3, m)
        self.assertNotIn((4, 5), moves)
 
    def test_white_pawn_blocked_by_own_piece(self):
        m = empty_board()
        place(m, 4, 4, Pawn("w"))
        place(m, 4, 5, Pawn("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertNotIn((4, 5), moves)
        self.assertNotIn((4, 6), moves)
 
    def test_white_pawn_diagonal_capture(self):
        m = empty_board()
        place(m, 4, 4, Pawn("w"))
        place(m, 3, 5, Pawn("b"))
        place(m, 5, 5, Pawn("b"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertIn((3, 5), moves)
        self.assertIn((5, 5), moves)
 
    def test_white_pawn_cannot_capture_own_piece(self):
        m = empty_board()
        place(m, 4, 4, Pawn("w"))
        place(m, 3, 5, Pawn("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertNotIn((3, 5), moves)
 
    def test_black_pawn_single_step(self):
        m = empty_board()
        place(m, 4, 4, Pawn("b"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertIn((4, 3), moves)
 
    def test_black_pawn_double_step_from_start(self):
        m = empty_board()
        place(m, 4, 6, Pawn("b"))
        moves = m.get_piece(4, 6).valid_moves(4, 6, m)
        self.assertIn((4, 4), moves)
 
    def test_pawn_cannot_move_off_board(self):
        m = empty_board()
        place(m, 0, 7, Pawn("w"))
        moves = m.get_piece(0, 7).valid_moves(0, 7, m)
        # Off the top of the board — no forward move
        self.assertNotIn((0, 8), moves)


class TestKnightMoves(unittest.TestCase):
 
    def test_knight_in_center_has_eight_moves(self):
        m = empty_board()
        place(m, 4, 4, Knight("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertEqual(len(moves), 8)
 
    def test_knight_in_corner_has_two_moves(self):
        m = empty_board()
        place(m, 0, 0, Knight("w"))
        moves = m.get_piece(0, 0).valid_moves(0, 0, m)
        self.assertEqual(len(moves), 2)
 
    def test_knight_cannot_land_on_own_piece(self):
        m = empty_board()
        place(m, 4, 4, Knight("w"))
        place(m, 6, 5, Pawn("w"))   # one of the 8 target squares
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertNotIn((6, 5), moves)
 
    def test_knight_can_capture_enemy(self):
        m = empty_board()
        place(m, 4, 4, Knight("w"))
        place(m, 6, 5, Pawn("b"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertIn((6, 5), moves)
 
    def test_knight_jumps_over_pieces(self):
        m = empty_board()
        place(m, 4, 4, Knight("w"))
        # Fill all adjacent squares
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc != 0 or dr != 0:
                    place(m, 4 + dc, 4 + dr, Pawn("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        # Knight should still have moves — it jumps
        self.assertEqual(len(moves), 8)
 
 
class TestBishopMoves(unittest.TestCase):
 
    def test_bishop_open_board(self):
        m = empty_board()
        place(m, 4, 4, Bishop("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        # 4 diagonals, 4+3+4+3 = 13 squares from e5,
        # minus one for the initialized kings in the corners
        self.assertEqual(len(moves), 12)
 
    def test_bishop_blocked_by_own_piece(self):
        m = empty_board()
        place(m, 4, 4, Bishop("w"))
        place(m, 6, 6, Pawn("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertNotIn((6, 6), moves)
        self.assertNotIn((7, 7), moves)
 
    def test_bishop_captures_enemy_and_stops(self):
        m = empty_board()
        place(m, 4, 4, Bishop("w"))
        place(m, 6, 6, Pawn("b"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertIn((6, 6), moves)
        self.assertNotIn((7, 7), moves)
 
    def test_bishop_stays_on_diagonal_colour(self):
        m = empty_board()
        place(m, 0, 0, Bishop("w"))
        moves = m.get_piece(0, 0).valid_moves(0, 0, m)
        for col, row in moves:
            self.assertEqual((col + row) % 2, 0)
 
 
class TestRookMoves(unittest.TestCase):
 
    def test_rook_open_board(self):
        m = empty_board()
        place(m, 4, 4, Rook("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertEqual(len(moves), 14)
 
    def test_rook_blocked_by_own_piece(self):
        m = empty_board()
        place(m, 4, 4, Rook("w"))
        place(m, 4, 6, Pawn("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertNotIn((4, 6), moves)
        self.assertNotIn((4, 7), moves)
 
    def test_rook_captures_and_stops(self):
        m = empty_board()
        place(m, 4, 4, Rook("w"))
        place(m, 4, 6, Pawn("b"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertIn((4, 6), moves)
        self.assertNotIn((4, 7), moves)
 
    def test_rook_moves_only_horizontally_vertically(self):
        m = empty_board()
        place(m, 4, 4, Rook("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        for col, row in moves:
            self.assertTrue(col == 4 or row == 4)
 
 
class TestQueenMoves(unittest.TestCase):
 
    def test_queen_combines_rook_and_bishop(self):
        m = empty_board()
        place(m, 4, 4, Queen("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        # 14 rook squares + 13 bishop squares
        # minus one for the initialized kings in the corner
        self.assertEqual(len(moves), 26)
 
    def test_queen_blocked_diagonally(self):
        m = empty_board()
        place(m, 0, 0, Queen("w"))
        place(m, 2, 2, Pawn("w"))
        moves = m.get_piece(0, 0).valid_moves(0, 0, m)
        self.assertNotIn((2, 2), moves)
        self.assertNotIn((3, 3), moves)
 
    def test_queen_captures_diagonally(self):
        m = empty_board()
        place(m, 0, 0, Queen("w"))
        place(m, 2, 2, Pawn("b"))
        moves = m.get_piece(0, 0).valid_moves(0, 0, m)
        self.assertIn((2, 2), moves)
        self.assertNotIn((3, 3), moves)
 
 
class TestKingMoves(unittest.TestCase):
 
    def test_king_in_center_has_eight_moves(self):
        m = empty_board()
        place(m, 4, 4, King("w"))
        # No castling possible (no rooks), no check
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        # valid_moves includes castling check; with no rooks, just 8 squares
        expected = {(3,3),(4,3),(5,3),(3,4),(5,4),(3,5),(4,5),(5,5)}
        self.assertEqual(set(moves), expected)
 
    def test_king_in_corner_has_three_moves(self):
        m = empty_board()
        place(m, 0, 0, King("w"))
        moves = m.get_piece(0, 0).valid_moves(0, 0, m)
        self.assertEqual(len(moves), 3)
 
    def test_king_cannot_take_own_piece(self):
        m = empty_board()
        place(m, 4, 4, King("w"))
        place(m, 4, 5, Pawn("w"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertNotIn((4, 5), moves)
 
    def test_king_can_capture_enemy(self):
        m = empty_board()
        place(m, 4, 4, King("w"))
        place(m, 4, 5, Pawn("b"))
        moves = m.get_piece(4, 4).valid_moves(4, 4, m)
        self.assertIn((4, 5), moves)


# ---------------
# Check detection
# ---------------
 
class TestCheckDetection(unittest.TestCase):
 
    def test_not_in_check_empty_board(self):
        m = empty_board()
        place(m, 4, 0, King("w"))
        self.assertFalse(m.is_in_check("w"))
 
    def test_rook_gives_check(self):
        m = empty_board()
        place(m, 4, 0, King("w"))
        place(m, 4, 7, Rook("b"))
        self.assertTrue(m.is_in_check("w"))
 
    def test_bishop_gives_check(self):
        m = empty_board()
        place(m, 4, 0, King("w"))
        place(m, 7, 3, Bishop("b"))
        self.assertTrue(m.is_in_check("w"))
 
    def test_queen_gives_check_horizontally(self):
        m = empty_board()
        place(m, 4, 0, King("w"))
        place(m, 0, 0, Queen("b"))
        self.assertTrue(m.is_in_check("w"))
 
    def test_queen_gives_check_diagonally(self):
        m = empty_board()
        place(m, 4, 0, King("w"))
        place(m, 7, 3, Queen("b"))
        self.assertTrue(m.is_in_check("w"))
 
    def test_knight_gives_check(self):
        m = empty_board()
        place(m, 4, 0, King("w"))
        place(m, 3, 2, Knight("b"))
        self.assertTrue(m.is_in_check("w"))
 
    def test_pawn_gives_check(self):
        m = empty_board()
        place(m, 4, 4, King("w"))
        place(m, 3, 5, Pawn("b"))
        self.assertTrue(m.is_in_check("w"))
 
    def test_pawn_behind_does_not_give_check(self):
        m = empty_board()
        place(m, 4, 4, King("w"))
        place(m, 3, 3, Pawn("b"))  # behind white king from black's perspective
        self.assertFalse(m.is_in_check("w"))
 
    def test_blocking_piece_removes_check(self):
        m = empty_board()
        place(m, 4, 0, King("w"))
        place(m, 4, 7, Rook("b"))
        place(m, 4, 4, Rook("w"))  # blocks the check
        self.assertFalse(m.is_in_check("w"))
 
    def test_is_in_check_raises_without_king(self):
        m = empty_board()
        clear_kings(m)

        with self.assertRaises(ValueError):
            m.is_in_check("w")
 
    def test_own_pieces_do_not_give_check(self):
        m = empty_board()
        place(m, 4, 0, King("w"))
        place(m, 4, 7, Rook("w"))
        self.assertFalse(m.is_in_check("w"))
 
    def test_king_attacks_king_gives_check(self):
        m = empty_board()
        place(m, 4, 4, King("w"))
        place(m, 4, 6, King("b"))
        place(m, 4, 5, King("b"))  # adjacent kings
        self.assertTrue(m.is_in_check("w"))
 
    def test_illegal_move_leaving_king_in_check_rejected(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 0, King("w"))
        place(m, 4, 1, Rook("w"))   # pinned rook
        place(m, 4, 7, Rook("b"))   # attacker along e-file
        # Moving the rook sideways exposes the king
        self.assertFalse(m.is_legal_move(4, 1, 5, 1))
 
    def test_legal_move_resolves_check(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 0, King("w"))
        place(m, 4, 7, Rook("b"))
        place(m, 4, 3, Rook("w"))   # can block on e4
        self.assertTrue(m.is_legal_move(4, 3, 4, 4))


# -----------------------
# Checkmate and stalemate
# -----------------------
 
class TestCheckmateAndStalemate(unittest.TestCase):
 
    def _fool_mate(self):
        """
        Set up the board after the Fool's Mate sequence (fastest checkmate):
        1. f3 e5  2. g4 Qh4#
        """
        m = ChessModel()
        m.setup_standard()
        m.move_piece(5, 1, 5, 2)   # f3
        m.move_piece(4, 6, 4, 4)   # e5
        m.move_piece(6, 1, 6, 3)   # g4
        m.move_piece(3, 7, 7, 3)   # Qh4#
        return m
 
    def test_fool_mate_is_checkmate(self):
        m = self._fool_mate()
        self.assertTrue(m.is_in_check("w"))
        self.assertFalse(m.has_legal_moves("w"))
 
    def test_fool_mate_game_end(self):
        m = self._fool_mate()
        self.assertTrue(m.check_game_end())
        self.assertEqual(m.game_result, "checkmate_b")
 
    def test_stalemate_detected(self):
        """
        Simplest stalemate: black king in corner, white queen one knight's
        move away, white king controlling escape squares.
        """
        m = empty_board()
        clear_kings(m)

        m._turn = "b"
        place(m, 0, 7, King("b"))
        place(m, 1, 5, Queen("w"))
        place(m, 2, 6, King("w"))
        self.assertFalse(m.is_in_check("b"))
        self.assertFalse(m.has_legal_moves("b"))
        self.assertTrue(m.check_game_end())
        self.assertEqual(m.game_result, "stalemate")
 
    def test_not_game_over_with_legal_moves(self):
        m = ChessModel()
        m.setup_standard()
        self.assertFalse(m.check_game_end())
        self.assertIsNone(m.game_result)



# --------
# Castling
# --------
 
class TestCastling(unittest.TestCase):
 
    def _castling_board(self, color):
        """Board with king and both rooks on their starting squares."""
        m = empty_board()
        back = 0 if color == "w" else 7
        place(m, 4, back, King(color))
        place(m, 0, back, Rook(color))
        place(m, 7, back, Rook(color))
        m._castling_rights[color]["kingside"] = True
        m._castling_rights[color]["queenside"] = True
        return m, back
 
    def test_white_kingside_castling_available(self):
        m, back = self._castling_board("w")
        moves = m.get_castling_moves(4, back, "w")
        self.assertIn((6, back), moves)
 
    def test_white_queenside_castling_available(self):
        m, back = self._castling_board("w")
        moves = m.get_castling_moves(4, back, "w")
        self.assertIn((2, back), moves)
 
    def test_black_kingside_castling_available(self):
        m, back = self._castling_board("b")
        moves = m.get_castling_moves(4, back, "b")
        self.assertIn((6, back), moves)
 
    def test_castling_blocked_by_piece_between(self):
        m, back = self._castling_board("w")
        place(m, 5, back, Knight("w"))  # blocks kingside
        moves = m.get_castling_moves(4, back, "w")
        self.assertNotIn((6, back), moves)
 
    def test_castling_right_revoked_after_king_moves(self):
        m, back = self._castling_board("w")
        m._turn = "w"
        m.move_piece(4, back, 4, 1)  # king moves up
        self.assertFalse(m._castling_rights["w"]["kingside"])
        self.assertFalse(m._castling_rights["w"]["queenside"])
 
    def test_castling_right_revoked_after_rook_moves(self):
        m, back = self._castling_board("w")
        m._turn = "w"
        m.move_piece(7, back, 7, 1)  # kingside rook moves
        self.assertFalse(m._castling_rights["w"]["kingside"])
        self.assertTrue(m._castling_rights["w"]["queenside"])
 
    def test_cannot_castle_while_in_check(self):
        m, back = self._castling_board("w")
        # Put a black rook on the e-file giving check
        place(m, 4, 7, Rook("b"))
        moves = m.get_castling_moves(4, back, "w")
        self.assertEqual(moves, [])
 
    def test_cannot_castle_through_attacked_square(self):
        m, back = self._castling_board("w")
        # Black rook attacks f1 (col 5), blocking kingside castling
        place(m, 5, 7, Rook("b"))
        moves = m.get_castling_moves(4, back, "w")
        self.assertNotIn((6, back), moves)
 
    def test_cannot_castle_into_check(self):
        m, back = self._castling_board("w")
        # Black rook attacks g1 (col 6), the king's landing square
        place(m, 6, 7, Rook("b"))
        moves = m.get_castling_moves(4, back, "w")
        self.assertNotIn((6, back), moves)
 
    def test_castling_moves_rook_correctly(self):
        m, back = self._castling_board("w")
        m._turn = "w"
        m.move_piece(4, back, 6, back)  # kingside castle
        self.assertIsInstance(m.get_piece(5, back), Rook)
        self.assertIsNone(m.get_piece(7, back))
 
    def test_queenside_castling_moves_rook_correctly(self):
        m, back = self._castling_board("w")
        m._turn = "w"
        m.move_piece(4, back, 2, back)  # queenside castle
        self.assertIsInstance(m.get_piece(3, back), Rook)
        self.assertIsNone(m.get_piece(0, back))
 
    def test_no_castling_if_rights_revoked(self):
        m, back = self._castling_board("w")
        m._castling_rights["w"]["kingside"] = False
        m._castling_rights["w"]["queenside"] = False
        moves = m.get_castling_moves(4, back, "w")
        self.assertEqual(moves, [])
 
 
# ----------
# En passant
# ----------
 
class TestEnPassant(unittest.TestCase):
 
    def test_en_passant_target_set_after_double_push(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 1, Pawn("w"))
        m.move_piece(4, 1, 4, 3)
        self.assertEqual(m._en_passant_target, (4, 2))
 
    def test_en_passant_target_cleared_after_other_move(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 1, Pawn("w"))
        place(m, 0, 6, Pawn("b"))
        m.move_piece(4, 1, 4, 3)   # sets EP target
        m.move_piece(0, 6, 0, 5)   # clears it
        self.assertIsNone(m._en_passant_target)
 
    def test_white_can_capture_en_passant(self):
        m = empty_board()
        m._turn = "b"
        place(m, 4, 4, Pawn("w"))
        place(m, 3, 6, Pawn("b"))
        m.move_piece(3, 6, 3, 4)   # black double-push sets EP target (3,5)
        pawn = m.get_piece(4, 4)
        moves = pawn.valid_moves(4, 4, m)
        self.assertIn((3, 5), moves)
 
    def test_en_passant_removes_captured_pawn(self):
        m = empty_board()
        m._turn = "b"
        place(m, 4, 4, Pawn("w"))
        place(m, 3, 6, Pawn("b"))
        m.move_piece(3, 6, 3, 4)   # sets EP target
        m._turn = "w"
        m.move_piece(4, 4, 3, 5)   # white captures en passant
        self.assertIsNone(m.get_piece(3, 4))   # captured pawn is gone
        self.assertIsInstance(m.get_piece(3, 5), Pawn)
 
    def test_en_passant_not_available_after_delay(self):
        """EP must be taken immediately; after another move the right expires."""
        m = empty_board()
        m._turn = "b"
        place(m, 4, 4, Pawn("w"))
        place(m, 3, 6, Pawn("b"))
        place(m, 7, 1, Pawn("w"))
        m.move_piece(3, 6, 3, 4)   # EP target set
        m._turn = "w"
        m.move_piece(7, 1, 7, 2)   # white plays a different move
        pawn = m.get_piece(4, 4)
        moves = pawn.valid_moves(4, 4, m)
        self.assertNotIn((3, 5), moves)
 
 
# --------------
# Pawn promotion
# --------------
 
class TestPromotion(unittest.TestCase):
 
    def test_promotion_triggered_at_rank_8(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 6, Pawn("w"))
        m.move_piece(4, 6, 4, 7)
        self.assertIsNotNone(m.promotion_pending)
        self.assertEqual(m.promotion_pending, (4, 7, "w"))
 
    def test_promotion_triggered_at_rank_1_for_black(self):
        m = empty_board()
        m._turn = "b"
        place(m, 4, 1, Pawn("b"))
        m.move_piece(4, 1, 4, 0)
        self.assertIsNotNone(m.promotion_pending)
        self.assertEqual(m.promotion_pending, (4, 0, "b"))
 
    def test_promote_to_queen(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 6, Pawn("w"))
        m.move_piece(4, 6, 4, 7)
        m.promote_pawn("Queen")
        self.assertIsInstance(m.get_piece(4, 7), Queen)
        self.assertIsNone(m.promotion_pending)
 
    def test_promote_to_knight(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 6, Pawn("w"))
        m.move_piece(4, 6, 4, 7)
        m.promote_pawn("Knight")
        self.assertIsInstance(m.get_piece(4, 7), Knight)
 
    def test_promote_to_rook(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 6, Pawn("w"))
        m.move_piece(4, 6, 4, 7)
        m.promote_pawn("Rook")
        self.assertIsInstance(m.get_piece(4, 7), Rook)
 
    def test_promote_to_bishop(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 6, Pawn("w"))
        m.move_piece(4, 6, 4, 7)
        m.promote_pawn("Bishop")
        self.assertIsInstance(m.get_piece(4, 7), Bishop)
 
    def test_promotion_suffix_appended_to_move_history(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 6, Pawn("w"))
        m.move_piece(4, 6, 4, 7)
        m.promote_pawn("Queen")
        self.assertTrue(m.move_history[-1].endswith("=Q"))
 
    def test_promote_pawn_returns_false_when_none_pending(self):
        m = empty_board()
        result = m.promote_pawn("Queen")
        self.assertFalse(result)
 
    def test_not_promoted_on_non_final_rank(self):
        m = empty_board()
        m._turn = "w"
        place(m, 4, 4, Pawn("w"))
        m.move_piece(4, 4, 4, 5)
        self.assertIsNone(m.promotion_pending)


if __name__ == "__main__":
    unittest.main(verbosity=2)